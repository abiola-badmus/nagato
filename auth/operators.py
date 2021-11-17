import bpy
import os
from .. import gazu
from .. import profile
from ..gazu.exception import NotAuthenticatedException, ParameterException, MethodNotAllowedException, RouteNotFoundException, ServerErrorException, AuthFailedException
from requests.exceptions import MissingSchema, InvalidSchema, ConnectionError
from bpy.types import (Operator,)
from bpy.props import (StringProperty,)

NagatoProfile = profile.NagatoProfile



class NAGATO_OT_SetHost(Operator):
    bl_label = 'Set Host'
    bl_idname = 'nagato.set_host'
    bl_description = 'sets host'   

    host: StringProperty(
        name = 'host',
        default = '',
        description = 'set kitsu host'
        )

    def execute(self, context):
        gazu.client.set_host(self.host)
        self.report({'INFO'}, 'host set to ' + self.host)
        return{'FINISHED'}

        
class NAGATO_OT_Login(Operator):
    bl_label = 'Kitsu Login'
    bl_idname = 'nagato.login'
    bl_description = 'login to kitsu'

    user_name: StringProperty(
        name = 'User Name',
        default = 'username',
        description = 'input your kitsu user name'
        )
    
    password: StringProperty(
        subtype = 'PASSWORD',
        name = 'Password',
        default = 'password',
        description = 'input your kitsu password'
        )
    
    @classmethod
    def poll(cls, context):
        return not bool(NagatoProfile.user)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    
    def execute(self, context):
        # scene = context.scene
        
        try:
            host = context.preferences.addons['nagato'].preferences.host_url
            bpy.ops.nagato.set_host(host=host)
            token = gazu.log_in(self.user_name, self.password)
            NagatoProfile.host = host
            NagatoProfile.login = token['login']
            NagatoProfile.user = token['user']
            NagatoProfile.access_token = token['access_token']
            NagatoProfile.refresh_token = token['refresh_token']
            NagatoProfile.ldap = token['ldap']
            NagatoProfile.save_json()
            svn_auth_folder = f'{os.getenv("APPDATA")}/Subversion/auth/svn.simple'
            if os.path.isdir(svn_auth_folder):
                filelist = [ auth_file for auth_file in os.listdir(svn_auth_folder) ]
                for auth_file in filelist:
                    file_path = os.path.join(svn_auth_folder, auth_file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
            bpy.ops.nagato.refresh()
            bpy.context.scene.update_tag()
            # update_list(scene)
            context.preferences.addons['nagato'].preferences.ok_message = 'Logged in'
            context.preferences.addons['nagato'].preferences.error_message = ''
            self.report({'INFO'}, f"logged in as {NagatoProfile.user['full_name']}")
        # except (AuthFailedException, NotAuthenticatedException, ServerErrorException, ParameterException):
        #     context.preferences.addons['nagato'].preferences.error_message = 'Username and/or password is incorrect'
        #     self.report({'WARNING'}, 'Username and/or password is incorrect')
        except AuthFailedException:
            context.preferences.addons['nagato'].preferences.error_message = 'Username and/or password is incorrect'
            self.report({'ERROR'}, 'Username and/or password is incorrect')
        except ConnectionError:
            context.preferences.addons['nagato'].preferences.error_message = f'Unable to reach {host}. verify if host is correct'
            self.report({'ERROR'}, f'Unable to reach {host}. verify if host is correct')
        except InvalidSchema:
            context.preferences.addons['nagato'].preferences.error_message = f'host ({host}) name is invalid. verify if host is correct'
            self.report({'ERROR'}, f'host ({host}) name is invalid. verify if host is correct')
        except MissingSchema as err:
            context.preferences.addons['nagato'].preferences.error_message = str(err)
            self.report({'WARNING'}, str(err))
        # except OSError:
        #     context.preferences.addons['nagato'].preferences.error_message = 'Cant connect to server. check connection or Host url'
        #     self.report({'WARNING'}, 'Cant connect to server. check connection or Host url')
        # except (MethodNotAllowedException, RouteNotFoundException):
        #     context.preferences.addons['nagato'].preferences.error_message = 'invalid host url'
        #     self.report({'WARNING'}, 'invalid host url')
        return{'FINISHED'}


class NAGATO_OT_Logout(Operator):
    bl_label = 'Log out'
    bl_idname = 'nagato.logout'
    bl_description = 'log out'  

    @classmethod
    def poll(cls, context):
        return NagatoProfile.user != None 
    
    def execute(self, context):
        try:
            gazu.log_out()
            NagatoProfile.reset()
            svn_auth_folder = f'{os.getenv("APPDATA")}/Subversion/auth/svn.simple'
            if os.path.isdir(svn_auth_folder):
                filelist = [ auth_file for auth_file in os.listdir(svn_auth_folder) ]
                for auth_file in filelist:
                    file_path = os.path.join(svn_auth_folder, auth_file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
            bpy.ops.nagato.refresh()
            self.report({'INFO'}, 'logged out')
            return{'FINISHED'}
        except NotAuthenticatedException:
            NagatoProfile.reset()
            svn_auth_folder = f'{os.getenv("APPDATA")}/Subversion/auth/svn.simple'
            if os.path.isdir(svn_auth_folder):
                filelist = [ auth_file for auth_file in os.listdir(svn_auth_folder) ]
                for auth_file in filelist:
                    file_path = os.path.join(svn_auth_folder, auth_file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
            bpy.ops.nagato.refresh()
            self.report({'INFO'}, 'logged out')
            return{'FINISHED'}

############### all classes ####################    
classes = [
        NAGATO_OT_SetHost,
        NAGATO_OT_Login,
        NAGATO_OT_Logout,
        ]  
    
    
# registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)   

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
            
