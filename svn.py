import bpy
import os
from bpy.types import (
    Operator,
    Panel,
    AddonPreferences,
    PropertyGroup,
    Menu
)
from bpy.props import (StringProperty, IntProperty, EnumProperty)
from . import pysvn
from . import gazu
from . import nagato_icon
from nagato.kitsu import NagatoProfile, load_config, task_file_directory, update_list, update_ui_list
from configparser import ConfigParser, NoOptionError
import nagato.kitsu

########## operators ################################
client = pysvn.Client()
svn_logged_in = True
revisions_list = list()

class OBJECT_OT_NagatoAdd(Operator):
    bl_label = 'Add file to SVN'
    bl_idname = 'nagato.add'
    bl_description = 'Add current file to project repository'
    
    @classmethod
    def poll(cls, context):
        return bool(NagatoProfile.user)


    def execute(self, context):  
        try:
            status = client.status(f'{bpy.context.blend_data.filepath}')[0]
            if str(status.text_status) == 'unversioned':
                r = str(status)[13:-1].replace('\\\\', '/')
                client.add(r[1:-1])
                self.report({'INFO'}, "File Added to Repository")
            else:
                self.report({'WARNING'}, "All files under version control")
        except pysvn._pysvn.ClientError:
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
            client.ls(client.info(directory).url)
        except pysvn._pysvn.ClientError as e:
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
                client.set_default_username(self.username)
                client.set_default_password(self.password)
            if self.comment == '':
                self.report({'WARNING'}, 'Publish failed, no comment added')
                return{'FINISHED'}
            if NagatoProfile.lastest_openfile['file_path'] == bpy.context.blend_data.filepath:
                bpy.ops.wm.save_mainfile()
            client.checkin(directory, f'{self.comment}')
            statuses = client.status(os.path.dirname(directory) + 'maps')
            for status in statuses:
                if str(status.text_status) in {'modified', 'added'}:
                    map_dir = str(status)[13:-1].replace('\\\\', '/')
                    client.checkin([map_dir[1:-1]], self.comment)
            svn_logged_in = True
            update_ui_list(
                            displayed_tasks=nagato.kitsu.displayed_tasks,
                            tasks=NagatoProfile.tasks,
                            active_project=NagatoProfile.active_project['name'],
                            active_task_type=NagatoProfile.active_task_type
                            )
            self.report({'INFO'}, "Publish successful")
        except pysvn._pysvn.ClientError as e:
            if str(e) == 'callback_get_login required':
                svn_logged_in = False
            update_ui_list(
                            displayed_tasks=nagato.kitsu.displayed_tasks,
                            tasks=NagatoProfile.tasks,
                            active_project=NagatoProfile.active_project['name'],
                            active_task_type=NagatoProfile.active_task_type
                            )
            self.report({'WARNING'}, str(e))
        bpy.context.scene.update_tag()
        bpy.app.handlers.depsgraph_update_pre.append(update_list)

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
            client.update(directory)
            client.update(os.path.dirname(directory) + 'maps')
            # bpy.ops.wm.revert_mainfile()
            if NagatoProfile.lastest_openfile['file_path'] == bpy.context.blend_data.filepath:
                bpy.ops.wm.revert_mainfile()
            update_ui_list(
                            displayed_tasks=nagato.kitsu.displayed_tasks,
                            tasks=NagatoProfile.tasks,
                            active_project=NagatoProfile.active_project['name'],
                            active_task_type=NagatoProfile.active_task_type
                            )
            self.report({'INFO'}, "Update Successful")
            return{'FINISHED'}
        except pysvn._pysvn.ClientError as e:
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
            client.set_default_username(self.username)
            client.set_default_password(self.password)

            client.update(directory)
            client.update(os.path.dirname(directory) + 'maps')
            if NagatoProfile.lastest_openfile['file_path'] == bpy.context.blend_data.filepath:
                bpy.ops.wm.revert_mainfile()
            update_ui_list(
                            displayed_tasks=nagato.kitsu.displayed_tasks,
                            tasks=NagatoProfile.tasks,
                            active_project=NagatoProfile.active_project['name'],
                            active_task_type=NagatoProfile.active_task_type
                            )
            self.report({'INFO'}, "Update Successful")
        except pysvn._pysvn.ClientError as err:
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
            # logs = client.log(directory)
            # logs.reverse()
            revision = revisions_list[context.scene.revisions_idx]
            roll_back_file= client.cat(directory, revision)
            with open(directory, 'w+b') as f:
                f.write(roll_back_file)
            if NagatoProfile.lastest_openfile['file_path'] == bpy.context.blend_data.filepath:
                bpy.ops.wm.revert_mainfile()
            update_ui_list(
                            displayed_tasks=nagato.kitsu.displayed_tasks,
                            tasks=NagatoProfile.tasks,
                            active_project=NagatoProfile.active_project['name'],
                            active_task_type=NagatoProfile.active_task_type
                            )
            self.report({'INFO'}, "revert to revision Successful")
            return{'FINISHED'}
        except pysvn._pysvn.ClientError as e:
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
            client.ls(client.info(directory).url)
        except pysvn._pysvn.ClientError as e:
            if str(e) == 'callback_get_login required':
                svn_logged_in = False
                return context.window_manager.invoke_props_dialog(self)

        logs = client.log(directory)
        logs.reverse()
        formatted_log  = list()
        revisions_list.clear()
        for i, log in enumerate(logs, 0):
            from datetime import datetime
            date = datetime.fromtimestamp(log.date).strftime('%Y-%m-%d')
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
            row.template_list("Revision_UL_list", "", context.scene, "revisions", context.scene, "revisions_idx", rows=6)

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
                client.set_default_username(self.username)
                client.set_default_password(self.password)
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
        project_folder = os.path.expanduser(os.path.join(mount_point, root, NagatoProfile.active_project['name'].replace(' ','_').lower()))
        try:
            for file in os.listdir(project_folder):
                try:
                    client.update(os.path.join(project_folder, file))
                except pysvn._pysvn.ClientError as error:
                    if str(error) == 'callback_get_login required':
                        return context.window_manager.invoke_props_dialog(self)
                    self.report({'WARNING'}, str(error))
            if bpy.data.is_saved:
                bpy.ops.wm.revert_mainfile()
            update_ui_list(
                displayed_tasks=nagato.kitsu.displayed_tasks,
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
        return bool(NagatoProfile.user) and bool(NagatoProfile.active_project)

    def execute(self, context):
        client.set_default_username(self.username)
        client.set_default_password(self.password)

        mount_point = NagatoProfile.active_project['file_tree']['working']['mountpoint']
        root = NagatoProfile.active_project['file_tree']['working']['root']
        project_folder = os.path.expanduser(os.path.join(mount_point, root, NagatoProfile.active_project['name']))
        try:
            for file in os.listdir(project_folder):
                try:
                    client.update(os.path.join(project_folder, file))
                    if bpy.data.is_saved:
                        bpy.ops.wm.revert_mainfile()
                    update_ui_list(
                        displayed_tasks=nagato.kitsu.displayed_tasks,
                        tasks=NagatoProfile.tasks,
                        active_project=NagatoProfile.active_project['name'],
                        active_task_type=NagatoProfile.active_task_type
                        )
                    self.report({'INFO'}, "Update Successful")
                except pysvn._pysvn.ClientError as error:
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
            client.revert(directory)
            if NagatoProfile.lastest_openfile['file_path'] == bpy.context.blend_data.filepath:
                bpy.ops.wm.revert_mainfile()
            update_ui_list(
                            displayed_tasks=nagato.kitsu.displayed_tasks,
                            tasks=NagatoProfile.tasks,
                            active_project=NagatoProfile.active_project['name'],
                            active_task_type=NagatoProfile.active_task_type
                            )
            self.report({'INFO'}, "reverted")
        except pysvn._pysvn.ClientError as e:
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
            pass
        else:
            layout = self.layout
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
            client.ls(client.info(directory).url)
        except pysvn._pysvn.ClientError as e:
            if str(e) == 'callback_get_login required':
                svn_logged_in = False
                return context.window_manager.invoke_props_dialog(self)
        return self.execute(context)

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
                client.set_default_username(self.username)
                client.set_default_password(self.password)

            client.resolved(directory)
            svn_logged_in = True
            update_ui_list(
                            displayed_tasks=nagato.kitsu.displayed_tasks,
                            tasks=NagatoProfile.tasks,
                            active_project=NagatoProfile.active_project['name'],
                            active_task_type=NagatoProfile.active_task_type
                            )
            self.report({'INFO'}, "conflict resolved")
        except pysvn._pysvn.ClientError as e:
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
        mount_point = os.path.expanduser(context.preferences.addons['nagato'].preferences.mountpoint)
        file_root = bpy.context.blend_data.filepath.rsplit('/', 1)
        path = file_root[0].split(mount_point, 1)[1].split('/', 3)
        root = os.path.join(mount_point, path[1], path[2])
        try:
            client.cleanup(root)
            self.report({'INFO'}, "clean up succesful")
        except pysvn._pysvn.ClientError as e:
            self.report({'WARNING'}, str(e))
        return{'FINISHED'}


class Nagato_OT_CheckOut(Operator):
    bl_label = 'Download files'
    bl_idname = 'nagato.check_out'
    bl_description = 'checkout project files'
    
    
    remote_bool: bpy.props.BoolProperty(
        name = 'Remote',
        default = False,
        description = 'is host remote'
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

        
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    @classmethod
    def poll(cls, context):
        return bool(NagatoProfile.user) and NagatoProfile.active_project != None

    def execute(self, context):
        project_info = NagatoProfile.active_project
        try:
            if self.remote_bool is False:
                repo_url = project_info['data']['local_svn_url']
            else:
                repo_url = project_info['data']['remote_svn_url']
            root = project_info['file_tree']['working']['root']
            mount_point = project_info['file_tree']['working']['mountpoint']
            file_path = os.path.expanduser(os.path.join(mount_point, root, NagatoProfile.active_project['name'].replace(' ', '_').lower()))
            client.set_default_username(self.username)
            client.set_default_password(self.password)
            if os.path.isdir(file_path) == False:
                os.makedirs(file_path)
                try:
                    if client.is_url(repo_url):
                        client.checkout(repo_url, file_path)
                        self.report({'INFO'}, "project files downloaded")
                    else:
                        self.report({'INFO'}, "SVN url invalid")
                except pysvn._pysvn.ClientError as e:
                    os.removedirs(file_path)
                    self.report({'WARNING'}, str(e))
            elif len(os.listdir(file_path)) == 0:
                try:
                    if client.is_url(repo_url):
                        client.checkout(repo_url, file_path)
                        self.report({'INFO'}, "project files downloaded")
                    else:
                        os.removedirs(file_path)
                        self.report({'WARNING'}, "SVN url invalid")
                except pysvn._pysvn.ClientError as e:
                    self.report({'WARNING'}, str(e))
            elif os.path.isdir(file_path + '/.svn') == True:
                bpy.ops.nagato.update_all()
                self.report({'INFO'}, "project file updated")
            else:
                self.report({'WARNING'}, "Directory is not empty and not under version control")
            return{'FINISHED'}
        except (TypeError, KeyError):
            self.report({'WARNING'}, "svn url not set")
            return{'FINISHED'}


class Nagato_OT_ConsolidateMaps(Operator):
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

            for image in images:
                if image.name != 'Viewer Node':
                    if image.name != 'Render Result':
                        if image.name_full.split('_', 1)[0].lower() in {'ref', 'blueprint'}:
                            print(image.name_full + ' this is a ref')
                        elif image.name_full.rsplit('.', 1)[-1].lower() in {'jpg', 'jpeg', 'png', 'bmp', 'sgi', 'rgb', 'bw', 'jp2',
                                                                            'j2c', 'tga', 'cin', 'dpx', 'exr', 'hdr', 'tif', 'tiff'}:
                            image.pack()
                            image.packed_files[image.filepath].filepath = f'//maps/{image.name_full}'
                            image.unpack(method='USE_ORIGINAL')
                        elif image.file_format.lower() == 'png':
                            image.pack()
                            image.packed_files[image.filepath].filepath = f'//maps/{image.name_full}.png'
                            image.unpack(method='USE_ORIGINAL')
                        elif image.file_format.lower() == 'jpeg':
                            image.pack()
                            image.packed_files[image.filepath].filepath = f'//maps/{image.name_full}.jpg'
                            image.unpack(method='USE_ORIGINAL')
                        elif image.file_format.lower() == 'bmp':
                            image.pack()
                            image.packed_files[image.filepath].filepath = f'//maps/{image.name_full}.bmp'
                            image.unpack(method='USE_ORIGINAL')
                        elif image.file_format.lower() == 'iris':
                            image.pack()
                            image.packed_files[image.filepath].filepath = f'//maps/{image.name_full}.rgb'
                            image.unpack(method='USE_ORIGINAL')
                        elif image.file_format.lower() == 'jpeg2000':
                            image.pack()
                            image.packed_files[image.filepath].filepath = f'//maps/{image.name_full}.jp2'
                            image.unpack(method='USE_ORIGINAL')
                        elif image.file_format.lower() == 'targa':
                            image.pack()
                            image.packed_files[image.filepath].filepath = f'//maps/{image.name_full}.tga'
                            image.unpack(method='USE_ORIGINAL')
                        elif image.file_format.lower() == 'open_exr':
                            image.pack()
                            image.packed_files[image.filepath].filepath = f'//maps/{image.name_full}.exr'
                            image.unpack(method='USE_ORIGINAL')
                        elif image.file_format.lower() == 'tiff':
                            image.pack()
                            image.packed_files[image.filepath].filepath = f'//maps/{image.name_full}.tif'
                            image.unpack(method='USE_ORIGINAL')
                        elif image.file_format.lower() == 'hdr':
                            image.pack()
                            image.packed_files[image.filepath].filepath = f'//maps/{image.name_full}.hdr'
                            image.unpack(method='USE_ORIGINAL')
                        elif image.file_format.lower() == 'cineon':
                            image.pack()
                            image.packed_files[image.filepath].filepath = f'//maps/{image.name_full}.cin'
                            image.unpack(method='USE_ORIGINAL')
                        elif image.file_format.lower() == 'dpx':
                            image.pack()
                            image.packed_files[image.filepath].filepath = f'//maps/{image.name_full}.dpx'
                            image.unpack(method='USE_ORIGINAL')
        except KeyError as e:
            self.report({'WARNING'}, str(e))
        except RuntimeError as r:
            self.report({'WARNING'}, str(r))
        else:
            try:
                #add consolidated files to svn
                statuses = client.status(bpy.path.abspath('//') + 'maps')
                for status in statuses:
                    if str(status.text_status) == 'unversioned':
                        r = str(status)[13:-1].replace('\\\\', '/')
                        client.add(r[1:-1])
                        client.checkin([r[1:-1]], f'commit consolidated maps')
                self.report({'INFO'}, "Maps Colsolidated")
            except pysvn._pysvn.ClientError as error:
                self.report({'WARNING'}, str(error))
                self.report({'INFO'}, "Maps Colsolidated but not under version control")
        return{'FINISHED'}


class Nagato_OT_SvnUrl(Operator):
    bl_label = 'set svn url'
    bl_idname = 'nagato.svn_url'
    bl_description = 'set svn url'
    
    local_url: StringProperty(
        name = 'Local Url',
        default = '',
        description = 'input svn local url for project'
        )

    remote_url: StringProperty(
        name = 'Remote Url',
        default = '',
        description = 'input svn remote url for project'
        )


    @classmethod
    def poll(cls, context):
        return bool(NagatoProfile.user) and bool(NagatoProfile.active_project) and NagatoProfile.user['role'] == 'admin'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        project = gazu.project.get_project_by_name(NagatoProfile.active_project['name'])
        project_id = project['id']
        gazu.project.update_project_data(project_id, {'local_svn_url': self.local_url})
        gazu.project.update_project_data(project_id, {'remote_svn_url': self.remote_url})
        return{'FINISHED'}


##########################MENU############################
class NAGATO_MT_ProjectFiles(Menu):
    bl_label = 'project files operators'
    bl_idname = "NAGATO_MT_ProjectFiles"
    
    def draw(self, context):
        layout = self.layout
        # layout.operator('nagato.add', icon = 'ADD')
        # layout.separator()
        # layout.operator('nagato.update_all', text= 'update all files')
        # layout.operator('nagato.check_out', text= 'download project files')
        # layout.separator()
        # layout.operator('nagato.consolidate', text= 'consolidate maps', icon = 'FULLSCREEN_EXIT')
        # TODO get reference images and send image to kitsu
        # FIX Consolidate maps
        # layout.operator('nagato.get_ref', text= 'get refernce images', icon='IMAGE_REFERENCE')
        layout.separator()
        # layout.operator('nagato.revision_log', icon='FILE_TEXT')
        layout.operator('nagato.revert_selected', icon='LOOP_BACK')
        # layout.operator('nagato.update_to_revision')
        layout.operator('nagato.resolve', icon_value = nagato_icon.icon('resolve_conflict'))
        layout.operator('nagato.clean_up', icon = 'BRUSH_DATA')



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
    Nagato_OT_ConsolidateMaps,
    NAGATO_MT_ProjectFiles,
    Nagato_OT_SvnUrl,
    NAGATO_OT_RevisionLog,
]
        
        
###################### registration######################
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
