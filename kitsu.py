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

NagatoProfile = profile.NagatoProfile
time_queue = [0, 3]
current_user = ['NOT LOGGED IN']
remote_host = ['None']
todo = []
projects = []
filtered_todo = []
displayed_tasks = []
project_names = []
task_tpyes = []
status = ['wip', 'todo', 'wfa']
status_name = []

# use to store data of active categories selected
current_project = []
current_filter = []
current_status = []


########################### FUNCTIONS ################################ 
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
    print(self.tasks_idx)
    bpy.context.scene.tasks_idx = self.tasks_idx
    time_queue.pop(0)
    time_queue.append(time.time())
    if time_queue[1] - time_queue[0] <= 0.3:
        bpy.ops.nagato.open()
        print('yes')
    else:
        print('no')

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
            if len(current_filter) == 0:
                task_icon='BLENDER'
            elif current_filter[0].lower() in {'modeling'}:
                task_icon='CUBE'
            elif current_filter[0].lower() in {'shading', 'texturing'}:
                task_icon='SHADING_RENDERED'
            elif current_filter[0].lower() in {'lighting'}:
                task_icon='OUTLINER_DATA_LIGHT'
            elif current_filter[0].lower() in {'anim', 'animation'}:
                task_icon='ARMATURE_DATA'
            elif current_filter[0].lower() in {'fx'}:
                task_icon='SHADERFX'
            elif current_filter[0].lower() in {'rigging'}:
                task_icon='BONE_DATA'
            elif current_filter[0].lower() in {'layout'}:
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
        return  current_user[0] == 'NOT LOGGED IN'
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    
    def execute(self, context):
        # scene = context.scene
        
        try:
            current_user.clear()
            remote_host.clear()
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

                remote_host.append(False)
                current_user.append(f'{gazu.client.get_current_user()["full_name"]} - Local Host')
                current_user.append(f'{gazu.client.get_current_user()["role"]}')
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
                
                remote_host.append(True)
                current_user.append(f'{gazu.client.get_current_user()["full_name"]} - Remote Host')
                current_user.append(f'{gazu.client.get_current_user()["role"]}')
            displayed_tasks.clear()
            bpy.ops.nagato.refresh()
            bpy.context.scene.update_tag()
            # update_list(scene)
            self.report({'INFO'}, f"logged in as {current_user}")
        except (NotAuthenticatedException, ServerErrorException, ParameterException):
            self.report({'WARNING'}, 'wrong credecials')
            current_user.append('NOT LOGGED IN')
            remote_host.append('None')
        except (MissingSchema, InvalidSchema, ConnectionError) as err:
            self.report({'WARNING'}, str(err))
            current_user.append('NOT LOGGED IN')
            remote_host.append('None')
        except OSError:
            self.report({'WARNING'}, 'Cant connect to server. check connection or Host url')
            current_user.append('NOT LOGGED IN')
            remote_host.append('None')
        except (MethodNotAllowedException, RouteNotFoundException):
            self.report({'WARNING'}, 'invalid host url')
            current_user.append('NOT LOGGED IN')
            remote_host.append('None')
        except Exception as err:
            self.report({'WARNING'}, f'something went wrong. {err}')
            current_user.append('NOT LOGGED IN')
            remote_host.append('None')
        return{'FINISHED'}


class NAGATO_OT_Logout(Operator):
    bl_label = 'Log out'
    bl_idname = 'nagato.logout'
    bl_description = 'log out'  

    @classmethod
    def poll(cls, context):
        return  current_user[0] != 'NOT LOGGED IN'  
    
    def execute(self, context):
        gazu.log_out()
        NagatoProfile.reset()
        global current_user
        current_user = ['NOT LOGGED IN']
        bpy.ops.nagato.refresh()
        self.report({'INFO'}, 'logged out')
        return{'FINISHED'}


class NAGATO_OT_Refresh(Operator):
    bl_label = 'Sasori Refresh'
    bl_idname = 'nagato.refresh'
    bl_description = 'refresh kitsu data'    

    def execute(self, context):
        scene = context.scene
        print(current_project)
        print(len(current_project))
        todo.clear()
        task_tpyes.clear()
        project_names.clear()
        displayed_tasks.clear()
        current_filter.clear()
        current_project.clear()
        scene.tasks.clear()
        try:
            for ob in gazu.user.all_tasks_to_do():
                if ob not in todo:
                    todo.append(ob)
            for project in gazu.user.all_tasks_to_do():
               p = project['project_name']
               if p not in project_names:
                   project_names.append(p)
            self.report({'INFO'}, 'Refreshed')
        except:
            self.report({'INFO'}, 'Not Logged in')
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
        current_project.clear()
        current_filter.clear()
        displayed_tasks.clear()
        projects.clear()
        task_tpyes.clear()
        filtered_todo.clear()
        for file in todo:
            if file['project_name'] == self.project:
                projects.append(file)
        current_project.append(self.project)
        bpy.context.scene.update_tag()
        bpy.app.handlers.depsgraph_update_pre.append(update_list)
        for task in projects:
            i = task['task_type_name']
            if i not in task_tpyes:
                task_tpyes.append(i) 
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
        current_filter.clear()
        displayed_tasks.clear()
        filtered_todo.clear()
        for file in projects:
            if file['task_type_name'] == self.filter:
                if file['sequence_name'] == None:
                    displayed_tasks.append([file['entity_name'], file['task_status_short_name']])
                else:
                    displayed_tasks.append([file['sequence_name'] + '_' + file['entity_name'], file['task_status_short_name']])
                filtered_todo.append(file) 
        current_filter.append(self.filter)
        bpy.context.scene.update_tag()
        bpy.app.handlers.depsgraph_update_pre.append(update_list)
        self.report({'INFO'}, 'filtered by ' + self.filter)
        return{'FINISHED'}


class NAGATO_OT_OpenFile(Operator):
    bl_label = 'open'
    bl_idname = 'nagato.open'
    bl_description = 'opens active selected task'

    save_bool = bpy.props.BoolProperty()

    @classmethod
    def poll(cls, context):
        try:
            task_list_index = bpy.context.scene.tasks_idx
            filtered_todo[task_list_index]['id']
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
        mount_point = context.preferences.addons['nagato'].preferences.project_mount_point
        task_list_index = bpy.context.scene.tasks_idx
        active_id = filtered_todo[task_list_index]['id']
        file_path = mount_point.replace("\\","/")  + gazu.files.build_working_file_path(active_id)
        if filtered_todo[task_list_index]['task_type_name'].casefold() in {'lighting', 'rendering', 'compositing'}:
            directory = file_path + '_lighting.blend'
        elif filtered_todo[task_list_index]['task_type_name'].casefold() in {'layout', 'previz'}:
            directory = file_path + '_layout.blend'
        elif filtered_todo[task_list_index]['task_type_name'].casefold() in {'fx'}:
            directory = file_path + '_fx.blend'
        elif filtered_todo[task_list_index]['task_type_name'].casefold() in {'anim', 'animation'}:
            directory = file_path + '_anim.blend'
        else:
            directory = file_path + '.blend'
        try:
            if self.save_bool == True:
                bpy.ops.wm.save_mainfile()
            bpy.ops.wm.open_mainfile(filepath= directory, load_ui=False)
        except:
            self.report({'WARNING'}, 'file path incorrect, check file tree')
        bpy.context.scene.tasks_idx = task_list_index
        bpy.context.scene.update_tag()
        bpy.app.handlers.depsgraph_update_pre.append(update_list)
        return{'FINISHED'}
 

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
        task_list_index = bpy.context.scene.tasks_idx
        filtered_todo[task_list_index]['id']
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
        task_type = filtered_todo[task_list_index]['task_type_name']
        entity_name = filtered_todo[task_list_index]['entity_name']
        entity_sq_name = filtered_todo[task_list_index]['sequence_name']
        
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
            gazu.task.add_comment(filtered_todo[task_list_index]['id'], status_name[0], self.comment)
            if status_name[0]['short_name'] == 'wfa':
                bpy.ops.nagato.publish()
            displayed_tasks[task_list_index][1] = status_name[0]['short_name']
            for item in todo:
                if item['id'] == filtered_todo[task_list_index]['id']:
                    item['task_status_short_name'] = status_name[0]['short_name']
            for item in projects:
                if item['id'] == filtered_todo[task_list_index]['id']:
                    item['task_status_short_name'] = status_name[0]['short_name']  
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
        project = gazu.project.get_project_by_name(current_project[0])
        project_id = project['id']
        mount_point = context.preferences.addons['nagato'].preferences.project_mount_point
        project_root = os.path.join(mount_point, context.preferences.addons['nagato'].preferences.root)
        project_name = current_project[0]
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
        return current_user[0] != 'NOT LOGGED IN' and len(current_project) != 0 and current_user[1] == 'admin'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        root = context.preferences.addons['nagato'].preferences.root
        asset_path = context.preferences.addons['nagato'].preferences.asset_path
        shot_path = context.preferences.addons['nagato'].preferences.shot_path
        sequence_path = context.preferences.addons['nagato'].preferences.sequence_path
        scenes_path = context.preferences.addons['nagato'].preferences.scenes_path
        asset_name = context.preferences.addons['nagato'].preferences.asset_name
        shot_name = context.preferences.addons['nagato'].preferences.shot_name
        sequence_name = context.preferences.addons['nagato'].preferences.sequence_name
        scenes_name = context.preferences.addons['nagato'].preferences.scenes_name
        with open('file_tree.json', 'r') as data:
            file_tree = json.load(data)
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

        project = gazu.project.get_project_by_name(current_project[0])
        project_id = project['id']
        gazu.files.update_project_file_tree(project_id, file_tree)
        self.report({'INFO'}, 'file tree applied')
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
        for project in project_names:
            layout = self.layout
            layout.operator('nagato.projects', text= project).project= project


class NAGATO_MT_FilterTask(Menu):
    bl_label = 'select filter'
    bl_idname = "nagato.filter_tasks"
    
    def draw(self, context):
        for task in task_tpyes:
            layout = self.layout
            layout.operator('nagato.filter', text= task).filter= task
       
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
        NAGATO_OT_Projects,
        NAGATO_MT_Projects,
        NAGATO_OT_SetStatus,
        NAGATO_MT_StatusList,
        NAGATO_OT_UpdateStatus,
        NAGATO_OT_GetRefImg,
        OBJECT_OT_NagatoSetFileTree
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
            current_user.clear()
            current_user.append(f"{active_user_profile['user']['full_name']} - Local Host")
            current_user.append(f"{active_user_profile['user']['role']}")
        except NotAuthenticatedException:
            NagatoProfile.reset()
        except ConnectionError:
            NagatoProfile.reset()


    for cls in classes:
        bpy.utils.register_class(cls)   
    bpy.types.Scene.tasks = bpy.props.CollectionProperty(type=MyTasks)
    bpy.types.Scene.tasks_idx = bpy.props.IntProperty(default=0)

    bpy.app.handlers.depsgraph_update_pre.append(update_list)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)  
    del bpy.types.Scene.tasks
    del bpy.types.Scene.tasks_idx