import bpy
from bpy.types import AddonPreferences
from bpy.props import (StringProperty, EnumProperty, BoolProperty)
import os
from .. import profile

NagatoProfile = profile.NagatoProfile

class NagatoPreferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = 'nagato'
    user = os.environ.get('homepath')
    host_url: StringProperty(
        name="url of server",
        default='http://myAddress/api',
    )
    error_message: StringProperty(
        name='Error Message',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'}
    )
    ok_message: StringProperty(
        name='Message',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'}
    )
    
    #working file tree properties
    working_mountpoint: StringProperty(
        name="Mount Point",
        default='~',
    )
    working_root: StringProperty(
        name="Root",
        default='projects',
    )
      # folder paths
    working_asset_path: StringProperty(
        name="Asset Path",
        default='<Project>/lib/<AssetType>',
    )
    working_shot_path: StringProperty(
        name="Shot Path",
        default='<Project>/scenes/<Sequence>/<Shot>',
    )
    working_sequence_path: StringProperty(
        name="Sequence Path",
        default='<Project>/sequences/<Sequence>/<TaskType>',
    )
    working_scenes_path: StringProperty(
        name="Scenes Path",
        default='<Project>/scenes/<Sequence>/<Scene>/<TaskType>',
    )
        # file name
    working_asset_name: StringProperty(
        name="Asset Name",
        default='<Asset>',
    )
    working_shot_name: StringProperty(
        name="Shot Name",
        default='<Sequence>_<Shot>',
    )
    working_sequence_name: StringProperty(
        name="Sequence Name",
        default='<Sequence>',
    )
    working_scenes_name: StringProperty(
        name="Scenes Name",
        default='<Scene>',
    )

    #output file tree properties
    output_mountpoint: StringProperty(
        name="Mount Point",
        default='~',
    )
    output_root: StringProperty(
        name="Root",
        default='projects_output',
    )
      # folder paths
    output_asset_path: StringProperty(
        name="Asset Path",
        default='<Project>/assets/<Asset>/<AssetType>/<OutputType>',
    )
    output_shot_path: StringProperty(
        name="Shot Path",
        default='<Project>/shots/<Sequence>_<Shot>/<OutputType>',
    )
    output_sequence_path: StringProperty(
        name="Sequence Path",
        default='<Project>/sequences/<Sequence>/<OutputType>',
    )
    output_scenes_path: StringProperty(
        name="Scenes Path",
        default='<Project>/scenes/<Sequence>/<Scene>/<OutputType>',
    )
        # file name
    output_asset_name: StringProperty(
        name="Asset Name",
        default='<Project>_<AssetType>_<Asset>_<OutputType>_<OutputFile>',
    )
    output_shot_name: StringProperty(
        name="Shot Name",
        default='<Project>_<Sequence>_<Shot>_<OutputType>_<OutputFile>',
    )
    output_sequence_name: StringProperty(
        name="Sequence Name",
        default='<Project>_<Sequence>_<OuputType>_<OutputFile>',
    )
    output_scenes_name: StringProperty(
        name="Scenes Name",
        default='<Project>_<Sequence>_<Scene>_<OutputType>_<OutputFile>',
    )

    mixer_pref_path: StringProperty(
        name="Mixer Prefrence path",
        default=f'{os.getenv("APPDATA")}/Quixel/Quixel Mixer/Settings/MixerPrefs.xml',
    )
    mixer_luncher: StringProperty(
        name="Mixer Launcher path",
        default=f'',
    )
    use_mixer: BoolProperty(default=False, name='')

    def reset_messages(self):
        self.ok_message = ''
        self.error_message = ''


    def draw(self, context):
        layout = self.layout

        if self.error_message:
            sub = layout.row()
            sub.alert = True  # labels don't display in red :(
            sub.label(text=self.error_message, icon='ERROR')
        if self.ok_message:
            sub = layout.row()
            sub.label(text=self.ok_message, icon='FILE_TICK')

        box = layout.box()
        # layout.label(text="Nagato Preferences")
        box.prop(self, "host_url")
        box.operator('nagato.login')
        # box.prop(self, "project_mount_point")
        layout = self.layout
        row = layout.row()
        row.alignment = 'LEFT'
        row.prop(self, "use_mixer")
        row.label(text = "use_mixer")
        if self.use_mixer:
            box = layout.box()
            box.prop(self, "mixer_luncher")
            box.prop(self, "mixer_pref_path")

        ####### admin user settings  #####################
        if NagatoProfile.user and NagatoProfile.user['role'] == 'admin':
            layout.label(text="Admin Users Setting:")
            row = layout.row()
            row.enabled = bool(NagatoProfile.tasks)
            row.alignment = 'LEFT'

            if bool(NagatoProfile.active_project):
                project_label = NagatoProfile.active_project['name']
            else:
                project_label = 'select project'

            row.menu("NAGATO_MT_Projects", text = project_label)
            row = layout.row()
            row.alignment = 'LEFT'
            row.operator('nagato.svn_url')

            # set kitsu file tree
            row = layout.row(align=True)
            row.alignment = 'LEFT'
            if context.scene.show_working_file_tree:
                row.prop(context.scene, "show_working_file_tree", icon="DOWNARROW_HLT", text="working file tree setting", emboss=False)
            else:
                row.prop(context.scene, "show_working_file_tree", icon="RIGHTARROW", text="working file tree setting", emboss=False)
            if context.scene.show_working_file_tree:
                box = layout.box()
                box.label(text="mountpoint")
                box.prop(self, "working_mountpoint")
                box.label(text="root")
                box.prop(self, "working_root")
                box_2 = box.box()
                box_2.label(text="folder path:")
                box_2.prop(self, "working_asset_path")
                box_2.prop(self, "working_shot_path")
                # box_2.prop(self, "sequence_path")
                # box_2.prop(self, "scenes_path")
                box_3 = box.box()
                box_3.label(text="file name:")
                box_3.prop(self, "working_asset_name")
                box_3.prop(self, "working_shot_name")
                box_3.prop(self, "working_sequence_name")
                # box_3.prop(self, "scenes_name")
                # layout = self.layout


            row = layout.row(align=True)
            row.alignment = 'LEFT'
            if context.scene.show_output_file_tree:
                row.prop(context.scene, "show_output_file_tree", icon="DOWNARROW_HLT", text="output file tree setting", emboss=False)
            else:
                row.prop(context.scene, "show_output_file_tree", icon="RIGHTARROW", text="output file tree setting", emboss=False)
            if context.scene.show_output_file_tree:
                box = layout.box()
                box.label(text="mountpoint")
                box.prop(self, "output_mountpoint")
                box.label(text="root")
                box.prop(self, "output_root")
                box_2 = box.box()
                box_2.label(text="folder path:")
                box_2.prop(self, "output_asset_path")
                box_2.prop(self, "output_shot_path")
                # box_2.prop(self, "sequence_path")
                # box_2.prop(self, "scenes_path")
                box_3 = box.box()
                box_3.label(text="file name:")
                box_3.prop(self, "output_asset_name")
                box_3.prop(self, "output_shot_name")
                box_3.prop(self, "output_sequence_name")
                # box_3.prop(self, "scenes_name")
                # layout = self.layout



                layout.operator('nagato.set_file_tree', text='apply file tree')
                


# registration
classes = [
    NagatoPreferences
]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.show_working_file_tree = bpy.props.BoolProperty(name='show working file tree', default=False)
    bpy.types.Scene.show_output_file_tree = bpy.props.BoolProperty(name='show output file tree', default=False)
    bpy.context.preferences.addons['nagato'].preferences.reset_messages()   

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls) 

    del bpy.types.Scene.show_working_file_tree
    del bpy.types.Scene.show_output_file_tree