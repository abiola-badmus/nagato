import bpy
import os, stat, shutil
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty
from .. import profile, gazu
from bpy.app.handlers import persistent
import threading
from ..ui import NAGATO_PT_TaskManagementPanel

from sys import platform
if platform == "linux" or platform == "linux2":
    from .. import pysvn_linux as pysvn
elif platform == "darwin":
    pass
#     from . import pysvn_osx as pysvn
elif platform == "win32":
    from .. import pysvn_win as pysvn
svn_client = pysvn.Client()
ClientError = pysvn.ClientError
svn_client.exception_style = 1
download_in_progress = False

percentage = 0
cancel_download = False
NagatoProfile = profile.NagatoProfile
slugify = NagatoProfile.slugify
svn_logged_in = True
revisions_list = list()
# client = pysvn.Client()

#TODO update svn status on save
@persistent
def update_current_file_data(dummy):
    # bpy.app.handlers.save_pre.remove(update_current_file_data)
    if NagatoProfile.active_project and NagatoProfile.active_task_type:
        update_tasks_list(
            scene=bpy.context.scene,
            tasks=NagatoProfile.tasks,
            active_project=NagatoProfile.active_project['name'],
            active_task_type=NagatoProfile.active_task_type
        )


def update_tasks_list(scene, tasks, active_project, active_task_type):
    try:
        scene.tasks.clear()
    except AttributeError as e:
        print(str(e) + '\nTasks list is not found')
    for i, file in enumerate(tasks[active_project][active_task_type]):
        # bpy.app.handlers.depsgraph_update_pre.remove(update_list)
        #TODO add file svn status
        try:
            file_path = file['full_working_file_path']
            if file_path == None:
                file_status = 'not_existing'
            elif os.path.isfile(file_path):
                file_status = str(svn_client.status(file_path)[0].text_status)
            else:
                file_status = 'not_existing'
        except KeyError:
            file_status = 'not_existing'
        NagatoProfile.active_task_type = active_task_type
        if file['task_type_name'] == active_task_type:
            if file['sequence_name'] == None:
                task_name = file['entity_name']
            else:
                task_name = f"{file['sequence_name']}_{file['entity_name']}"
            task_status = file['task_status_short_name']
            task_id = file['id']
            try:
                colection = scene.tasks.add()   
                colection.tasks = task_name
                colection.tasks_status = task_status 
                colection.file_status = file_status
                colection.task_id = task_id
                colection.tasks_idx = i
            except AttributeError as e:
                print(str(e) + '\nTasks list is not found')


def download_project(scene, svn_client, username, password, project_path, repo_url, report):
    try:
        svn_client.set_default_username(username)
        svn_client.set_default_password(password)
        if os.path.isdir(project_path) == False:
            os.makedirs(project_path)
        if len(os.listdir(project_path)) == 0:
            try:
                if svn_client.is_url(repo_url):
                    svn_client.checkout(repo_url, project_path)
                    if NagatoProfile.active_project and NagatoProfile.active_task_type:
                        update_tasks_list(
                            scene=scene,
                            tasks=NagatoProfile.tasks,
                            active_project=NagatoProfile.active_project['name'],
                            active_task_type=NagatoProfile.active_task_type
                            )
                    report({'INFO'}, "project files downloaded")
                else:
                    report({'INFO'}, "SVN url invalid")
            except ClientError as e:
                if 'cancelled by user' in str(e):
                    report({'INFO'}, "download cancelled")
                    # os.removedirs(project_path)
                    # shutil.rmtree(project_path)
                else:
                    report({'WARNING'}, str(e))
        # elif os.path.isdir(os.path.join(project_path, '.svn')) == True:
        #     bpy.ops.nagato.update_all()
        #     report({'INFO'}, "project file updated")
        # elif len(os.listdir(project_path)) != 0:
        #     report({'WARNING'}, f"Directory is not empty, Cant download project into {project_path}")
        return{'FINISHED'}
    except (TypeError, KeyError):
        report({'WARNING'}, "svn url not set")
        return{'FINISHED'}

def redraw_panel():
	try:
		bpy.utils.unregister_class(NAGATO_PT_TaskManagementPanel)
	except:
		pass
	bpy.utils.register_class(NAGATO_PT_TaskManagementPanel)

class OBJECT_OT_NagatoAdd(Operator):
    bl_label = 'Add file to SVN'
    bl_idname = 'nagato.add'
    bl_description = 'Add current file to project repository'
    
    @classmethod
    def poll(cls, context):
        return bool(NagatoProfile.user)


    def execute(self, context):  
        try:
            status = svn_client.status(f'{bpy.context.blend_data.filepath}')[0]
            if str(status.text_status) == 'unversioned':
                r = str(status)[13:-1].replace('\\\\', '/')
                svn_client.add(r[1:-1])
                self.report({'INFO'}, "File Added to Repository")
            else:
                self.report({'WARNING'}, "All files under version control")
        except ClientError:
            self.report({'WARNING'}, "Not a working copy")
        return{'FINISHED'}
        

class OBJECT_OT_NagatoPublishSelected(Operator):
    bl_label = 'Publish selected file'
    bl_idname = 'nagato.publish_selected'
    bl_description = 'Publish selected file to project repository'
    
    comment: StringProperty(
        name = 'comment',
        default = '',
        description = 'comment for publishing'
        )
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


    @classmethod
    def poll(cls, context):
        try:
            task_list_index = bpy.context.scene.tasks_idx
            NagatoProfile.tasks[NagatoProfile.active_project['name']][NagatoProfile.active_task_type][task_list_index]['id']
            status = 1
        except:
            status = 0
        return status == 1

    def draw(self, context):
        if svn_logged_in:
            layout = self.layout
            if self.comment == '':
                layout.alert = True
                layout.label(text = 'you have to write a comment')
                if self.comment == '':
                    layout.alert = True
                else:
                    layout.alert = False
            layout.prop(self, "comment")
        else:
            layout = self.layout
            if self.comment == '':
                layout.alert = True
                layout.label(text = 'you have to write a comment')
                if self.comment == '':
                    layout.alert = True
                else:
                    layout.alert = False
            layout.prop(self, "comment")
            layout.prop(self, "username")
            layout.prop(self, "password")
  
    def invoke(self, context, event):
        global svn_logged_in
        active_project = NagatoProfile.active_project
        task_list_index = bpy.context.scene.tasks_idx
        active_project_tasks = NagatoProfile.tasks[active_project['name']]
        active_task = active_project_tasks[NagatoProfile.active_task_type][task_list_index]
        directory = active_task['full_working_file_path']
        if not os.path.isfile(directory):
            self.report({'WARNING'}, 'file deos not exist yet, pls download project file or update project')
            return{'FINISHED'}

        try:
            svn_client.ls(svn_client.info(directory).url)
        except ClientError as e:
            if str(e) == 'callback_get_login required':
                svn_logged_in = False
                return context.window_manager.invoke_props_dialog(self)
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        global svn_logged_in
        active_project = NagatoProfile.active_project
        task_list_index = bpy.context.scene.tasks_idx
        active_project_tasks = NagatoProfile.tasks[active_project['name']]
        active_task = active_project_tasks[NagatoProfile.active_task_type][task_list_index]
        directory = active_task['full_working_file_path']
        if not os.path.isfile(directory):
            self.report({'WARNING'}, 'file deos not exist yet, pls download project file or update project')
            return{'FINISHED'}

        user = NagatoProfile.user['full_name']
        
        try:
            if svn_logged_in == False:
                svn_client.set_default_username(self.username)
                svn_client.set_default_password(self.password)
            if self.comment == '':
                self.report({'WARNING'}, 'Publish failed, no comment added')
                return{'FINISHED'}
            if NagatoProfile.lastest_openfile['file_path'] == bpy.context.blend_data.filepath:
                bpy.ops.wm.save_mainfile()
            svn_client.checkin(directory, f'{self.comment}')
            statuses = svn_client.status(os.path.dirname(directory) + 'maps')
            for status in statuses:
                if str(status.text_status) in {'modified', 'added'}:
                    map_dir = str(status)[13:-1].replace('\\\\', '/')
                    svn_client.checkin([map_dir[1:-1]], self.comment)
            svn_logged_in = True
            update_tasks_list(
                            scene=context.scene,
                            tasks=NagatoProfile.tasks,
                            active_project=NagatoProfile.active_project['name'],
                            active_task_type=NagatoProfile.active_task_type
                            )
            context.preferences.addons['nagato'].preferences.error_message = ''
            self.report({'INFO'}, "Publish successful")
        except ClientError as e:
            if str(e) == 'callback_get_login required':
                svn_logged_in = False
                context.preferences.addons['nagato'].preferences.error_message = 'SVN Username and/or password is incorrect'
            update_tasks_list(
                            scene=context.scene,
                            tasks=NagatoProfile.tasks,
                            active_project=NagatoProfile.active_project['name'],
                            active_task_type=NagatoProfile.active_task_type
                            )
            
            self.report({'ERROR'}, str(e))
        # bpy.context.scene.update_tag()

        return{'FINISHED'}


class OBJECT_OT_NagatoUpdateSelected(Operator):
    bl_label = 'Update selected file'
    bl_idname = 'nagato.update_selected'
    bl_description = 'Update selected file from project repository'

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
        
    def invoke(self, context, event):
        global svn_logged_in
        active_project = NagatoProfile.active_project
        task_list_index = bpy.context.scene.tasks_idx
        active_project_tasks = NagatoProfile.tasks[active_project['name']]
        active_task = active_project_tasks[NagatoProfile.active_task_type][task_list_index]
        directory = active_task['full_working_file_path']
        if not os.path.isfile(directory):
            self.report({'WARNING'}, 'file deos not exist yet, pls download project file or update project')
            return{'FINISHED'}

        try:
            svn_client.update(directory)
            svn_client.update(os.path.dirname(directory) + 'maps')
            # bpy.ops.wm.revert_mainfile()
            if NagatoProfile.lastest_openfile['file_path'] == bpy.context.blend_data.filepath:
                bpy.ops.wm.revert_mainfile()
            update_tasks_list(
                            scene=context.scene,
                            tasks=NagatoProfile.tasks,
                            active_project=NagatoProfile.active_project['name'],
                            active_task_type=NagatoProfile.active_task_type
                            )
            self.report({'INFO'}, "Update Successful")
            return{'FINISHED'}
        except ClientError as e:
            if str(e) == 'callback_get_login required':
                return context.window_manager.invoke_props_dialog(self)
            self.report({'WARNING'}, str(e))
            return{'FINISHED'}
    
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
        global svn_logged_in
        active_project = NagatoProfile.active_project
        task_list_index = bpy.context.scene.tasks_idx
        active_project_tasks = NagatoProfile.tasks[active_project['name']]
        active_task = active_project_tasks[NagatoProfile.active_task_type][task_list_index]
        directory = active_task['full_working_file_path']
        if not os.path.isfile(directory):
            self.report({'WARNING'}, 'file deos not exist yet, pls download project file or update project')
            return{'FINISHED'}

        try:
            svn_client.set_default_username(self.username)
            svn_client.set_default_password(self.password)

            svn_client.update(directory)
            svn_client.update(os.path.dirname(directory) + 'maps')
            if NagatoProfile.lastest_openfile['file_path'] == bpy.context.blend_data.filepath:
                bpy.ops.wm.revert_mainfile()
            update_tasks_list(
                            scene=context.scene,
                            tasks=NagatoProfile.tasks,
                            active_project=NagatoProfile.active_project['name'],
                            active_task_type=NagatoProfile.active_task_type
                            )
            self.report({'INFO'}, "Update Successful")
        except ClientError as err:
            self.report({'WARNING'}, str(err))
        return{'FINISHED'}


class NAGATO_OT_UpdateToRevision(Operator):
    bl_label = 'revert to revision'
    bl_idname = 'nagato.update_to_revision'
    bl_description = 'revert to revision'

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

    def execute(self, context):
        global svn_logged_in
        active_project = NagatoProfile.active_project
        task_list_index = bpy.context.scene.tasks_idx
        active_project_tasks = NagatoProfile.tasks[active_project['name']]
        active_task = active_project_tasks[NagatoProfile.active_task_type][task_list_index]
        directory = active_task['full_working_file_path']
        if not os.path.isfile(directory):
            self.report({'WARNING'}, 'file deos not exist yet, pls download project file or update project')
            return{'FINISHED'}

        try:
            # logs = svn_client.log(directory)
            # logs.reverse()
            revision = revisions_list[context.scene.revisions_idx]
            roll_back_file= svn_client.cat(directory, revision)
            with open(directory, 'w+b') as f:
                f.write(roll_back_file)
            if NagatoProfile.lastest_openfile['file_path'] == bpy.context.blend_data.filepath:
                bpy.ops.wm.revert_mainfile()
            update_tasks_list(
                            scene=context.scene,
                            tasks=NagatoProfile.tasks,
                            active_project=NagatoProfile.active_project['name'],
                            active_task_type=NagatoProfile.active_task_type
                            )
            self.report({'INFO'}, "revert to revision Successful")
            return{'FINISHED'}
        except ClientError as e:
            if str(e) == 'callback_get_login required':
                return context.window_manager.invoke_props_dialog(self)
            self.report({'WARNING'}, str(e))
        return{'FINISHED'}


class NAGATO_OT_RevisionLog(Operator):
    bl_label = 'verson history'
    bl_idname = 'nagato.revision_log'
    bl_description = 'verson history'

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
        global svn_logged_in
        active_project = NagatoProfile.active_project
        task_list_index = bpy.context.scene.tasks_idx
        active_project_tasks = NagatoProfile.tasks[active_project['name']]
        active_task = active_project_tasks[NagatoProfile.active_task_type][task_list_index]
        directory = active_task['full_working_file_path']
        if not os.path.isfile(directory):
            self.report({'WARNING'}, 'file deos not exist yet, pls download project file or update project')
            return{'FINISHED'}

        try:
            svn_client.ls(svn_client.info(directory).url)
        except ClientError as e:
            if str(e) == 'callback_get_login required':
                svn_logged_in = False
                return context.window_manager.invoke_props_dialog(self)

        logs = svn_client.log(directory)
        logs.reverse()
        formatted_log  = list()
        revisions_list.clear()
        for i, log in enumerate(logs, 0):
            from datetime import datetime
            date = datetime.fromtimestamp(log.date).strftime('%d-%m-%Y')
            revisions_list.append(log.revision)
            formatted_log.append([str(i), log.message, log.author, str(date)])

        try:
            context.scene.revisions.clear()
        except:
            pass
        for i, (revision, message, author, date) in enumerate(formatted_log, 0): 
            colection = context.scene.revisions.add()   
            colection.revision = revision
            colection.message = message 
            colection.author = author
            colection.date = date
            colection.revisions_idx = i
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        if svn_logged_in:
            revisions_list_index = context.scene.revisions_idx
            revision = context.scene.revisions[revisions_list_index]

            row = self.layout
            row.label(text ='No.' + ' '*10 + 'User' +' '*30 +'Date Published')
            row.template_list("REVISIONS_UL_list", "", context.scene, "revisions", context.scene, "revisions_idx", rows=6)

            row.label(text = f'{revision["message"]}')
            row.operator('nagato.update_to_revision')
        else:
            layout = self.layout
            layout.alert = True
            layout.label(text = 'pls log in and try checking log again')
            layout.alert = False
            layout.prop(self, "username")
            layout.prop(self, "password")

    def execute(self, context):
        if svn_logged_in == False:
                svn_client.set_default_username(self.username)
                svn_client.set_default_password(self.password)
                svn_logged_in == True
        return{'FINISHED'}


class Nagato_OT_UpdateAll(Operator):
    bl_label = 'Update project files'
    bl_idname = 'nagato.update_all'
    bl_description = 'Update all files in project repository'

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

    def invoke(self, context, event):
        mount_point = NagatoProfile.active_project['file_tree']['working']['mountpoint']
        root = NagatoProfile.active_project['file_tree']['working']['root']
        project_file_name = slugify(NagatoProfile.active_project['name'], separator='_')
        project_folder = os.path.expanduser(os.path.join(mount_point, root, project_file_name))
        try:
            for file in os.listdir(project_folder):
                try:
                    svn_client.update(os.path.join(project_folder, file))
                except ClientError as error:
                    if str(error) == 'callback_get_login required':
                        return context.window_manager.invoke_props_dialog(self)
                    self.report({'WARNING'}, str(error))
            if bpy.data.is_saved:
                bpy.ops.wm.revert_mainfile()
            if NagatoProfile.active_task_type:
                update_tasks_list(
                    scene=context.scene,
                    tasks=NagatoProfile.tasks,
                    active_project=NagatoProfile.active_project['name'],
                    active_task_type=NagatoProfile.active_task_type
                    )
            self.report({'INFO'}, "Update Successful")
        except FileNotFoundError:
            self.report({'WARNING'}, 'project files do not exist')
        return{'FINISHED'}
    
    @classmethod
    def poll(cls, context):
        return bool(NagatoProfile.user) and bool(NagatoProfile.active_project) and not download_in_progress

    def execute(self, context):
        svn_client.set_default_username(self.username)
        svn_client.set_default_password(self.password)

        mount_point = NagatoProfile.active_project['file_tree']['working']['mountpoint']
        root = NagatoProfile.active_project['file_tree']['working']['root']
        project_folder = os.path.expanduser(os.path.join(mount_point, root, NagatoProfile.active_project['name']))
        try:
            for file in os.listdir(project_folder):
                try:
                    svn_client.update(os.path.join(project_folder, file))
                    if bpy.data.is_saved:
                        bpy.ops.wm.revert_mainfile()
                    update_tasks_list(
                        scene=context.scene,
                        tasks=NagatoProfile.tasks,
                        active_project=NagatoProfile.active_project['name'],
                        active_task_type=NagatoProfile.active_task_type
                        )
                    self.report({'INFO'}, "Update Successful")
                except ClientError as error:
                    self.report({'WARNING'}, str(error))
        except FileNotFoundError:
            self.report({'WARNING'}, 'project files do not exist')
        return{'FINISHED'}


class Nagato_OT_RevertSelected(Operator):
    bl_label = 'reset file'
    bl_idname = 'nagato.revert_selected'
    bl_description = 'revert to last checkpoint'
    
    @classmethod
    def poll(cls, context):
        try:
            task_list_index = bpy.context.scene.tasks_idx
            NagatoProfile.tasks[NagatoProfile.active_project['name']][NagatoProfile.active_task_type][task_list_index]['id']
            status = 1
        except:
            status = 0
        return status == 1
    
    def draw(self, context):
        layout = self.layout
        layout.alert = True
        layout.label(text='you will lose all changes before last publish')
        layout.alert = False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)



    def execute(self, context):
        active_project = NagatoProfile.active_project
        task_list_index = bpy.context.scene.tasks_idx
        active_project_tasks = NagatoProfile.tasks[active_project['name']]
        active_task = active_project_tasks[NagatoProfile.active_task_type][task_list_index]
        directory = active_task['full_working_file_path']
        if not os.path.isfile(directory):
            self.report({'WARNING'}, 'file deos not exist yet, pls download project file or update project')
            return{'FINISHED'}

        try:
            svn_client.revert(directory)
            if NagatoProfile.lastest_openfile['file_path'] == bpy.context.blend_data.filepath:
                bpy.ops.wm.revert_mainfile()
            update_tasks_list(
                            scene=context.scene,
                            tasks=NagatoProfile.tasks,
                            active_project=NagatoProfile.active_project['name'],
                            active_task_type=NagatoProfile.active_task_type
                            )
            self.report({'INFO'}, "reverted")
        except ClientError as e:
            self.report({'WARNING'}, str(e))
        return{'FINISHED'}


class Nagato_OT_Resolve(Operator):
    bl_label = 'resolve conflict'
    bl_idname = 'nagato.resolve'
    bl_description = 'resolve file conflict'

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
    
    @classmethod
    def poll(cls, context):
        try:
            task_list_index = bpy.context.scene.tasks_idx
            NagatoProfile.tasks[NagatoProfile.active_project['name']][NagatoProfile.active_task_type][task_list_index]['id']
            status = 1
        except:
            status = 0
        return status == 1

    def draw(self, context):
        if svn_logged_in:
            layout = self.layout
            layout.alert = True
            layout.label(text='if you want to keep newly fetched file use the reset button instead')
            layout.alert = False
            # pass
        else:
            layout = self.layout
            layout.alert = True
            layout.label(text='if you want to keep new fetch file use the reset button instead')
            layout.alert = False
            layout.prop(self, "username")
            layout.prop(self, "password")

    def invoke(self, context, event):
        global svn_logged_in
        active_project = NagatoProfile.active_project
        task_list_index = bpy.context.scene.tasks_idx
        active_project_tasks = NagatoProfile.tasks[active_project['name']]
        active_task = active_project_tasks[NagatoProfile.active_task_type][task_list_index]
        directory = active_task['full_working_file_path']
        if not os.path.isfile(directory):
            self.report({'WARNING'}, 'file deos not exist yet, pls download project file or update project')
            return{'FINISHED'}

        try:
            svn_client.ls(svn_client.info(directory).url)
        except ClientError as e:
            if str(e) == 'callback_get_login required':
                svn_logged_in = False
                return context.window_manager.invoke_props_dialog(self)
        # return self.execute(context)
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        global svn_logged_in
        active_project = NagatoProfile.active_project
        task_list_index = bpy.context.scene.tasks_idx
        active_project_tasks = NagatoProfile.tasks[active_project['name']]
        active_task = active_project_tasks[NagatoProfile.active_task_type][task_list_index]
        directory = active_task['full_working_file_path']
        if not os.path.isfile(directory):
            self.report({'WARNING'}, 'file deos not exist yet, pls download project file or update project')
            return{'FINISHED'}

        try:
            if svn_logged_in == False:
                svn_client.set_default_username(self.username)
                svn_client.set_default_password(self.password)

            svn_client.resolved(directory)
            svn_logged_in = True
            update_tasks_list(
                            scene=context.scene,
                            tasks=NagatoProfile.tasks,
                            active_project=NagatoProfile.active_project['name'],
                            active_task_type=NagatoProfile.active_task_type
                            )
            self.report({'INFO'}, "conflict resolved")
        except ClientError as e:
            self.report({'WARNING'}, str(e))
        return{'FINISHED'}


class Nagato_OT_CleanUp(Operator):
    bl_label = 'clean up'
    bl_idname = 'nagato.clean_up'
    bl_description = 'clean up files'
    
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
        mount_point = NagatoProfile.active_project['file_tree']['working']['mountpoint']
        root = NagatoProfile.active_project['file_tree']['working']['root']
        project_file_name = slugify(NagatoProfile.active_project['name'], separator='_')
        project_folder = os.path.expanduser(os.path.join(mount_point, root, project_file_name))
        try:
            svn_client.cleanup(project_folder)
            self.report({'INFO'}, "clean up succesful")
        except ClientError as e:
            self.report({'WARNING'}, str(e))
        return{'FINISHED'}


class Nagato_OT_CheckOut(Operator):
    bl_label = 'Download files'
    bl_idname = 'nagato.check_out'
    bl_description = 'checkout project files'
    
    username: StringProperty(
        name = 'Username',
        default = '',
        description = 'input svn username'
        )

    password: StringProperty(
        subtype = 'PASSWORD',
        name = 'Password',
        default = '',
        description = 'input your svn password'
        )
    
    ran_download: BoolProperty(default=False)

    def draw(self, context):
        row = self.layout

        row.prop(self, "username")
        row.prop(self, "password")
        
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    @classmethod
    def poll(cls, context):
        return bool(NagatoProfile.user) and NagatoProfile.active_project != None and not download_in_progress

    def modal(self, context, event):
        global percentage
        global download_in_progress
        # if event.type in {'ESC'}:
        #     global cancel_download
        #     download_in_progress = False
        #     cancel_download = True
        #     percentage = 0
        #     context.scene.progress_bar = percentage
        #     self.ran_download == False
        #     wm = context.window_manager
        #     wm.event_timer_remove(self._timer)
        #     # del self.svn_download_client
        #     # svn_client.cleanup(self.file_path)
        #     return {'FINISHED'}

        if event.type == 'TIMER':
            if self.ran_download == False:
                self.ran_download = True
                download_in_progress = True
                # threading.Thread(target=self.do_some_thing).start()
                threading.Thread(target=download_project,
                                args=[context.scene, self.svn_download_client, self.username, self.password, self.file_path, self.repo_url, self.report]
                                ).start()
            context.scene.progress_bar = percentage
            redraw_panel()
        if int(percentage) == 100:
            percentage = 0
            context.scene.progress_bar = percentage
            self.ran_download = False
            download_in_progress = False
            wm = context.window_manager
            wm.event_timer_remove(self._timer)
            return {'FINISHED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        self.svn_download_client = pysvn.Client()
        project_info = NagatoProfile.active_project
        self.repo_url = project_info['data']['svn_url']
        root = project_info['file_tree']['working']['root']
        mount_point = project_info['file_tree']['working']['mountpoint']
        self.svn_download_client.set_default_username(self.username)
        self.svn_download_client.set_default_password(self.password)
        project_file_name = slugify(NagatoProfile.active_project['name'] ,separator='_')
        self.file_path = os.path.expanduser(os.path.join(mount_point, root, project_file_name))
        self.total_files = len(self.svn_download_client.list(self.repo_url, recurse=True))
        notify_file_path = self.file_path
        notify_total_file = self.total_files
        def notify( event_dict ):
            global percentage
            totalFiles = 0
            totalDir = 0
            for base, dirs, files in os.walk(notify_file_path):
                if '.svn' in base:
                    continue
                for directories in dirs:
                    totalDir += 1
                for Files in files:
                    totalFiles += 1
            percentage = ((totalDir + totalFiles) / notify_total_file) * 100

        def cancel():
            return cancel_download

        self.svn_download_client.callback_notify = notify
        self.svn_download_client.callback_cancel  = cancel
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class Nagato_OT_DeleteProject(Operator):
    bl_label = 'delete project'
    bl_idname = 'nagato.delete'
    bl_description = 'delete project files'

    def execute(self, context):
        #TODO delete project files
        global svn_client
        svn_client = pysvn.Client()
        # try:
        #     del svn_client
        #     print('delete svn client')
        #     # del Nagato_OT_CheckOut.svn_download_client
        #     # print('delere svn_download_client')
        # except NameError:
        #     pass

        # try:
        #     bpy.utils.unregister_class(Nagato_OT_CheckOut)
        # except:
        #     pass
	    # bpy.utils.register_class(Nagato_OT_CheckOut)
        project_info = NagatoProfile.active_project
        root = project_info['file_tree']['working']['root']
        mount_point = project_info['file_tree']['working']['mountpoint']
        project_file_name = slugify(NagatoProfile.active_project['name'] ,separator='_')
        project_path = os.path.expanduser(os.path.join(mount_point, root, project_file_name))
        # shutil.rmtree(project_path)

        def on_rm_error( func, path, exc_info):
            # path contains the path of the file that couldn't be removed
            # let's just assume that it's read-only and unlink it.
            os.chmod( path, stat.S_IWRITE )
            os.unlink( path )
        if os.path.isdir(project_path):
            try:
                shutil.rmtree( project_path, onerror = on_rm_error )
            except PermissionError as err:
                self.report({'WARNING'}, str(err))
        return {"FINISHED"}


class Nagato_OT_ConsolidateMaps(Operator):
    #TODO update and fix consolidate maps
    bl_label = 'Consolidate'
    bl_idname = 'nagato.consolidate'
    bl_description = 'consolidate all external images to maps folder'

    def invoke(self, context, event):
         return context.window_manager.invoke_confirm(self, event)

    @classmethod
    def poll(cls, context):
        return bool(NagatoProfile.user) and bpy.data.is_saved == True

    def execute(self, context):
        try:
            bpy.ops.file.make_paths_relative()
            images = bpy.data.images
            file_formats = {
                'png': 'png', 'jpeg': 'jpg', 
                'tga': 'tga', 'bmp': 'bmp', 
                'tiff': 'tif', 'iris':'rgb', 
                'openexr':'exr', 'hdr':'hdr', 
                'dpx':'dpx', 'cineon':'cin', 
                'jpeg2000':'jp2', 'targa':'tga',
            }

            for image in images:
                if image.name not in {'Viewer Node', 'Render Result'}:
                    if image.name_full.split('_', 1)[0].lower() in {'ref', 'blueprint'}:
                        print(image.name_full + ' this is a refermce/blueprint file')
                    elif image.name_full.rsplit('.', 1)[-1].lower() in {'jpg', 'jpeg', 'png', 'bmp', 'sgi', 'rgb', 'bw', 'jp2',
                                                                        'j2c', 'tga', 'cin', 'dpx', 'exr', 'hdr', 'tif', 'tiff'}:
                        image.pack()
                        image.packed_files[image.filepath].filepath = f'//maps/{image.name_full}'
                        image.unpack(method='USE_ORIGINAL')
                    else:
                        image.pack()
                        image.packed_files[image.filepath].filepath = f'//maps/{image.name_full}.{file_formats[image.file_format.lower()]}'
                        image.unpack(method='USE_ORIGINAL')
        except KeyError as e:
            self.report({'WARNING'}, str(e))
        except RuntimeError as r:
            self.report({'WARNING'}, str(r))
        else:
            try:
                #add consolidated files to svn
                statuses = svn_client.status(bpy.path.abspath('//') + 'maps')
                for status in statuses:
                    if str(status.text_status) == 'unversioned':
                        r = str(status)[13:-1].replace('\\\\', '/')
                        svn_client.add(r[1:-1])
                        svn_client.checkin([r[1:-1]], f'commit consolidated maps')
                self.report({'INFO'}, "Maps Colsolidated")
            except ClientError as error:
                self.report({'WARNING'}, str(error))
                self.report({'INFO'}, "Maps Colsolidated but not under version control")
        return{'FINISHED'}


class Nagato_OT_SvnUrl(Operator):
    bl_label = 'set svn url'
    bl_idname = 'nagato.svn_url'
    bl_description = 'set svn url'
    
    url: StringProperty(
        name = 'SVN Url',
        default = '',
        description = 'input svn url for project'
        )


    @classmethod
    def poll(cls, context):
        return bool(NagatoProfile.user) and bool(NagatoProfile.active_project) and NagatoProfile.user['role'] == 'admin'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        project = gazu.project.get_project_by_name(NagatoProfile.active_project['name'])
        project_id = project['id']
        gazu.project.update_project_data(project_id, {'svn_url': self.url})
        bpy.ops.nagato.refresh()
        return{'FINISHED'}

classes = [
    OBJECT_OT_NagatoAdd,
    # OBJECT_OT_NagatoPublish,
    OBJECT_OT_NagatoPublishSelected,
    # OBJECT_OT_NagatoUpdate,
    OBJECT_OT_NagatoUpdateSelected,
    NAGATO_OT_UpdateToRevision,
    Nagato_OT_UpdateAll,
    # Nagato_OT_Revert,
    Nagato_OT_RevertSelected,
    Nagato_OT_Resolve,
    Nagato_OT_CleanUp,
    Nagato_OT_CheckOut,
    Nagato_OT_DeleteProject,
    Nagato_OT_ConsolidateMaps,
    Nagato_OT_SvnUrl,
    NAGATO_OT_RevisionLog,
]
        
        
###################### registration######################
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.handlers.save_post.append(update_current_file_data)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)