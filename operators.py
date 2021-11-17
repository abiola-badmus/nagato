import bpy
import os
import json
from . import gazu
from .profile import NagatoProfile
from .gazu.exception import NotAuthenticatedException
from bpy.types import Operator
from .sequencer.operators import get_output_file_path

#TODO dynamically input frame rate
def ffmpeg_mp4():
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    is_ntsc = (bpy.context.scene.render.fps != 25)

    bpy.context.scene.render.ffmpeg.format = "MPEG4"
    bpy.context.scene.render.ffmpeg.codec = "H264"

    if is_ntsc:
        bpy.context.scene.render.ffmpeg.gopsize = 18
    else:
        bpy.context.scene.render.ffmpeg.gopsize = 15
    bpy.context.scene.render.ffmpeg.use_max_b_frames = False

    bpy.context.scene.render.ffmpeg.video_bitrate = 6000
    bpy.context.scene.render.ffmpeg.maxrate = 9000
    bpy.context.scene.render.ffmpeg.minrate = 0
    bpy.context.scene.render.ffmpeg.buffersize = 224 * 8
    bpy.context.scene.render.ffmpeg.packetsize = 2048
    bpy.context.scene.render.ffmpeg.muxrate = 10080000


def HDTV_1080p(frame_rate):
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.resolution_percentage = 100
    bpy.context.scene.render.pixel_aspect_x = 1
    bpy.context.scene.render.pixel_aspect_y = 1
    bpy.context.scene.render.fps = frame_rate
    bpy.context.scene.render.fps_base = 1


def anim_preset(filepath, frame_rate):
    ffmpeg_mp4()
    HDTV_1080p(frame_rate)
    bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
    bpy.context.scene.render.filepath = filepath


def layout_preset(filepath, frame_rate):
    ffmpeg_mp4()
    HDTV_1080p(frame_rate)
    bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
    bpy.context.scene.render.filepath = filepath


def lighting_preset(filepath, frame_rate):
    # bpy.context.scene.render.image_settings.file_format = 'PNG'
    ffmpeg_mp4()
    HDTV_1080p(frame_rate)
    bpy.context.scene.render.resolution_percentage = 30
    bpy.context.scene.frame_step = 10

    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 200

    bpy.context.scene.render.filepath = filepath

############## Operators #######################################
class NAGATO_OT_Refresh(Operator):
    bl_label = 'Nagato Refresh'
    bl_idname = 'nagato.refresh'
    bl_description = 'refresh kitsu data'    

    # @classmethod
    # def poll(cls, context):
    #     return NagatoProfile.user != None 

    def execute(self, context):
        scene = context.scene
        scene.tasks.clear()
        try:
            NagatoProfile.refresh_tasks()
            self.report({'INFO'}, 'Refreshed')
        except NotAuthenticatedException:
            self.report({'INFO'}, 'Not Logged in') 
        context.preferences.addons['nagato'].preferences.reset_messages()
        # bpy.context.scene.update_tag()
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
        working_mountpoint = context.preferences.addons['nagato'].preferences.working_mountpoint
        working_root = context.preferences.addons['nagato'].preferences.working_root
        working_asset_path = context.preferences.addons['nagato'].preferences.working_asset_path
        working_shot_path = context.preferences.addons['nagato'].preferences.working_shot_path
        working_sequence_path = context.preferences.addons['nagato'].preferences.working_sequence_path
        working_scenes_path = context.preferences.addons['nagato'].preferences.working_scenes_path
        working_asset_name = context.preferences.addons['nagato'].preferences.working_asset_name
        working_shot_name = context.preferences.addons['nagato'].preferences.working_shot_name
        working_sequence_name = context.preferences.addons['nagato'].preferences.working_sequence_name
        working_scenes_name = context.preferences.addons['nagato'].preferences.working_scenes_name

        output_mountpoint = context.preferences.addons['nagato'].preferences.output_mountpoint
        output_root = context.preferences.addons['nagato'].preferences.output_root
        output_asset_path = context.preferences.addons['nagato'].preferences.output_asset_path
        output_shot_path = context.preferences.addons['nagato'].preferences.output_shot_path
        output_sequence_path = context.preferences.addons['nagato'].preferences.output_sequence_path
        output_scenes_path = context.preferences.addons['nagato'].preferences.output_scenes_path
        output_asset_name = context.preferences.addons['nagato'].preferences.output_asset_name
        output_shot_name = context.preferences.addons['nagato'].preferences.output_shot_name
        output_sequence_name = context.preferences.addons['nagato'].preferences.output_sequence_name
        output_scenes_name = context.preferences.addons['nagato'].preferences.output_scenes_name

        file_tree_dir = os.path.join(os.path.dirname(__file__), 'file_tree.json')
        with open(file_tree_dir, 'r') as data:
            file_tree = json.load(data)
        #WORKING MOUNT_POINT
        file_tree['working']['mountpoint'] = working_mountpoint
        #WORKING ROOT
        file_tree['working']['root'] = working_root
        #WORKING FOLDER PATHS
        file_tree['working']['folder_path']['shot'] = working_shot_path
        file_tree['working']['folder_path']['asset'] = working_asset_path
        file_tree['working']['folder_path']['sequence'] = working_sequence_path
        file_tree['working']['folder_path']['scene'] = working_scenes_path
        #WORKING FILE_NAMES
        file_tree['working']['file_name']['shot'] = working_shot_name
        file_tree['working']['file_name']['asset'] = working_asset_name
        file_tree['working']['file_name']['sequence'] = working_sequence_name
        file_tree['working']['file_name']['scene'] = working_scenes_name

        #OUTPUT MOUNT_POINT
        file_tree['output']['mountpoint'] = output_mountpoint
        #OUTPUT ROOT
        file_tree['output']['root'] = output_root
        #OUTPUT FOLDER PATHS
        file_tree['output']['folder_path']['shot'] = output_shot_path
        file_tree['output']['folder_path']['asset'] = output_asset_path
        file_tree['output']['folder_path']['sequence'] = output_sequence_path
        file_tree['output']['folder_path']['scene'] = output_scenes_path
        #OUTPUT FILE_NAMES
        file_tree['output']['file_name']['shot'] = output_shot_name
        file_tree['output']['file_name']['asset'] = output_asset_name
        file_tree['output']['file_name']['sequence'] = output_sequence_name
        file_tree['output']['file_name']['scene'] = output_scenes_name

        project = gazu.project.get_project_by_name(NagatoProfile.active_project['name'])
        project_id = project['id']
        gazu.files.update_project_file_tree(project_id, file_tree)
        self.report({'INFO'}, 'file tree applied')
        return{'FINISHED'}

#TODO handle error when getting depenency
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


class NAGATO_OT_Render(Operator):
    bl_label = 'render'
    bl_idname = 'nagato.render'
    bl_description = 'render'


    @classmethod
    def poll(cls, context):
        return NagatoProfile.lastest_openfile['file_path'] == bpy.context.blend_data.filepath
        # return bool(NagatoProfile.user) and bool(NagatoProfile.active_project) and NagatoProfile.user['role'] == 'admin'

    def execute(self, context):
        entity_id = NagatoProfile.lastest_openfile['entity_id']
        task_type = NagatoProfile.lastest_openfile['task_type']

        frame_rate = bpy.context.scene.render.fps
        if task_type.lower() in {'layout'}:
            previz_path = get_output_file_path('previz', task_type, entity_id)
            os.makedirs(os.path.dirname(previz_path), exist_ok=True)
            layout_preset(previz_path, frame_rate)
            bpy.ops.render.render('INVOKE_DEFAULT', use_viewport=True, animation=True)
        elif task_type.lower() in {"animation", "anim"}:
            play_blast_path = get_output_file_path('play_blast', task_type, entity_id)
            os.makedirs(os.path.dirname(play_blast_path), exist_ok=True)
            anim_preset(play_blast_path, frame_rate)
            bpy.ops.render.render('INVOKE_DEFAULT', use_viewport=True, animation=True)
        elif task_type.lower() in {"lighting"}:
            look_dev_path = get_output_file_path('look_dev', task_type, entity_id)
            os.makedirs(os.path.dirname(look_dev_path), exist_ok=True)
            lighting_preset(look_dev_path, frame_rate)
            bpy.ops.render.render('INVOKE_DEFAULT', use_viewport=True, animation=True)
        return{'FINISHED'}
############### all classes ####################    
classes = [
        NAGATO_OT_Refresh,
        NAGATO_OT_GetDependencies,
        NAGATO_OT_GetRefImg,
        OBJECT_OT_NagatoSetFileTree,
        NAGATO_OT_Setting,
        NAGATO_OT_Render,
        ]  
    
    
# registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)   
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)  