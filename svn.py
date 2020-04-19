import bpy
import os
from bpy.types import (
    Operator,
    Panel,
    AddonPreferences,
    PropertyGroup
)
from bpy.props import (StringProperty)
import pysvn
import gazu
from . import kitsu

# if len(nagato.kitsu.current_project) != 0:
    # url = 
# else:
#     url = 'no'

########## operators ################################
client = pysvn.Client()

class OBJECT_OT_NagatoAdd(Operator):
    bl_label = 'Add file to SVN'
    bl_idname = 'nagato.add'
    bl_description = 'Add current file to project repository'
    
    @classmethod
    def poll(cls, context):
        return kitsu.current_user[0] != 'NOT LOGGED IN'


    def execute(self, context):  
        try:
            status = client.status(f'{bpy.context.blend_data.filepath}')[0]
            if str(status.text_status) == 'unversioned':
                print(status.text_status) 
                r = str(status)[13:-1].replace('\\\\', '/')
                print(r[1:-1])
                client.add(r[1:-1])
                self.report({'INFO'}, "File Added to Repository")
            else:
                self.report({'WARNING'}, "All files under version control")
        except pysvn._pysvn_3_7.ClientError:
            self.report({'WARNING'}, "Not a working copy")
        return{'FINISHED'}
        

class OBJECT_OT_NagatoPublish(Operator):
    bl_label = 'Publish file'
    bl_idname = 'nagato.publish'
    bl_description = 'Publish current file to project repository'
    
    comment: StringProperty(
        name = 'comment',
        default = 'file published',
        description = 'comment for publishing'
        )
        
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    @classmethod
    def poll(cls, context):
        return kitsu.current_user[0] != 'NOT LOGGED IN'


    def execute(self, context):
        bpy.ops.wm.save_mainfile()
        user = kitsu.current_user[0]
        
        try:
            client.checkin([f'{bpy.context.blend_data.filepath}'], f'{user} : {self.comment}')
            statuses = client.status(bpy.path.abspath('//') + 'maps')
            print(client.status(f'{bpy.context.blend_data.filepath}'))
            for status in statuses:
                if str(status.text_status) == 'modified':
                    print(status.text_status) 
                    r = str(status)[13:-1].replace('\\\\', '/')
                    print(r[1:-1])
                    client.checkin([r[1:-1]], self.comment)
            self.report({'INFO'}, "Publish successful")
        except pysvn._pysvn_3_7.ClientError as e:
            self.report({'WARNING'}, str(e))
        return{'FINISHED'}

    
class OBJECT_OT_NagatoUpdate(Operator):
    bl_label = 'Update file'
    bl_idname = 'nagato.update'
    bl_description = 'Update current file from project repository'
    
    @classmethod
    def poll(cls, context):
        return kitsu.current_user[0] != 'NOT LOGGED IN'


    def execute(self, context):
        try:
            client.update(f'{bpy.context.blend_data.filepath}')
            client.update(bpy.path.abspath('//') + 'maps')
            bpy.ops.wm.revert_mainfile()
            self.report({'INFO'}, "Update Successful")
        except pysvn._pysvn_3_7.ClientError:
            self.report({'WARNING'}, "None of the targets are working copies")
        return{'FINISHED'}


class OBJECT_OT_NagatoCheckOut(Operator):
    bl_label = 'Check Out'
    bl_idname = 'nagato.check_out'
    bl_description = 'checkout project files'
    

    username: StringProperty(
        name = 'Username',
        default = 'username',
        description = 'input svn username'
        )

    password: StringProperty(
        subtype = 'PASSWORD',
        name = 'Password',
        default = 'password',
        description = 'input your svn password'
        )

    # repo_url: StringProperty(
    #     name = 'repository url',
    #     default = kitsu.url[0],
    #     # if len(nagato.kitsu.current_project) != 0 else '',
    #     description = 'repository location'
    #     )
    
    # directory: StringProperty(
    #     name = 'directory',
    #     default = file_path,
    #     description = 'checkout directory'
    #     )
        
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    @classmethod
    def poll(cls, context):
        return kitsu.current_user[0] != 'NOT LOGGED IN' and len(kitsu.current_project) != 0


    def execute(self, context):
        # if len(kitsu.current_project) != 0:
        project_info = gazu.project.get_project_by_name(kitsu.current_project[0])
        repo_url = project_info['data']['repository_url']
        user = os.environ.get('homepath')
        user_f = user.replace("\\","/")
        mount_point = 'C:' + user_f + '/projects/'
        file_path = mount_point + kitsu.current_project[0]
        print(file_path)  
        client.set_default_username(self.username)
        client.set_default_password(self.password)
        if os.path.isdir(mount_point) == False:
            os.mkdir(mount_point)
        if os.path.isdir(file_path) == False:
            os.mkdir(file_path)
            try:
                client.checkout(repo_url, file_path)
                self.report({'INFO'}, "project files downloaded")
            except pysvn._pysvn_3_7.ClientError as e:
                self.report({'WARNING'}, str(e))
        elif len(os.listdir(file_path)) == 0:
            try:
                client.checkout(repo_url, file_path)
                self.report({'INFO'}, "project files downloaded")
            except pysvn._pysvn_3_7.ClientError as e:
                self.report({'WARNING'}, str(e))
        elif os.path.isdir(file_path + '/.svn') == True:
            bpy.ops.nagato.update()
            self.report({'INFO'}, "project file updated")
        else:
            self.report({'WARNING'}, "Directory is not empty and not under version control")
        return{'FINISHED'}


class OBJECT_OT_ConsolidateMaps(Operator):
    bl_label = 'Consolidate'
    bl_idname = 'nagato.consolidate'
    bl_description = 'consolidate all external images to maps folder'

    def invoke(self, context, event):
         return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        # bpy.ops.file.make_paths_relative()
        # bpy.ops.file.pack_all()
        # images = bpy.data.images

        # for image in images:
        #     if image.name != 'Viewer Node':
        #          if image.name != 'Render Result':
        #              image.packed_files[image.filepath].filepath = '//maps/' + image.name_full
        # bpy.ops.file.unpack_all(method='USE_ORIGINAL')
        try:
            bpy.ops.file.make_paths_relative()
            bpy.ops.file.pack_all()
            images = bpy.data.images

            for image in images:
                if image.name != 'Viewer Node':
                    if image.name != 'Render Result':
                        image.packed_files[image.filepath].filepath = '//maps/' + image.name_full
            bpy.ops.file.unpack_all(method='USE_ORIGINAL')
            
            #add consolidated files to svn
            statuses = client.status(bpy.path.abspath('//') + 'maps')
            for status in statuses:
                if str(status.text_status) == 'unversioned':
                    print(status.text_status) 
                    r = str(status)[13:-1].replace('\\\\', '/')
                    print(r[1:-1])
                    client.add(r[1:-1])
            self.report({'INFO'}, "Maps Colsolidated")
        except KeyError as e:
            self.report({'WARNING'}, str(e))
        except RuntimeError as r:
            self.report({'WARNING'}, str(r))
        except pysvn._pysvn_3_7.ClientError:
            bpy.ops.file.make_paths_relative()
            bpy.ops.file.pack_all()
            images = bpy.data.images

            for image in images:
                if image.name != 'Viewer Node':
                    if image.name != 'Render Result':
                        image.packed_files[image.filepath].filepath = '//maps/' + image.name_full
            bpy.ops.file.unpack_all(method='USE_ORIGINAL')
        return{'FINISHED'}

classes = [
    OBJECT_OT_NagatoAdd,
    OBJECT_OT_NagatoPublish,
    OBJECT_OT_NagatoUpdate,
    OBJECT_OT_NagatoCheckOut,
    OBJECT_OT_ConsolidateMaps
]
        
        
###################### registration######################
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
