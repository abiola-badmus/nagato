import bpy
import os
import gazu
from bpy.types import (Operator, PropertyGroup, CollectionProperty, Menu)
from bpy.props import (StringProperty, IntProperty)
current_user = ['NOT LOGGED IN']
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
def fliter_projects(project):
    current_project.clear()
    current_filter.clear()
    displayed_tasks.clear()
    projects.clear()
    task_tpyes.clear()
    filtered_todo.clear()
    for file in todo:
        if file['project_name'] == project:
            projects.append(file)
    current_project.append(project)
    bpy.context.scene.update_tag()
    bpy.app.handlers.depsgraph_update_pre.append(update_list)


def fliter_task(filter):
    current_filter.clear()
    displayed_tasks.clear()
    filtered_todo.clear()
    for file in projects:
        if file['task_type_name'] == filter:
            if file['sequence_name'] == None:
                displayed_tasks.append([file['entity_name'], file['task_status_short_name']])
            else:
                displayed_tasks.append([file['sequence_name'] + '_' + file['entity_name'], file['task_status_short_name']])
            filtered_todo.append(file) 
    current_filter.append(filter)
    bpy.context.scene.update_tag()
    bpy.app.handlers.depsgraph_update_pre.append(update_list)  

    
def update_list(scene):
    bpy.app.handlers.depsgraph_update_pre.remove(update_list)

    try:
        scene.col.clear()
    except:
        pass

    for i, (tasks, tasks_stat) in enumerate(displayed_tasks, 1):   
        colection = scene.col.add()   
        colection.tasks = tasks
        colection.tasks_stat = tasks_stat  


############################## Addon preference to set host ####################################
class NagatoSetHost(bpy.types.AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = 'nagato'

    host_url: StringProperty(
        name="Url of server",
        default='',
    )

    def draw(self, context):
        layout = self.layout
        # layout.label(text="Nagato Preferences")
        layout.prop(self, "host_url")
        # layout.operator('nagato.set_host')


############################ Property groups #####################################################
class MyTasks(PropertyGroup):
     tasks : StringProperty()
     tasks_stat: StringProperty()
     

#################### mapping lists into column #################################
class TASKS_UL_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor= 0.6, align=True)   
            split.label(text = item.tasks, icon='BLENDER')
            split.label(text = item.tasks_stat)
        elif self.layout_type in {'GRID'}:
            pass
############## Operators #######################################

class NAGATO_OT_SetHost(Operator):
    bl_label = 'Set Host'
    bl_idname = 'nagato.set_host'
    bl_description = 'sets host'    
    
    def execute(self, context):
        host = context.preferences.addons['nagato'].preferences.host_url
        gazu.client.set_host(host)
        self.report({'INFO'}, 'host set to ' + host)
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
        return  current_user[0] == 'NOT LOGGED IN'
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    
    def execute(self, context):
        # gazu.log_in(self.user_name, self.password)
        # name = gazu.user.client.get_current_user()['full_name']
        # displayed_tasks.clear()
        # bpy.ops.nagato.refresh()
        # bpy.context.scene.update_tag()
        # bpy.app.handlers.depsgraph_update_pre.append(update_list)
        # self.report({'INFO'}, f"logged in as {name}")
        try:
            current_user.clear()
            bpy.ops.nagato.set_host()
            gazu.log_in(self.user_name, self.password)
            current_user.append(gazu.user.client.get_current_user()["full_name"])
            displayed_tasks.clear()
            bpy.ops.nagato.refresh()
            bpy.context.scene.update_tag()
            bpy.app.handlers.depsgraph_update_pre.append(update_list)
            self.report({'INFO'}, f"logged in as {current_user}")
        except gazu.exception.AuthFailedException:
            self.report({'WARNING'}, 'wrong credecials')
            current_user.append('NOT LOGGED IN')
        except gazu.exception.ParameterException:
            self.report({'WARNING'}, 'wrong credecials')
            current_user.append('NOT LOGGED IN')
        except OSError:
            self.report({'WARNING'}, 'Cant connect to server. check connection or Host url')
            current_user.append('NOT LOGGED IN')
        except gazu.exception.MethodNotAllowedException:
            self.report({'WARNING'}, 'invalid host url')
            current_user.append('NOT LOGGED IN')
        except Exception:
            self.report({'WARNING'}, 'something went wrong')
            current_user.append('NOT LOGGED IN')
        return{'FINISHED'}


class NAGATO_OT_Refresh(Operator):
    bl_label = 'Sasori Refresh'
    bl_idname = 'nagato.refresh'
    bl_description = 'refresh kitsu data'    

    def execute(self, context):
        todo.clear()
        task_tpyes.clear()
        project_names.clear()
        displayed_tasks.clear()
        current_filter.clear()
        current_project.clear()
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
        #gazu.files.set_project_file_tree('bd7c84a9-3457-4d72-89f2-9a3546345b98', 'eaxum')
        fliter_projects(self.project)
        for task in projects:
            i = task['task_type_name']
            if i not in task_tpyes:
                task_tpyes.append(i) 
        self.report({'INFO'}, 'Project: ' + self.project)
        return{'FINISHED'}


class NAGATO_OT_Filter(Operator):
    bl_label = 'filter'
    bl_idname = 'nagato.filter'
    bl_description = 'filter task'    
    
    task: StringProperty(default='')
    
    def execute(self, context):
        fliter_task(self.task)
        self.report({'INFO'}, 'filtered by ' + self.task)
        return{'FINISHED'}


class NAGATO_OT_OpenFile(Operator):
    bl_label = 'open'
    bl_idname = 'nagato.open'
    bl_description = 'opens active selected task'

    save_bool = bpy.props.BoolProperty()

    @classmethod
    def poll(cls, context):
        try:
            task_list_index = bpy.context.scene.col_idx
            filtered_todo[task_list_index]['id']
            status = 1
        except:
            status = 0
        return status == 1
    
    # def invoke(self, context, event):
    #     return context.window_manager.invoke_confirm(self, event)
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        row = self.layout
        row.prop(self, "save_bool", text="SAVE FILE")
    
    def execute(self, context):
        task_list_index = bpy.context.scene.col_idx
        active_id = filtered_todo[task_list_index]['id']
        user = os.environ.get('homepath')
        user_f = user.replace("\\","/")
        file_path = 'C:' + user_f + gazu.files.build_working_file_path(active_id)
        
        if filtered_todo[task_list_index]['task_type_name'] == 'lighting':
            directory = file_path + '_lighting.blend'
        elif filtered_todo[task_list_index]['task_type_name'] == 'rendering':
            directory = file_path + '_lighting.blend'
        elif filtered_todo[task_list_index]['task_type_name'] == 'previz':
            directory = file_path + '_layout.blend'
        elif filtered_todo[task_list_index]['task_type_name'] == 'layout':
            directory = file_path + '_layout.blend'
        elif filtered_todo[task_list_index]['task_type_name'] == 'anim':
            directory = file_path + '_anim.blend'
        else:
            directory = file_path + '.blend'
        try:
            if self.save_bool == True:
                bpy.ops.wm.save_mainfile()
            bpy.ops.wm.open_mainfile(filepath= directory, load_ui=False)
        except:
            self.report({'WARNING'}, 'file path incorrect, check file tree')
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
        task_list_index = bpy.context.scene.col_idx
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
        task_list_index = bpy.context.scene.col_idx
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


    # @classmethod
    # def poll(cls, context):
    #     if len(status_name) == 0:
    #         s = 1
    #     else:
    #         s = 0
    #     return s == 0
    #     # try:
    #     #     status_name[0]
    #     #     s = 0
    #     # except:
    #     #     s = 1
    #     # return s ==1

    def execute(self, context):
        task_list_index = bpy.context.scene.col_idx
        gazu.task.add_comment(filtered_todo[task_list_index]['id'], status_name[0], self.comment)
        displayed_tasks[task_list_index][1] = status_name[0]['short_name']
        for item in todo:
            if item['id'] == filtered_todo[task_list_index]['id']:
                item['task_status_short_name'] = status_name[0]['short_name']
        for item in projects:
            if item['id'] == filtered_todo[task_list_index]['id']:
                item['task_status_short_name'] = status_name[0]['short_name']  
        print(filtered_todo[task_list_index])
        bpy.context.scene.update_tag()
        bpy.app.handlers.depsgraph_update_pre.append(update_list)
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
            layout.operator('nagato.filter', text= task).task= task
       
############### all classes ####################    
classes = [
        NagatoSetHost,
        NAGATO_OT_SetHost,
        NAGATO_OT_Login,
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
        NAGATO_OT_UpdateStatus
        ]  
    
    
# registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.col = bpy.props.CollectionProperty(type=MyTasks)
    bpy.types.Scene.col_idx = bpy.props.IntProperty(default=0)

    bpy.app.handlers.depsgraph_update_pre.append(update_list)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
        
    del bpy.types.Scene.col
    del bpy.types.Scene.col_idx