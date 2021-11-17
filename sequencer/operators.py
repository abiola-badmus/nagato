import bpy
from .. import gazu, profile
from bpy.types import (Operator, Menu)
from bpy.props import (StringProperty, BoolProperty, EnumProperty)
from bpy.app.handlers import persistent
import os
import shutil
NagatoProfile = profile.NagatoProfile

def get_output_file_path(out_put_type_name, task_type_name, entity_id):
    out_put_type = gazu.files.get_output_type_by_name(out_put_type_name)
    if out_put_type:
        task_type = gazu.task.get_task_type_by_name(task_type_name)
        out_put_type_path = os.path.expanduser(f"{gazu.files.build_entity_output_file_path(entity=entity_id,output_type=out_put_type,task_type=task_type)}.mp4")
    else:
        out_put_type = gazu.files.new_output_type(out_put_type_name, out_put_type_name)
        task_type = gazu.task.get_task_type_by_name(task_type_name)
        out_put_type_path = os.path.expanduser(f"{gazu.files.build_entity_output_file_path(entity=entity_id,output_type=out_put_type,task_type=task_type)}.mp4")
    return out_put_type_path

class NAGATO_OT_Submit_shot_to_kitsu(Operator):
    #TODO create new shot in kitsu
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


class Nagato_OT_Pull_Shots(Operator):
    """
    Operator that Pulls all shot from the server
    """
    bl_idname = "nagato.pull_shots"
    bl_label = "Pull shot"
    bl_description = "Pull shot"

    def execute(self, context):
        default_frame_in = 1
        gazu.cache.clear_all()
        active_strip = []
        strips = bpy.context.scene.sequence_editor.sequences_all
        for strip in strips:
            try:
                if strip.kitsu.linked:
                    shot_id = strip.kitsu.shot_id
                    active_strip.append(shot_id)
            except AttributeError:
                pass
        shots = gazu.shot.all_shots_for_project(NagatoProfile.active_project['id'])
        for shot in shots:
            if shot['id'] not in active_strip:
                shot = gazu.shot.get_shot(shot['id'])
                sequence = gazu.shot.get_sequence(shot['parent_id'])
                strip_name = f"{sequence['name']}_{shot['name']}"
                if shot['frame_in'] != None and shot['frame_in'] != '':
                    frame_in = int(shot['frame_in'])
                else:
                    frame_in = default_frame_in
                    default_frame_in += 120
                if shot['frame_out'] != None and shot['frame_out'] != '':
                    frame_out = int(shot['frame_out'])
                else:
                    frame_out = frame_in + 120
                place_holder_path = os.path.join(os.path.dirname(__file__), '..', 'video_place_holder.mp4')
                look_dev_path = get_output_file_path('look_dev', 'Lighting', shot['id'])
                play_blast_path = get_output_file_path('play_blast', 'Animation', shot['id'])
                previz_path = get_output_file_path('previz', 'Layout', shot['id'])

                if not os.path.isfile(look_dev_path):
                    os.makedirs(os.path.dirname(look_dev_path), exist_ok=True)
                    shutil.copyfile(place_holder_path, look_dev_path)
                if not os.path.isfile(play_blast_path):
                    os.makedirs(os.path.dirname(play_blast_path), exist_ok=True)
                    shutil.copyfile(place_holder_path, play_blast_path)
                if not os.path.isfile(previz_path):
                    os.makedirs(os.path.dirname(previz_path), exist_ok=True)
                    shutil.copyfile(place_holder_path, previz_path)

                strip = context.scene.sequence_editor.sequences.new_movie(
                            strip_name,
                            look_dev_path,
                            1,
                            frame_in,
                        )
                # strip = context.scene.sequence_editor.sequences.new_movie(
                #             strip_name,
                #             previz,
                #             1,
                #             frame_in,
                #         )
                strip.frame_final_end = frame_out
                strip.kitsu.shot_id = shot['id']
                strip.kitsu.shot_name = shot['name']
                strip.kitsu.sequence_id = sequence['id']
                strip.kitsu.sequence_name = sequence['name']
                strip.kitsu.project_id = NagatoProfile.active_project['id']
                strip.kitsu.project_name = NagatoProfile.active_project['name']
                strip.kitsu.linked = True
        return {"FINISHED"}


class Nagato_OT_Push_Shots(Operator):
    """
    Operator that Pulls all shot from the server
    """
    bl_idname = "nagato.push_shots"
    bl_label = "Push shot"
    bl_description = "Pull shot"

    def execute(self, context):
        default_frame_in = 0
        strips = bpy.context.scene.sequence_editor.sequences_all
        for strip in strips:
            if strip.kitsu.linked:
                shot_id = strip.kitsu.shot_id
                shot_name = strip.kitsu.shot_name
                sequence_id =  strip.kitsu.sequence_id
                sequence_name = strip.kitsu.sequence_name
                project_id = strip.kitsu.project_id
                project_name = strip.kitsu.project_name
                frame_final_duration = strip.frame_final_duration
                frame_in = strip.frame_final_start
                frame_out = strip.frame_final_end - 1
                nb_frame = strip.frame_final_duration
                shot = gazu.shot.get_shot(shot_id)
                shot['data']['fps'] = 24
                shot['data']['frame_in'] = frame_in
                shot['data']['frame_out'] = frame_out
                shot['nb_frames'] = nb_frame
                gazu.shot.update_shot(shot)
                gazu.cache.clear_all()
        return {"FINISHED"}


class Nagato_OT_Update_Strip_Media(Operator):
    """
    Operator that Pulls all shot from the server
    """
    bl_idname = "nagato.update_strip_media"
    bl_label = "Update Strip Media"
    bl_description = "Update_Strip_Media"

    def execute(self, context):
        #TODO Update_Strip_Media
        strips = bpy.context.scene.sequence_editor.sequences_all
        for strip in strips:
            try:
                if strip.kitsu.linked:
                    shot_id = strip.kitsu.shot_id
                    if context.scene.render_type == 'look_dev':
                        look_dev_path = get_output_file_path('look_dev', 'Lighting', shot_id)
                        strip.filepath = look_dev_path
                    elif context.scene.render_type == 'play_blast':
                        play_blast_path = get_output_file_path('play_blast', 'Animation', shot_id)
                        strip.filepath = play_blast_path
                    elif context.scene.render_type == 'previz':
                        previz_path = get_output_file_path('previz', 'Layout', shot_id)
                        strip.filepath = previz_path
            except AttributeError:
                print('strip not linked to kitsu')
        return {"FINISHED"}
        


classes = [
    NAGATO_OT_Submit_shot_to_kitsu,
    Nagato_OT_Pull_Shots,
    Nagato_OT_Push_Shots,
    Nagato_OT_Update_Strip_Media
]
    
    
# registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls) 