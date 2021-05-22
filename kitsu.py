from gazu import project, shot
from typing import Sequence
import bpy
import os
import time
import json
import gazu
from . import profile
from gazu.exception import NotAuthenticatedException, ParameterException, MethodNotAllowedException, RouteNotFoundException, ServerErrorException
from requests.exceptions import MissingSchema, InvalidSchema, ConnectionError
from bpy.types import (Operator, PropertyGroup, CollectionProperty, Menu)
from bpy.props import (StringProperty, IntProperty, BoolProperty)
from bpy.app.handlers import persistent
from configparser import ConfigParser, NoOptionError
import shutil
import re

NagatoProfile = profile.NagatoProfile
# time_queue = [0, 3]

displayed_tasks = []
status = ['wip', 'todo', 'wfa']
status_name = []
current_status = []


########################### FUNCTIONS ################################ 
@persistent
def create_main_collection(dummy):
    if 'main' not in bpy.data.collections.keys():
        collection = bpy.data.collections.new('main')
        bpy.context.scene.collection.children.link(collection)
    if 'main' not in bpy.data.scenes.keys():
        bpy.data.scenes.new('main')

def update_list(scene):
    bpy.app.handlers.depsgraph_update_pre.remove(update_list)

    try:
        scene.tasks.clear()
    except:
        pass

    for i, (task, task_status) in enumerate(displayed_tasks, 0):   
        colection = scene.tasks.add()   
        colection.tasks = task
        colection.tasks_status = task_status 
        colection.tasks_idx = i

def double_click(self, context):
    bpy.context.scene.tasks_idx = self.tasks_idx
    time_queue.pop(0)
    time_queue.append(time.time())
    if time_queue[1] - time_queue[0] <= 0.3:
        bpy.ops.nagato.open()
        print('yes')
    else:
        print('no')

def write_config(file_directory, config_parser):
    '''
        write data from a configuration parser
        to file
    '''
    with open(file_directory, 'w') as f:
        config_parser.write(f)

def load_config(file_directory, config_parser):
    '''
        load data from a configuration file 
        into a configuration parser instance
    '''
    with open(file_directory, 'r') as f:
        data = f.read()
    config_parser.read_string(data)

def task_file_directory(blend_file_path, file_map_parser, task_type):
    try:
        task_type_map = file_map_parser.get('file_map', task_type).lower()
        if task_type_map == 'base':
            directory = f'{blend_file_path}.blend'
            return directory
        elif task_type_map == 'none':
            pass
        else:
             directory = f'{blend_file_path}_{task_type_map}.blend'
             return directory
    except NoOptionError:
        return None
        # directory = f'{blend_file_path}_{task_type}.blend'
        # file_map_parser.set('file_map', task_type, task_type)

############################ Property groups #####################################################
class MyTasks(PropertyGroup):
    tasks_idx: IntProperty()
    tasks: StringProperty()
    tasks_status: StringProperty()
    # click: BoolProperty(default=False, update=double_click)

#################### mapping lists into column #################################
class TASKS_UL_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            active_task_type = NagatoProfile.active_task_type
            if active_task_type == None:
                task_icon='BLENDER'
            elif active_task_type.lower() in {'modeling'}:
                task_icon='CUBE'
            elif active_task_type.lower() in {'shading', 'texturing'}:
                task_icon='SHADING_RENDERED'
            elif active_task_type.lower() in {'lighting'}:
                task_icon='OUTLINER_DATA_LIGHT'
            elif active_task_type.lower() in {'anim', 'animation'}:
                task_icon='ARMATURE_DATA'
            elif active_task_type.lower() in {'fx'}:
                task_icon='SHADERFX'
            elif active_task_type.lower() in {'rigging'}:
                task_icon='BONE_DATA'
            elif active_task_type.lower() in {'layout'}:
                task_icon='MOD_ARRAY'
            else:
                task_icon='BLENDER'

            split = layout.split(factor= 0.8, align=True)
            # split.prop(item, 'click',icon = task_icon, text=item.tasks, emboss=False, translate=False)
            split.label(text = item.tasks, icon = task_icon)
            split.label(text = item.tasks_status)
        elif self.layout_type in {'GRID'}:
            pass
############## Operators #######################################

class NAGATO_OT_SetLocalHost(Operator):
    bl_label = 'Set Host'
    bl_idname = 'nagato.set_local_host'
    bl_description = 'sets host'    
    
    def execute(self, context):
        host = context.preferences.addons['nagato'].preferences.local_host_url
        gazu.client.set_host(host)
        self.report({'INFO'}, 'host set to ' + host)
        return{'FINISHED'}


class NAGATO_OT_SetRemoteHost(Operator):
    bl_label = 'Set Host'
    bl_idname = 'nagato.set_remote_host'
    bl_description = 'sets host'    
    
    def execute(self, context):
        host = context.preferences.addons['nagato'].preferences.remote_host_url
        gazu.client.set_host(host)
        self.report({'INFO'}, 'host set to ' + host)
        return{'FINISHED'}

        
class NAGATO_OT_Login(Operator):
    bl_label = 'Kitsu Login'
    bl_idname = 'nagato.login'
    bl_description = 'login to kitsu'

    remote_bool = BoolProperty(
        name = 'Remote',
        default = False,
        description = 'is host url remote'
    )
    
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
            if self.remote_bool == False:
                host = context.preferences.addons['nagato'].preferences.local_host_url
                bpy.ops.nagato.set_local_host()
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
            else:
                host = context.preferences.addons['nagato'].preferences.remote_host_url
                bpy.ops.nagato.set_remote_host()
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

            displayed_tasks.clear()
            bpy.ops.nagato.refresh()
            bpy.context.scene.update_tag()
            # update_list(scene)
            context.preferences.addons['nagato'].preferences.ok_message = 'Logged in'
            context.preferences.addons['nagato'].preferences.error_message = ''
            self.report({'INFO'}, f"logged in as {NagatoProfile.user['full_name']}")
        except (NotAuthenticatedException, ServerErrorException, ParameterException):
            context.preferences.addons['nagato'].preferences.error_message = 'Username and/or password is incorrect'
            self.report({'WARNING'}, 'wrong credecials')
        except (MissingSchema, InvalidSchema, ConnectionError) as err:
            context.preferences.addons['nagato'].preferences.error_message = str(err)
            self.report({'WARNING'}, str(err))
        except OSError:
            context.preferences.addons['nagato'].preferences.error_message = 'Cant connect to server. check connection or Host url'
            self.report({'WARNING'}, 'Cant connect to server. check connection or Host url')
        except (MethodNotAllowedException, RouteNotFoundException):
            context.preferences.addons['nagato'].preferences.error_message = 'invalid host url'
            self.report({'WARNING'}, 'invalid host url')
        except Exception as err:
            context.preferences.addons['nagato'].preferences.error_message = f'something went wrong. {err}'
            self.report({'WARNING'}, f'something went wrong. {err}')
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
            return{'FINISHED'}
            

class NAGATO_OT_Refresh(Operator):
    bl_label = 'Nagato Refresh'
    bl_idname = 'nagato.refresh'
    bl_description = 'refresh kitsu data'    

    # @classmethod
    # def poll(cls, context):
    #     return NagatoProfile.user != None 

    def execute(self, context):
        scene = context.scene
        displayed_tasks.clear()
        scene.tasks.clear()
        try:
            NagatoProfile.refresh_tasks()
            self.report({'INFO'}, 'Refreshed')
        except NotAuthenticatedException:
            self.report({'INFO'}, 'Not Logged in') 
        context.preferences.addons['nagato'].preferences.reset_messages()
        bpy.context.scene.update_tag()
        bpy.app.handlers.depsgraph_update_pre.append(update_list)
        return{'FINISHED'}
       

class NAGATO_OT_Projects(Operator):
    bl_label = 'projects'
    bl_idname = 'nagato.projects'
    bl_description = 'select project'    
    
    project: StringProperty(default='')
    
    def execute(self, context):
        # scene = context.scene
        NagatoProfile.active_project = gazu.project.get_project_by_name(self.project)
        displayed_tasks.clear()
        bpy.context.scene.update_tag()
        bpy.app.handlers.depsgraph_update_pre.append(update_list) 
        bpy.ops.nagato.assets_refresh()
        self.report({'INFO'}, 'Project: ' + self.project)
        return{'FINISHED'}


class NAGATO_OT_Filter(Operator):
    bl_label = 'filter'
    bl_idname = 'nagato.filter'
    bl_description = 'filter task'    
    
    filter: StringProperty(default='')
    
    def execute(self, context):
        # scene = context.scene
        displayed_tasks.clear()
        for file in NagatoProfile.tasks[NagatoProfile.active_project['name']][self.filter]:
            NagatoProfile.active_task_type = self.filter
            if file['task_type_name'] == self.filter:
                if file['sequence_name'] == None:
                    displayed_tasks.append([file['entity_name'], file['task_status_short_name']])
                else:
                    displayed_tasks.append([file['sequence_name'] + '_' + file['entity_name'], file['task_status_short_name']])
        bpy.context.scene.update_tag()
        bpy.app.handlers.depsgraph_update_pre.append(update_list)
        self.report({'INFO'}, 'filtered by ' + self.filter)
        return{'FINISHED'}


class NAGATO_OT_OpenFile(Operator):
    bl_label = 'open task file'
    bl_idname = 'nagato.open'
    bl_description = 'opens active selected task file'

    save_bool = bpy.props.BoolProperty()

    @classmethod
    def poll(cls, context):
        try:
            task_list_index = bpy.context.scene.tasks_idx
            NagatoProfile.tasks[NagatoProfile.active_project['name']][NagatoProfile.active_task_type][task_list_index]['id']
            status = 1
        except:
            status = 0
        return status == 1
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        row = self.layout
        row.prop(self, "save_bool", text="SAVE FILE")
    
    def execute(self, context):
        file_map_parser = ConfigParser()
        task_list_index = bpy.context.scene.tasks_idx
        active_id = NagatoProfile.tasks[NagatoProfile.active_project['name']]\
            [NagatoProfile.active_task_type][task_list_index]['id']
        entity_id = NagatoProfile.tasks[NagatoProfile.active_project['name']]\
            [NagatoProfile.active_task_type][task_list_index]["entity_id"]
        file_path = os.path.expanduser(gazu.files.build_working_file_path(active_id))
        task_type = NagatoProfile.tasks[NagatoProfile.active_project['name']]\
            [NagatoProfile.active_task_type][task_list_index]['task_type_name']
        mount_point = NagatoProfile.active_project['file_tree']['working']['mountpoint']
        root = NagatoProfile.active_project['file_tree']['working']['root']
        project_folder = os.path.expanduser(os.path.join(mount_point, root, NagatoProfile.active_project['name'].replace(' ','_').lower()))
        file_map_dir = os.path.join(project_folder, '.conf/file_map')

        if not os.path.isdir(project_folder):
            self.report({'WARNING'}, 'Project not downloaded, download project file')
            return{'FINISHED'}
        if not os.path.isfile(file_map_dir):
            self.report({'WARNING'}, 'task file map does not exist in <project folder>/.conf/filemap')
            return{'FINISHED'}
        load_config(file_map_dir, file_map_parser)
        directory = task_file_directory(blend_file_path=file_path,
                                        file_map_parser=file_map_parser,
                                        task_type=task_type)
        task_file_data = {'task_type':task_type, 'task_id':active_id, 'entity_id':entity_id}
        if directory:
            try:
                if self.save_bool == True:
                    bpy.ops.wm.save_mainfile()
                bpy.ops.wm.open_mainfile(filepath= directory, load_ui=False)
                scene = bpy.data.scenes.get('main')
                scene['task_file_data'] = task_file_data
                bpy.ops.wm.save_mainfile()
            except RuntimeError as err:
                self.report({'WARNING'}, f'{err}')
        else:
             self.report({'WARNING'}, 'no file for task, check task file map')
        bpy.context.scene.tasks_idx = task_list_index
        bpy.context.scene.update_tag()
        bpy.app.handlers.depsgraph_update_pre.append(update_list)
        return{'FINISHED'}


class NAGATO_OT_project_open_in_browser(Operator):
    bl_idname = "nagato.project_open_in_browser"
    bl_label = "Open Project in Browser"
    bl_description = "Opens a webbrowser to show the project in Kitsu"

    project_id: bpy.props.StringProperty(name="Project ID", default="")

    @classmethod
    def poll(cls, context):
        return bool(NagatoProfile.user) and NagatoProfile.active_project != None

    def execute(self, context):
        import webbrowser
        url = gazu.project.get_project_url(NagatoProfile.active_project['id'])
        print(NagatoProfile.active_project)
        webbrowser.open_new_tab(url)
        self.report({"INFO"}, f"Opened a browser at {url}")

        return {"FINISHED"}


class NAGATO_OT_Submit_shot_to_kitsu(Operator):
    bl_idname = "nagato.submit_shots_to_kitsu"
    bl_label = "Submit all shots to kitsu"
    bl_description = "Submit all shots to kitsu"

    project_id: bpy.props.StringProperty(name="Project ID", default="")

    def execute(self, context):
        project = NagatoProfile.active_project
        selected_scrips = bpy.context.selected_sequences
        for i in selected_scrips:
            name = i.name
            sequence_pattern = re.compile(r'\bsq_[^\s]+')
            Sequence_match = sequence_pattern.search(name)
            shot_pattern = re.compile(r'\bsh_[^\s]+')
            shot_match = shot_pattern.search(name)

            if Sequence_match:
                sequence_name = Sequence_match.group(0)
            else:
                sequence_name = None
            if shot_match:
                shot_name = shot_match.group(0)
            else:
                shot_name = None
            if sequence_name and shot_name:
                sequence = gazu.shot.get_sequence_by_name(project['id'], sequence_name)
                if sequence:
                    shot = gazu.shot.get_shot_by_name(sequence, shot_name)
                    if not shot:
                        gazu.shot.new_shot(
                            project=project['id'],
                            sequence=sequence,
                            name=shot_name)
                else:
                    sequence = gazu.shot.new_sequence(project['id'], sequence_name)
                    gazu.shot.new_shot(
                        project=project['id'],
                        sequence=sequence,
                        name=shot_name)




        return {"FINISHED"}


class NAGATO_OT_SetStatus(Operator):
    bl_label = 'status'
    bl_idname = 'nagato.setstatus'
    bl_description = 'opens active selected task'

    stat: StringProperty(default='')
    
    def execute(self, context):
        current_status.clear()
        status_name.clear()
        gazu.task.get_task_status_by_short_name(self.stat)
        s = gazu.task.get_task_status_by_short_name(self.stat)
        status_name.append(s)
        # task_list_index = bpy.context.scene.tasks_idx
        # filtered_todo[task_list_index]['id']
        current_status.append(s['short_name'])
        self.report({'INFO'}, 'Status: ' + self.stat)
        return{'FINISHED'}


class NAGATO_OT_UpdateStatus(Operator):
    bl_label = 'update status'
    bl_idname = 'nagato.update_status'
    bl_description = 'update status'



    comment: StringProperty(
        name = 'comment',
        default = '',
        description = 'type your comment'
        )


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        task_list_index = bpy.context.scene.tasks_idx
        task_type = NagatoProfile.tasks[NagatoProfile.active_project['name']][NagatoProfile.active_task_type]\
            [task_list_index]["entity_name"] #filtered_todo[task_list_index]['task_type_name']
        entity_name = NagatoProfile.tasks[NagatoProfile.active_project['name']][NagatoProfile.active_task_type]\
            [task_list_index]["entity_name"] # filtered_todo[task_list_index]['entity_name']
        entity_sq_name = NagatoProfile.tasks[NagatoProfile.active_project['name']][NagatoProfile.active_task_type]\
            [task_list_index]["entity_name"]# filtered_todo[task_list_index]['sequence_name']
        
        # if entity_name['sequence_name'] == None:
        #     displayed_tasks.append(file['entity_name'])
        # else:
        #     displayed_tasks.append(file['sequence_name'] + '_' + file['entity_name'])
        #     filtered_todo.append(file)

        if task_type == 'lighting':
            if entity_sq_name == None:
                file_name = entity_name + '_lighting.blend'
            else:
                file_name = entity_sq_name + '_' + entity_name + '_lighting.blend'
        elif task_type == 'rendering':
            if entity_sq_name == None:
                file_name = entity_name + '_lighting.blend'
            else:
                file_name = entity_sq_name + '_' + entity_name + '_lighting.blend'
        elif task_type == 'previz':
            if entity_sq_name == None:
                file_name = entity_name + '_layout.blend'
            else:
                file_name = entity_sq_name + '_' + entity_name + '_layout.blend'
        elif task_type == 'layout':
            if entity_sq_name == None:
                file_name = entity_name + '_layout.blend'
            else:
                file_name = entity_sq_name + '_' + entity_name + '_layout.blend'
        elif task_type == 'anim':
            if entity_sq_name == None:
                file_name = entity_name + '_anim.blend'
            else:
                file_name = entity_sq_name + '_' + entity_name + '_anim.blend'
        else:
            file_name = entity_name + '.blend'

        row = self.layout
        row.label(text = 'FILE:  ' + file_name)
        # if len(status_name) == 0:
        #     row.label(text = 'STATUS:  NO STATUS SELECTED')
        # else:
        #     row.label(text = 'STATUS:  ' + status_name[0]['short_name'])
        
        if len(current_status) == 0:
            status_label = 'select status'
        else:
            status_label = current_status[0]
        row.menu("nagato.select_status", text= status_label)
        row.prop(self, "comment")

    def execute(self, context):
        # scene = context.scene
        try:
            task_list_index = bpy.context.scene.tasks_idx
            task = NagatoProfile.tasks[NagatoProfile.active_project['name']][NagatoProfile.active_task_type][task_list_index]
            gazu.task.add_comment(task['id'], status_name[0], self.comment)
            if status_name[0]['short_name'] == 'wfa':
                bpy.ops.nagato.publish()
            displayed_tasks[task_list_index][1] = status_name[0]['short_name']
            task['task_status_short_name'] = status_name[0]['short_name']
            bpy.context.scene.update_tag()
            bpy.app.handlers.depsgraph_update_pre.append(update_list)
            self.report({'INFO'}, "status updated")
        except IndexError:
            self.report({'WARNING'}, "No status selected.")
        return{'FINISHED'}


class NAGATO_OT_GetRefImg(Operator):
    bl_label = 'Get Reference images'
    bl_idname = 'nagato.get_ref'
    bl_description = 'get reference images'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        project = gazu.project.get_project_by_name(NagatoProfile.active_project['name'])
        project_id = project['id']
        mount_point = context.preferences.addons['nagato'].preferences.project_mount_point
        project_root = os.path.join(mount_point, context.preferences.addons['nagato'].preferences.root)
        project_name = NagatoProfile.active_project['name']
        file_name = os.path.splitext(os.path.basename(bpy.context.blend_data.filepath))[0] 
        refs_path = os.path.join(project_root, project_name, 'refs')
        dimension = gazu.asset.get_asset_by_name(project_id, file_name)['data']['dimension']
        height = float(dimension.split('x')[0])
        if 'refs' not in bpy.data.collections:
            bpy.data.collections.new('refs')
            collection = bpy.data.collections['refs']
        if 'refs' not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(collection)
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['refs']
        for image in os.listdir(refs_path):
            if file_name == '_'.join(image.split('_')[1:-1]):
                if image.split('_', 1)[0] in {'blueprint'}:
                    if os.path.splitext(image.rsplit('_', 1)[-1])[0] in {'right', 'left', 'front', 'back'}:
                        bpy.ops.object.load_background_image(filepath=os.path.join(refs_path, image))
                        bpy.ops.transform.rotate(value=1.5708, orient_axis='X')
                        bpy.context.object.empty_display_size = height
                        bpy.context.object.empty_image_offset[1] = 0
                        bpy.context.object.show_empty_image_perspective = False
                    if  os.path.splitext(image.rsplit('_', 1)[-1])[0] in {'right'}:
                        bpy.ops.transform.rotate(value=1.5708, orient_axis='Z')
                        bpy.context.object.name = 'right'
                        bpy.context.object.hide_select = True
                    elif os.path.splitext(image.rsplit('_', 1)[-1])[0] in {'left'}:
                        bpy.ops.transform.rotate(value=-1.5708, orient_axis='Z')
                        bpy.context.object.name = 'left'
                        bpy.context.object.hide_select = True
                    elif os.path.splitext(image.rsplit('_', 1)[-1])[0] in {'back'}:
                        bpy.ops.transform.rotate(value=3.14159, orient_axis='Z')
                        bpy.context.object.name = 'back'
                        bpy.context.object.hide_select = True
                    elif os.path.splitext(image.rsplit('_', 1)[-1])[0] in {'front'}:
                        bpy.context.object.name = 'front'
                        bpy.context.object.hide_select = True
            if file_name == os.path.splitext(image.split('_', 1)[-1])[0]:
                if image.split('_', 1)[0] in {'ref'}:
                    bpy.ops.object.load_reference_image(filepath=os.path.join(refs_path, image))
                    bpy.ops.transform.rotate(value=1.5708, orient_axis='X')
                    bpy.context.object.name = os.path.splitext(image)[0]
                    bpy.context.object.empty_display_size = height
        return{'FINISHED'}


class OBJECT_OT_NagatoSetFileTree(Operator):
    bl_label = 'set file tree?'
    bl_idname = 'nagato.set_file_tree'
    bl_description = 'set file tree'

    @classmethod
    def poll(cls, context):
        return bool(NagatoProfile.user) and bool(NagatoProfile.active_project) and NagatoProfile.user['role'] == 'admin'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        mountpoint = context.preferences.addons['nagato'].preferences.mountpoint
        root = context.preferences.addons['nagato'].preferences.root
        asset_path = context.preferences.addons['nagato'].preferences.asset_path
        shot_path = context.preferences.addons['nagato'].preferences.shot_path
        sequence_path = context.preferences.addons['nagato'].preferences.sequence_path
        scenes_path = context.preferences.addons['nagato'].preferences.scenes_path
        asset_name = context.preferences.addons['nagato'].preferences.asset_name
        shot_name = context.preferences.addons['nagato'].preferences.shot_name
        sequence_name = context.preferences.addons['nagato'].preferences.sequence_name
        scenes_name = context.preferences.addons['nagato'].preferences.scenes_name
        file_tree_dir = os.path.join(os.path.dirname(__file__), 'file_tree.json')
        with open(file_tree_dir, 'r') as data:
            file_tree = json.load(data)
        #MOUNT_POINT
        file_tree['working']['mountpoint'] = mountpoint
        #ROOT
        file_tree['working']['root'] = root
        #FOLDER PATHS
        file_tree['working']['folder_path']['shot'] = shot_path
        file_tree['working']['folder_path']['asset'] = asset_path
        file_tree['working']['folder_path']['sequence'] = sequence_path
        file_tree['working']['folder_path']['scene'] = scenes_path
        #FILE_NAMES
        file_tree['working']['file_name']['shot'] = shot_name
        file_tree['working']['file_name']['asset'] = asset_name
        file_tree['working']['file_name']['sequence'] = sequence_name
        file_tree['working']['file_name']['scene'] = scenes_name

        project = gazu.project.get_project_by_name(NagatoProfile.active_project['name'])
        project_id = project['id']
        gazu.files.update_project_file_tree(project_id, file_tree)
        self.report({'INFO'}, 'file tree applied')
        return{'FINISHED'}


class NAGATO_OT_GetDependencies(Operator):
    bl_label = 'set file tree?'
    bl_idname = 'nagato.get_dependencies'
    bl_description = 'set file tree'

    # @classmethod
    # def poll(cls, context):
    #     return bool(NagatoProfile.user) and bool(NagatoProfile.active_project) and NagatoProfile.user['role'] == 'admin'

    def execute(self, context):
        main_file_path = bpy.context.blend_data.filepath
        scene = bpy.data.scenes.get('main')
        entity = gazu.entity.get_entity(scene['task_file_data']['entity_id'])
        entity_type = entity['type']
        file_dependencies = entity['entities_out']
        for file_dependency in file_dependencies:
            asset = gazu.asset.get_asset(file_dependency)
            asset_name = asset['name']
            path = f"{gazu.files.build_working_file_path(asset['tasks'][0]['id'])}.blend"
            expanded_path = os.path.expanduser(path)
            if not bpy.data.objects.get(asset_name):
                if not main_file_path == expanded_path:
                    file_name = 'main'
                    directory = f'{expanded_path}/Collection'
                    bpy.ops.wm.link(
                        filename=file_name,
                        directory=directory)
                    bpy.context.selected_objects[0].name = asset_name
                    if 'file_dependecies' not in scene.keys():
                        scene['file_dependecies'] = dict()
                    scene['file_dependecies'][asset_name] = path    
        self.report({'INFO'}, 'dependency updated')
        return{'FINISHED'}

class NAGATO_OT_Setting(Operator):
    bl_label = 'setting'
    bl_idname = 'nagato.setting'
    bl_description = 'go to nagato setting'

    # @classmethod
    # def poll(cls, context):
    #     return bool(NagatoProfile.user) and bool(NagatoProfile.active_project) and NagatoProfile.user['role'] == 'admin'

    def execute(self, context):
        bpy.ops.preferences.addon_show(module = 'nagato')
        return{'FINISHED'}

######################################### Menu ################################################################################
class NAGATO_MT_StatusList(Menu):
    bl_label = 'select_status'
    bl_idname = "nagato.select_status"
    
    def draw(self, context):
        for s in status:
            layout = self.layout
            layout.operator('nagato.setstatus', text= s).stat= s


class NAGATO_MT_Projects(Menu):
    bl_label = 'select project'
    bl_idname = "nagato.select_project"
    
    def draw(self, context):
        for project in NagatoProfile.tasks:
            layout = self.layout
            layout.operator('nagato.projects', text= project).project= project


class NAGATO_MT_FilterTask(Menu):
    bl_label = 'select filter'
    bl_idname = "nagato.filter_tasks"
    
    def draw(self, context):
        
        for task_type in NagatoProfile.tasks[NagatoProfile.active_project['name']]:
            layout = self.layout
            layout.operator('nagato.filter', text= task_type).filter = task_type
       
############### all classes ####################    
classes = [
        #NagatoSetHost,
        NAGATO_OT_SetLocalHost,
        NAGATO_OT_SetRemoteHost,
        NAGATO_OT_Login,
        NAGATO_OT_Logout,
        NAGATO_OT_Refresh,
        MyTasks,
        TASKS_UL_list,
        NAGATO_MT_FilterTask,
        NAGATO_OT_Filter,
        NAGATO_OT_OpenFile,
        NAGATO_OT_Submit_shot_to_kitsu,
        NAGATO_OT_project_open_in_browser,
        NAGATO_OT_Projects,
        NAGATO_MT_Projects,
        NAGATO_OT_SetStatus,
        NAGATO_MT_StatusList,
        NAGATO_OT_GetDependencies,
        NAGATO_OT_UpdateStatus,
        NAGATO_OT_GetRefImg,
        OBJECT_OT_NagatoSetFileTree,
        NAGATO_OT_Setting,
        ]  
    
    
# registration
def register():
    profile.register()
    active_user_profile = NagatoProfile.read_json()
    if active_user_profile['login'] == True:
        try:
            gazu.client.set_tokens(active_user_profile)
            gazu.client.set_host(active_user_profile['host'])
            gazu.client.get_current_user()

            NagatoProfile.host = active_user_profile['host']
            NagatoProfile.login = active_user_profile['login']
            NagatoProfile.user = active_user_profile['user']
            NagatoProfile.access_token = active_user_profile['access_token']
            NagatoProfile.refresh_token = active_user_profile['refresh_token']
            NagatoProfile.ldap = active_user_profile['ldap']
        except NotAuthenticatedException:
            NagatoProfile.reset()
        except ConnectionError:
            NagatoProfile.reset()


    for cls in classes:
        bpy.utils.register_class(cls)   
    bpy.types.Scene.tasks = bpy.props.CollectionProperty(type=MyTasks)
    bpy.types.Scene.tasks_idx = bpy.props.IntProperty(default=0)

    bpy.app.handlers.depsgraph_update_pre.append(update_list)
    bpy.app.handlers.load_post.append(create_main_collection)
    # bpy.app.handlers.load_factory_preferences_post.append(load_handler)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)  
    del bpy.types.Scene.tasks
    del bpy.types.Scene.tasks_idx