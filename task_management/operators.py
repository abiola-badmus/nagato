import bpy
import os
from .. import gazu, profile
from ..gazu.exception import NotAuthenticatedException
from requests.exceptions import ConnectionError
from bpy.types import Operator
from bpy.props import (StringProperty, BoolProperty, EnumProperty)
import ctypes
import subprocess
# from ..svn.operators import svn_client
from ..svn.operators import update_tasks_list

NagatoProfile = profile.NagatoProfile
task_file_directory = NagatoProfile.task_file_directory
slugify = NagatoProfile.slugify


class NAGATO_OT_Projects(Operator):
    bl_label = 'projects'
    bl_idname = 'nagato.projects'
    bl_description = 'select project'    
    
    project: StringProperty(default='')
    
    def execute(self, context):
        NagatoProfile.active_project = gazu.project.get_project_by_name(self.project)
        NagatoProfile.active_task_type = None
        context.scene.tasks.clear()
        # bpy.ops.nagato.assets_refresh()
        self.report({'INFO'}, f'Project: {self.project}')
        return{'FINISHED'}


class NAGATO_OT_Filter(Operator):
    bl_label = 'filter'
    bl_idname = 'nagato.filter'
    bl_description = 'filter task'    
    
    filter: StringProperty(default='')
    
    def execute(self, context):
        # scene = context.scene
        update_tasks_list(
            scene=context.scene,
            tasks=NagatoProfile.tasks,
            active_project=NagatoProfile.active_project['name'],
            active_task_type=self.filter
        )
        self.report({'INFO'}, 'filtered by ' + self.filter)
        return{'FINISHED'}


class NAGATO_OT_OpenFile(Operator):
    bl_label = 'open task file'
    bl_idname = 'nagato.open'
    bl_description = 'opens active selected task file'

    save_bool: bpy.props.BoolProperty()
    load_ui: bpy.props.BoolProperty()
    new_instance: bpy.props.BoolProperty()

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

    @staticmethod
    def open_file(blender_exe, file_path):
        subprocess.Popen(f"{blender_exe} {file_path}")

    def draw(self, context):
        row = self.layout.row()
        row.prop(self, "load_ui", text="LOAD UI")
        row.prop(self, "save_bool", text="SAVE FILE")
        row.prop(self, "new_instance", text="NEW INSTANCE")
    
    def execute(self, context):
        active_project = NagatoProfile.active_project
        task_list_index = bpy.context.scene.tasks_idx
        active_project_tasks = NagatoProfile.tasks[active_project['name']]
        active_task = active_project_tasks[NagatoProfile.active_task_type][task_list_index]
        blend_file_path = os.path.expanduser(active_task['working_file_path'])
        active_task_id = active_task['id']
        entity_id = active_project_tasks[NagatoProfile.active_task_type][task_list_index]["entity_id"]
        task_type = NagatoProfile.tasks[NagatoProfile.active_project['name']]\
            [NagatoProfile.active_task_type][task_list_index]['task_type_name']
        #TODO open editing files 
        if task_type.lower() in {'editing', 'edit'}:
            project_file_name = slugify(active_project['name'], separator="_")
            if active_task['episode_name'] == None:
                base_file_directory = os.path.join(active_project['file_tree']['working']['mountpoint'], \
                active_project['file_tree']['working']['root'],project_file_name,'edit','edit.blend')
            else:
                episode_name = slugify(active_task['episode_name'], separator="_")
                base_file_directory = os.path.join(active_project['file_tree']['working']['mountpoint'], \
                    active_project['file_tree']['working']['root'],project_file_name,'edit',f"{episode_name}_edit.blend")
            directory = os.path.expanduser(base_file_directory)
        else:
            directory = task_file_directory(task_type.lower(), blend_file_path, active_project)
        task_file_data = {'task_type':task_type, 'task_id':active_task_id, 'entity_id':entity_id}
        if directory:
            try:
                if self.new_instance == True:
                    self.open_file(blender_exe=bpy.app.binary_path, file_path=directory)
                else:
                    if self.save_bool == True:
                        bpy.ops.wm.save_mainfile()
                    bpy.ops.wm.open_mainfile(filepath= directory, load_ui=self.load_ui)
                    NagatoProfile.lastest_openfile['file_path'] = bpy.context.blend_data.filepath
                    NagatoProfile.lastest_openfile['task_id'] = active_task_id
                    NagatoProfile.lastest_openfile['entity_id'] = entity_id
                    NagatoProfile.lastest_openfile['task_type'] = task_type
                    scene = bpy.data.scenes.get('main')
                    scene['task_file_data'] = task_file_data
            except RuntimeError as err:
                self.report({'WARNING'}, f'{err}')
        else:
             self.report({'WARNING'}, 'no file for task, check task file map')
        bpy.ops.nagato.filter(filter=NagatoProfile.active_task_type)
        context.scene.tasks_idx = task_list_index
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
        webbrowser.open_new_tab(url)
        del webbrowser
        self.report({"INFO"}, f"Opened a browser at {url}")

        return {"FINISHED"}


# deprecated
class NAGATO_OT_UpdateStatus(Operator):
    bl_label = 'update status'
    bl_idname = 'nagato.update_status'
    bl_description = 'update status'

    comment: StringProperty(
        name = 'comment',
        default = '',
        description = 'type your comment'
        )

    preview_path: StringProperty(
        name = 'add preview',
        default = '',
        description = 'path to preview file'
        )

    render_type: EnumProperty(
        items={
            ('opengl', 'opengl', 'render with opengl'),
            ('full', 'full', 'render full image'),
            ('50%', '50%', r'render 50% of image')},
        default='opengl',
        name= "Render type",
        description="choose a render type",
        )
    status: EnumProperty(
        items={
            ('todo', 'todo', 'set task status to todo'),
            ('wip', 'wip', 'set task status to work in progress'),
            ('wfa', 'wfa', 'set task status to waiting for approver')},
        default='wip',
        name= "Task status",
        description="update task status",
        )
    render_preview: BoolProperty(
        name = 'Render Preview',
        default = False,
        description = 'send render preview of opened task'
    )


    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        task_list_index = bpy.context.scene.tasks_idx
        task = NagatoProfile.tasks[NagatoProfile.active_project['name']][NagatoProfile.active_task_type][task_list_index]
        task_file_path = task['full_working_file_path']
        file_name = os.path.basename(task_file_path)

        row = self.layout
        row.label(text = f'file name: {file_name}')

        row.prop(self, "status")
        row.prop(self, "comment")
        row.prop(self, "preview_path")
        # row.prop(self, "render_preview")
        # row.prop(self, "render_type")

    def execute(self, context):
        try:
            status = gazu.task.get_task_status_by_short_name(self.status)
            task_list_index = bpy.context.scene.tasks_idx
            task = NagatoProfile.tasks[NagatoProfile.active_project['name']][NagatoProfile.active_task_type][task_list_index]

            if self.render_preview:
                if task['task_type_name'].lower() in {'modeling'}:
                    bpy.ops.render.opengl()
                    profile_path = bpy.utils.user_resource('CONFIG', 'nagato', create=True)
                    render_path = os.path.join(profile_path, 'render', 'render.png')
                    # render = tempfile.NamedTemporaryFile(prefix='nagato', delete=True)
                    bpy.data.images['Render Result'].save_render(render_path)


            if self.preview_path == '':
                gazu.task.add_comment(task['id'], status, self.comment)
            elif self.render_preview:
                comment = gazu.task.add_comment(task['id'], status, self.comment, attachments=[render_path])
                gazu.task.add_preview(task['id'], comment, render_path)

            elif os.path.isfile(self.preview_path):
                comment = gazu.task.add_comment(task['id'], status, self.comment, attachments=[self.preview_path])
                gazu.task.add_preview(task['id'], comment, self.preview_path)
            else:
                self.report({'WARNING'}, "preview file do not exist")
                return{'FINISHED'}
            displayed_tasks[task_list_index][1] = status['short_name']
            task['task_status_short_name'] = status['short_name']
            self.report({'INFO'}, "status updated")
        except IndexError:
            self.report({'WARNING'}, "No status selected.")
        return{'FINISHED'}


class NAGATO_OT_PostComment(Operator):
    bl_label = 'post comment'
    bl_idname = 'nagato.post_comment'
    bl_description = 'post comment'    
    
    @classmethod
    def poll(cls, context):
        try:
            task_list_index = bpy.context.scene.tasks_idx
            NagatoProfile.tasks[NagatoProfile.active_project['name']][NagatoProfile.active_task_type][task_list_index]['id']
            status = 1
        except:
            status = 0
        return status == 1

    def execute(self, context):
        status = gazu.task.get_task_status_by_short_name(context.scene.status)
        task_list_index = bpy.context.scene.tasks_idx
        task = NagatoProfile.tasks[NagatoProfile.active_project['name']][NagatoProfile.active_task_type][task_list_index]
        preview = bpy.path.abspath(context.window_manager.preview_path)
        if preview == '':
            gazu.task.add_comment(task['id'], status, context.scene.comment)
        elif os.path.isfile(preview):
            comment = gazu.task.add_comment(task['id'], status, context.scene.comment, attachments=[preview])
            gazu.task.add_preview(task['id'], comment, preview)
        else:
            self.report({'WARNING'}, "preview file do not exist")
            return{'FINISHED'}
        task['task_status_short_name'] = status['short_name']
        bpy.ops.nagato.filter(filter=NagatoProfile.active_task_type)
        context.window_manager.preview_path = ''
        context.scene.comment = ''
        self.report({'INFO'}, "status updated")
        return{'FINISHED'}


############### all classes ####################    
classes = [
        NAGATO_OT_Filter,
        NAGATO_OT_OpenFile,
        NAGATO_OT_project_open_in_browser,
        NAGATO_OT_Projects,
        # NAGATO_OT_SetStatus,
        # NAGATO_MT_StatusList,
        # NAGATO_OT_UpdateStatus,
        NAGATO_OT_PostComment,
        ]

# registration
def register():
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

    # bpy.app.handlers.depsgraph_update_pre.append(update_list)
    # bpy.app.handlers.save_post.append(update_current_file_data)
    # bpy.app.handlers.load_post.append(create_main_collection)
    # bpy.app.handlers.load_factory_preferences_post.append(load_handler)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)  