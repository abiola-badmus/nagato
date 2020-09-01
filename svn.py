import bpy
import os
from bpy.types import (
    Operator,
    Panel,
    AddonPreferences,
    PropertyGroup,
    Menu
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
# def remote():
#         if kitsu.remote_host[0] == True:
#             return True
#         else:
#             return False

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
        return kitsu.current_user[0] != 'NOT LOGGED IN' and bpy.data.is_saved == True


    def execute(self, context):
        bpy.ops.wm.save_mainfile()
        user = kitsu.current_user[0]
        
        try:
            client.checkin([f'{bpy.context.blend_data.filepath}'], f'{user} : {self.comment}')
            statuses = client.status(bpy.path.abspath('//') + 'maps')
            for status in statuses:
                print(str(status.text_status)) 
                if str(status.text_status) in {'modified', 'added'}:
                    map_dir = str(status)[13:-1].replace('\\\\', '/')
                    client.checkin([map_dir[1:-1]], self.comment)
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
        except pysvn._pysvn_3_7.ClientError as e:
            self.report({'WARNING'}, str(e))
        # except pysvn._pysvn_3_7.ClientError:
        #     self.report({'WARNING'}, "None of the targets are working copies")
        return{'FINISHED'}


class OBJECT_OT_NagatoUpdateAll(Operator):
    bl_label = 'Update all files'
    bl_idname = 'nagato.update_all'
    bl_description = 'Update all files in project repository'
    
    @classmethod
    def poll(cls, context):
        return kitsu.current_user[0] != 'NOT LOGGED IN' and len(kitsu.current_project) != 0

    def execute(self, context):
        user = os.environ.get('homepath')
        user_f = user.replace("\\","/")
        mount_point = 'C:' + user_f + '/projects/'
        project = mount_point + kitsu.current_project[0]
        try:
            for file in os.listdir(project):
                try:
                    client.update(os.path.join(project, file))
                    bpy.ops.wm.revert_mainfile()
                    self.report({'INFO'}, "Update Successful")
                except pysvn._pysvn_3_7.ClientError as error:
                    self.report({'INFO'}, str(error))
        except FileNotFoundError:
            self.report({'WARNING'}, 'project files do not exist')
        return{'FINISHED'}


class OBJECT_OT_NagatoRevert(Operator):
    bl_label = 'reset file'
    bl_idname = 'nagato.revert'
    bl_description = 'revert to last checkpoint'
    
    @classmethod
    def poll(cls, context):
        return kitsu.current_user[0] != 'NOT LOGGED IN' and bpy.data.is_saved == True


    def execute(self, context):
        try:
            client.revert(f'{bpy.context.blend_data.filepath}')
            bpy.ops.wm.revert_mainfile()
            self.report({'INFO'}, "reverted")
        except pysvn._pysvn_3_7.ClientError as e:
            self.report({'WARNING'}, str(e))
        return{'FINISHED'}


class OBJECT_OT_NagatoResolve(Operator):
    bl_label = 'resolve conflict'
    bl_idname = 'nagato.resolve'
    bl_description = 'resolve file conflict'
    
    @classmethod
    def poll(cls, context):
        return kitsu.current_user[0] != 'NOT LOGGED IN' and bpy.data.is_saved == True


    def execute(self, context):
        try:
            client.resolved(f'{bpy.context.blend_data.filepath}')
            self.report({'INFO'}, "conflict resolved")
        except pysvn._pysvn_3_7.ClientError as e:
            self.report({'WARNING'}, str(e))
        return{'FINISHED'}


class OBJECT_OT_NagatoCleanUp(Operator):
    bl_label = 'clean up'
    bl_idname = 'nagato.clean_up'
    bl_description = 'clean up files'
    
    @classmethod
    def poll(cls, context):
        return kitsu.current_user[0] != 'NOT LOGGED IN' and bpy.data.is_saved == True


    def execute(self, context):
        mount_point = context.preferences.addons['nagato'].preferences.project_mount_point
        file_root = bpy.context.blend_data.filepath.rsplit('/', 1)
        path = file_root[0].split(mount_point, 1)[1].split('/', 3)
        root = os.path.join(mount_point, path[1], path[2])
        print(root)
        try:
            client.cleanup(root)
            self.report({'INFO'}, "clean up succesful")
        except pysvn._pysvn_3_7.ClientError as e:
            self.report({'WARNING'}, str(e))
        return{'FINISHED'}


class OBJECT_OT_NagatoCheckOut(Operator):
    bl_label = 'Download files'
    bl_idname = 'nagato.check_out'
    bl_description = 'checkout project files'
    
    
    remote_bool = bpy.props.BoolProperty(
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
        return kitsu.current_user[0] != 'NOT LOGGED IN' and len(kitsu.current_project) != 0

    def execute(self, context):
        # if len(kitsu.current_project) != 0:
        project_info = gazu.project.get_project_by_name(kitsu.current_project[0])
        try:
            if self.remote_bool is False:
                repo_url = project_info['data']['local_svn_url']
            else:
                repo_url = project_info['data']['remote_svn_url']
            print(f'this {repo_url}')
            print(f'this {project_info}')
            user = os.environ.get('homepath')
            user_f = user.replace("\\","/")
            root = context.preferences.addons['nagato'].preferences.root
            mount_point = os.path.join('C:', user_f, root)
            file_path = os.path.join(mount_point, kitsu.current_project[0])
            print(file_path)  
            client.set_default_username(self.username)
            client.set_default_password(self.password)
            if os.path.isdir(mount_point) == False:
                os.mkdir(mount_point)
            if os.path.isdir(file_path) == False:
                os.mkdir(file_path)
                try:
                    if client.is_url(repo_url) in [1, True]:
                        client.checkout(repo_url, file_path)
                        self.report({'INFO'}, "project files downloaded")
                    else:
                        self.report({'INFO'}, "SVN url invalid")
                except pysvn._pysvn_3_7.ClientError as e:
                    self.report({'WARNING'}, str(e))
            elif len(os.listdir(file_path)) == 0:
                try:
                    if client.is_url(repo_url) in [1, True]:
                        client.checkout(repo_url, file_path)
                        self.report({'INFO'}, "project files downloaded")
                    else:
                        self.report({'WARNING'}, "SVN url invalid")
                except pysvn._pysvn_3_7.ClientError as e:
                    self.report({'WARNING'}, str(e))
            elif os.path.isdir(file_path + '/.svn') == True:
                bpy.ops.nagato.update_all()
                self.report({'INFO'}, "project file updated")
            else:
                self.report({'WARNING'}, "Directory is not empty and not under version control")
            return{'FINISHED'}
        except TypeError:
            self.report({'WARNING'}, "svn url not set")
            return{'FINISHED'}


class OBJECT_OT_ConsolidateMaps(Operator):
    bl_label = 'Consolidate'
    bl_idname = 'nagato.consolidate'
    bl_description = 'consolidate all external images to maps folder'

    def invoke(self, context, event):
         return context.window_manager.invoke_confirm(self, event)

    @classmethod
    def poll(cls, context):
        return kitsu.current_user[0] != 'NOT LOGGED IN' and bpy.data.is_saved == True

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
                        print(status.text_status) 
                        r = str(status)[13:-1].replace('\\\\', '/')
                        print(r[1:-1])
                        client.add(r[1:-1])
                        client.checkin([r[1:-1]], f'commit consolidated maps')
                self.report({'INFO'}, "Maps Colsolidated")
            except pysvn._pysvn_3_7.ClientError as error:
                self.report({'WARNING'}, str(error))
                self.report({'INFO'}, "Maps Colsolidated but not under version control")
        return{'FINISHED'}


class OBJECT_OT_NagatoSvnUrl(Operator):
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
        return kitsu.current_user[0] != 'NOT LOGGED IN' and len(kitsu.current_project) != 0 and kitsu.current_user[1] == 'admin'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        project = gazu.project.get_project_by_name(kitsu.current_project[0])
        project_id = project['id']
        print(project_id)
        print(kitsu.current_user[1])
        gazu.project.update_project_data(project_id, {'local_svn_url': self.local_url})
        gazu.project.update_project_data(project_id, {'remote_svn_url': self.remote_url})
        return{'FINISHED'}


##########################MENU############################
class NAGATO_MT_ProjectFiles(Menu):
    bl_label = 'project files operators'
    bl_idname = "nagato.project_files"
    
    def draw(self, context):
        layout = self.layout
        layout.operator('nagato.add', icon = 'ADD')
        layout.separator()
        layout.operator('nagato.update_all', text= 'update all files')
        layout.operator('nagato.check_out', text= 'download project files')
        layout.separator()
        layout.operator('nagato.consolidate', text= 'consolidate maps', icon = 'FULLSCREEN_EXIT')
        layout.operator('nagato.get_ref', text= 'get refernce images')
        layout.separator()
        layout.operator('nagato.revert', icon='LOOP_BACK')
        layout.operator('nagato.resolve', icon = 'OUTLINER_DATA_GREASEPENCIL')
        layout.operator('nagato.clean_up', icon = 'BRUSH_DATA')



classes = [
    OBJECT_OT_NagatoAdd,
    OBJECT_OT_NagatoPublish,
    OBJECT_OT_NagatoUpdate,
    OBJECT_OT_NagatoUpdateAll,
    OBJECT_OT_NagatoRevert,
    OBJECT_OT_NagatoResolve,
    OBJECT_OT_NagatoCleanUp,
    OBJECT_OT_NagatoCheckOut,
    OBJECT_OT_ConsolidateMaps,
    NAGATO_MT_ProjectFiles,
    OBJECT_OT_NagatoSvnUrl
]
        
        
###################### registration######################
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
