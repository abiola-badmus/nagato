import bpy
from . import gazu
import nagato.kitsu
import nagato.asset_browser
from bpy.types import (Operator, PropertyGroup, CollectionProperty, Menu)
from bpy.props import (StringProperty, IntProperty)
import os
from . import nagato_icon


class NAGATO_PT_VersionControlPanel(bpy.types.Panel):
    bl_label = 'Version Control'
    bl_idname = 'SVN_PT_Pysvn'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    
    
    # panel functions
    def draw(self, context):
        layout = self.layout
        layout.label(text='SVN version control')
        
        box = layout.box()
        row = box.row(align=True)
        col = row.column()
        # box = row.box()
        # col = box.column(align= True)
        col.operator('nagato.publish', icon = 'EXPORT')
        col.operator('nagato.add', icon = 'ADD')
        col = row.column()
        col.operator('nagato.update', icon = 'IMPORT')
        col.operator('nagato.update_all', icon = 'IMPORT')
        
        row = layout.row()
        col = row.column(align= True)
        col.operator('nagato.revert', icon='LOOP_BACK')
        col.operator('nagato.resolve', icon = 'OUTLINER_DATA_GREASEPENCIL')
        col.operator('nagato.clean_up', icon = 'BRUSH_DATA')

        col = row.column(align= True)
        col.operator('nagato.check_out', text= 'download project files',icon = 'IMPORT')
        # row.alignment = 'LEFT'
        col.operator('nagato.consolidate', text= 'consolidate maps', icon = 'FULLSCREEN_EXIT')
        col.operator('nagato.get_ref', text= 'get refernce images')

class NAGATO_PT_TaskManagementPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Task Management"
    bl_idname = "SASORI_PT_ui"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"

    def draw_header(self, context):
        self.layout.operator('nagato.setting', icon = 'PREFERENCES', text="")
    
    def draw(self, context):
        layout = self.layout

        if context.preferences.addons['nagato'].preferences.error_message:
            sub = layout.row()
            sub.alert = True  # labels don't display in red :(
            sub.label(text=context.preferences.addons['nagato'].preferences.error_message, icon='ERROR')
        if context.preferences.addons['nagato'].preferences.ok_message:
            sub = layout.row()
            sub.label(text=context.preferences.addons['nagato'].preferences.ok_message, icon='FILE_TICK')
        
        task_list_index = bpy.context.scene.tasks_idx
        col = context.scene.tasks
        idx = context.scene.tasks_idx
        
        if idx >= len(col):
            text = "(index error)"
        else:
            text = "Task file"
        
        #displays the name of current logging in user
        # try:
        #     layout.label(text= f'user: testing')
        #     # layout.label(text= f'user: {gazu.user.client.get_current_user()["full_name"]}')
        # except:
        #     layout.label(text= f'user: No Logged in user')
        if nagato.kitsu.NagatoProfile.user == None:
            layout.label(text= f'user: Not logged in')
        else:
            layout.label(text= f'user: {nagato.kitsu.NagatoProfile.user["full_name"]}')
        row = layout.row()
        row.alignment = 'LEFT'
        coll = row.column()
        coll.operator('nagato.login', icon = 'USER')   
        coll = row.column()
        coll.operator('nagato.logout', icon = 'USER')   
        coll = row.column()
        coll.enabled = bool(nagato.kitsu.NagatoProfile.user)
        coll.operator('nagato.refresh', icon = 'FILE_REFRESH', text= '')
        
        ####### projects menu  #####################
        # r = 'no' if len(nagato.kitsu.project_names) == 0 else 'yes'
        row = layout.row()
        row.enabled = bool(nagato.kitsu.NagatoProfile.tasks)
        row.alignment = 'LEFT'

        if bool(nagato.kitsu.NagatoProfile.active_project):
            project_label = nagato.kitsu.NagatoProfile.active_project['name']
        else:
            project_label = 'select project'
        row.menu("NAGATO_MT_Projects", text = project_label)
        if nagato.kitsu.NagatoProfile.active_project:
            mount_point = nagato.kitsu.NagatoProfile.active_project['file_tree']['working']['mountpoint'] #context.preferences.addons['nagato'].preferences.project_mount_point
            root = nagato.kitsu.NagatoProfile.active_project['file_tree']['working']['root']
        else:
            mount_point = 'None'
            root = 'None'
        project_folder = os.path.expanduser(os.path.join(mount_point, root, project_label.replace(' ', '_').lower()))
        if os.path.isdir(project_folder):
            row.operator('nagato.update_all', text= 'update all files', icon = 'IMPORT')
        else:
            row.operator('nagato.check_out', text= 'download project files', icon = 'IMPORT')
        row.operator('nagato.project_open_in_browser', icon= 'WORLD', text= '')
        
        ############# filter menu #############################
        # rf = 'no' if len(nagato.kitsu.task_tpyes) == 0 else 'yes' 
        row = layout.row()
        row.enabled = bool(nagato.kitsu.NagatoProfile.active_project)
        row.alignment = 'LEFT'
        if nagato.kitsu.NagatoProfile.active_task_type == None:
            filter_label = 'select filter'
        else:
            filter_label = nagato.kitsu.NagatoProfile.active_task_type
        row.menu("NAGATO_MT_FilterTask", text = filter_label)
        
        ######### task list ######################################
        row = layout.row()
        row.template_list("TASKS_UL_list", "", context.scene, "tasks", context.scene, "tasks_idx", rows=7)
        col = row.column()
        col.operator("nagato.open", icon_value = nagato_icon.icon('open_file'), text="")
        col.enabled = text == "Task file"
        col.operator("nagato.update_status", icon='OUTLINER_DATA_GP_LAYER', text="")
        col.separator()
        col.menu("NAGATO_MT_ProjectFiles", icon="DOWNARROW_HLT", text="")
        col.separator()
        col.operator('nagato.publish_selected', icon_value = nagato_icon.icon('publish_file'), text='')
        col.operator('nagato.update_selected', icon_value = nagato_icon.icon('update_file'), text='')
        col.operator('nagato.revision_log', icon_value = nagato_icon.icon('version_history'), text='')

        
        #lists the amount of task in selected category
        layout.prop(context.scene, 'tasks')
         
        #TODO file and revison info
        ########## task description ####################
        scene = context.scene
        row = layout.row(align=True)
        row.alignment = 'LEFT'
        if scene.show_description:
            row.prop(scene, "show_description", icon="DOWNARROW_HLT", text="task description", emboss=False)
        else:
            row.prop(scene, "show_description", icon="RIGHTARROW", text="task description", emboss=False)
        if scene.show_description:
            for a in  bpy.context.screen.areas:
                if a.type == "PROPERTIES":
                    wrap_width = a.width/5.93
            row = layout.row(align=True)
            box = row.box()
            import textwrap
            try:
                active_project = nagato.kitsu.NagatoProfile.active_project['name']
                active_task_type = nagato.kitsu.NagatoProfile.active_task_type
                description = nagato.kitsu.NagatoProfile.tasks[active_project][active_task_type][task_list_index]['entity_description']
            except (TypeError, KeyError):
                description = 'None'
            wrapped_description = textwrap.wrap(description, wrap_width)
            for text in wrapped_description:
                box.label(text=text)
                
        layout.separator_spacer()
        layout.operator('nagato.get_dependencies', icon= 'LINKED', text= 'Get Dependencies')
        # mixer buttons
        box = layout.box()
        row = box.row()
        row.operator('nagato.lunch_mixer', text= 'Send to Mixer')
        row.operator('nagato.import_textures', text= 'Import Mixer Textures')
        
        ########### update status ######################33
        # row = layout.row()
        # row.enabled = text == "Task file"
        # row.operator('nagato.update_status', icon ='OUTLINER_DATA_GP_LAYER')


class NAGATO_PT_AssetBrowserPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Asset Browser"
    bl_idname = "NAGATO_PT_asset_browser"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    
    
    def draw(self, context):
        layout = self.layout
        ####### asset_types menu  #####################
        row = layout.row()
        row = row.column()
        row.alignment = 'LEFT'
        if len(nagato.asset_browser.active_asset_type) == 0:
            asset_type_label = 'select asset type'
        else:
            asset_type_label = nagato.asset_browser.active_asset_type[0]
        row.menu("NAGATO_MT_AssetType", text = asset_type_label)
        
        ######### task list ######################################
        row = layout.row()
        row.template_list("ASSETS_UL_list", "", context.scene, "assets", context.scene, "assets_idx")
        col = row.column()
        col.operator('nagato.link_asset', icon= 'LINKED', text= '')
        col.operator('nagato.append_asset', icon= 'APPEND_BLEND', text= '')
        col.separator()
        col.menu('NAGATO_MT_AssetFiles', icon="DOWNARROW_HLT", text="")

def act_strip(context):
    try:
        return context.scene.sequence_editor.active_strip
    except AttributeError:
        return None

class SequencerButtonsPanel():
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'

    @staticmethod
    def has_sequencer(context):
        return (context.space_data.view_type in {'SEQUENCER', 'SEQUENCER_PREVIEW'})

    @classmethod
    def poll(cls, context):
        return cls.has_sequencer(context) and (act_strip(context) is not None)


class NAGATO_PT_SequencerPanel(SequencerButtonsPanel, bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Nagato"
    bl_idname = "NAGATO_PT_SequencerPanel"
    bl_category = "Strip"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = 'UI'
    bl_category = "Strip"
    
    @classmethod
    def poll(cls, context):
        if not cls.has_sequencer(context):
            return False

        strip = act_strip(context)
        if not strip:
            return False

        return strip.type in {
            'ADD', 'SUBTRACT', 'ALPHA_OVER', 'ALPHA_UNDER',
            'CROSS', 'GAMMA_CROSS', 'MULTIPLY', 'OVER_DROP',
            'WIPE', 'GLOW', 'TRANSFORM', 'COLOR', 'SPEED',
            'MULTICAM', 'GAUSSIAN_BLUR', 'TEXT', 'COLORMIX'
        } and bool(nagato.kitsu.NagatoProfile.user) and bool(nagato.kitsu.NagatoProfile.active_project)
    
    def draw(self, context):
        layout = self.layout
        ####### asset_types menu  #####################
        row = layout.row()
        # row.alert = True
        col = row.column()
        col.operator('nagato.submit_shots_to_kitsu', text= 'Submit Selected Shots to Kitsu')
        col.operator('nagato.project_open_in_browser', icon= 'WORLD', text= 'Open Project in Browser')
               

############################ Property groups #####################################################
class Revision(PropertyGroup):
    revision: StringProperty()
    message: StringProperty()
    author: StringProperty()
    date: StringProperty()

#################### mapping lists into column #################################
class Revision_UL_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor= 0.1, align=True)
            split.label(text = item.revision)
            split.label(text = item.author)
            # split.label(text = item.message)
            split.label(text = item.date)
        elif self.layout_type in {'GRID'}:
            pass


#####preferences###################################
class NagatoGenesis(bpy.types.AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = 'nagato'
    user = os.environ.get('homepath') #.replace("\\","/")
    local_host_url: StringProperty(
        name="Local url of server",
        default='http://myAddress/api',
    )

    remote_host_url: StringProperty(
        name="Remote url of server",
        default='',
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

    # project_mount_point: StringProperty(
    #     name="Project mounting point",
    #     default='C:' + user,
    # )
    
    #file tree properties
    mountpoint: StringProperty(
        name="Mount Point",
        default='~',
    )
    root: StringProperty(
        name="Root",
        default='projects',
    )
      # folder paths
    asset_path: StringProperty(
        name="Asset Path",
        default='<Project>/lib/<AssetType>',
    )
    shot_path: StringProperty(
        name="Shot Path",
        default='<Project>/scenes/<Sequence>/<Shot>',
    )
    sequence_path: StringProperty(
        name="Sequence Path",
        default='<Project>/sequences/<Sequence>/<TaskType>',
    )
    scenes_path: StringProperty(
        name="Scenes Path",
        default='<Project>/scenes/<Sequence>/<Scene>/<TaskType>',
    )
        # file name
    asset_name: StringProperty(
        name="Asset Name",
        default='<Asset>',
    )
    shot_name: StringProperty(
        name="Shot Name",
        default='<Sequence>_<Shot>',
    )
    sequence_name: StringProperty(
        name="Sequence Name",
        default='<Sequence>',
    )
    scenes_name: StringProperty(
        name="Scenes Name",
        default='<Scene>',
    )
    mixer_pref_path: StringProperty(
        name="Mixer Prefrence path",
        default=f'{os.getenv("APPDATA")}/Quixel/Quixel Mixer/Settings/MixerPrefs.xml',
    )
    mixer_luncher: StringProperty(
        name="Mixer Launcher path",
        default=f'C:/Users/Itadori/Eaxum/Software/Quixel/QuixelMixer-2021.1.1/Quixel Mixer.exe',
    )

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
        box.prop(self, "local_host_url")
        box.prop(self, "remote_host_url")
        # box.prop(self, "project_mount_point")
        layout = self.layout
        layout.operator('nagato.login')
        box = layout.box()
        box.prop(self, "mixer_luncher")
        box.prop(self, "mixer_pref_path")

        ####### admin user settings  #####################
        if nagato.kitsu.NagatoProfile.user and nagato.kitsu.NagatoProfile.user['role'] == 'admin':
            layout.label(text="Admin Users Setting:")
            row = layout.row()
            row.enabled = bool(nagato.kitsu.NagatoProfile.tasks)
            row.alignment = 'LEFT'

            if bool(nagato.kitsu.NagatoProfile.active_project):
                project_label = nagato.kitsu.NagatoProfile.active_project['name']
            else:
                project_label = 'select project'

            row.menu("NAGATO_MT_Projects", text = project_label)
            row = layout.row()
            row.alignment = 'LEFT'
            row.operator('nagato.svn_url')

            # set kitsu file tree
            box = layout.box()
            box.label(text="mountpoint")
            box.prop(self, "mountpoint")
            box.label(text="root")
            box.prop(self, "root")
            box_2 = box.box()
            box_2.label(text="folder path:")
            box_2.prop(self, "asset_path")
            box_2.prop(self, "shot_path")
            # box_2.prop(self, "sequence_path")
            # box_2.prop(self, "scenes_path")
            box_3 = box.box()
            box_3.label(text="file name:")
            box_3.prop(self, "asset_name")
            box_3.prop(self, "shot_name")
            box_3.prop(self, "sequence_name")
            # box_3.prop(self, "scenes_name")
            # layout = self.layout
            layout.operator('nagato.set_file_tree', text='apply file tree')


# registration
classes = [
    Revision,
    Revision_UL_list,
    NAGATO_PT_TaskManagementPanel,
    NAGATO_PT_AssetBrowserPanel,
    NAGATO_PT_SequencerPanel,
    NagatoGenesis,
]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.show_description = bpy.props.BoolProperty(name='description', default=False)
    bpy.types.Scene.show_history = bpy.props.BoolProperty(name='file history', default=False)

    bpy.types.Scene.revisions = bpy.props.CollectionProperty(type=Revision)
    bpy.types.Scene.revisions_idx = bpy.props.IntProperty(default=0)

    bpy.context.preferences.addons['nagato'].preferences.reset_messages()   

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)  