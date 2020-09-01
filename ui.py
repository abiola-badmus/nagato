import bpy
import gazu
import nagato.kitsu
import nagato.asset_browser
from bpy.types import (Operator, PropertyGroup, CollectionProperty, Menu)
from bpy.props import (StringProperty, IntProperty)
import os


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
    
    
    def draw(self, context):
        layout = self.layout
        
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
        layout.label(text= f'user: {nagato.kitsu.current_user[0]}')                         
        row = layout.row()
        row.alignment = 'LEFT'
        coll = row.column()
        coll.operator('nagato.login', icon = 'USER')   
        coll = row.column()
        coll.operator('nagato.refresh', icon= 'FILE_REFRESH', text= '')
        
        ####### projects menu  #####################
        r = 'no' if len(nagato.kitsu.project_names) == 0 else 'yes'
        row = layout.row()
        row.enabled = r == 'yes'
        row.alignment = 'LEFT'

        if len(nagato.kitsu.current_project) == 0:
            project_label = 'select project'
        else:
            project_label = nagato.kitsu.current_project[0]
        row.menu("nagato.select_project", text = project_label)
        
        ############# filter menu #############################
        rf = 'no' if len(nagato.kitsu.task_tpyes) == 0 else 'yes' 
        row = layout.row()
        row.enabled = rf == 'yes'
        row.alignment = 'LEFT'
        if len(nagato.kitsu.current_filter) == 0:
            filter_label = 'select filter'
        else:
            filter_label = nagato.kitsu.current_filter[0]
        row.menu("nagato.filter_tasks", text = filter_label)
        
        ######### task list ######################################
        row = layout.row()
        row.template_list("TASKS_UL_list", "", context.scene, "tasks", context.scene, "tasks_idx", rows=6)
        col = row.column()
        col.operator("nagato.open", icon='FILEBROWSER', text="")
        col.enabled = text == "Task file"
        col.operator("nagato.update_status", icon='OUTLINER_DATA_GP_LAYER', text="")
        col.separator()
        col.menu("nagato.project_files", icon="DOWNARROW_HLT", text="")
        col.separator()
        col.operator('nagato.publish', icon = 'EXPORT', text='')
        col.operator('nagato.update', icon = 'IMPORT', text='')

        
        #lists the amount of task in selected category
        layout.prop(context.scene, 'tasks')
        
        # layout.operator('nagato.open', icon= 'FILEBROWSER', text= 'open file') 
        
        ########## task description ####################
        try:
            row = layout.row()
            box = row.box()
            box.label(text= 'description:')
            box.label(text= nagato.kitsu.filtered_todo[task_list_index]['entity_description'])
            
        except:
            pass        
        
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
        row.menu("nagato.select_asset_type", text = asset_type_label)
        
        ######### task list ######################################
        row = layout.row()
        row.template_list("ASSETS_UL_list", "", context.scene, "assets", context.scene, "assets_idx")
        col = row.column()
        col.operator('nagato.link_asset', icon= 'LINKED', text= '')
        col.operator('nagato.append_asset', icon= 'APPEND_BLEND', text= '')
        col.separator()
        col.menu('nagato.asset_files', icon="DOWNARROW_HLT", text="")
               


#####preferences###################################
class NagatoGenesis(bpy.types.AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = 'nagato'
    user = os.environ.get('homepath') #.replace("\\","/")
    local_host_url: StringProperty(
        name="Local url of server",
        # default='http://myAddress/api',
        default='https://studio.eaxum.com/api',
    )

    remote_host_url: StringProperty(
        name="Remote url of server",
        default='',
    )

    project_mount_point: StringProperty(
        name="Project mounting point",
        default='C:' + user,
    )
    
    #file tree properties
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
    




    def draw(self, context):
        layout = self.layout
        box = layout.box()
        # layout.label(text="Nagato Preferences")
        box.prop(self, "local_host_url")
        box.prop(self, "remote_host_url")
        box.prop(self, "project_mount_point")
        layout = self.layout
        layout.operator('nagato.login')

        ####### projects menu  #####################
        layout.label(text="Admin Users Setting:")
        r = 'no' if len(nagato.kitsu.project_names) == 0 else 'yes'
        row = layout.row()
        row.enabled = r == 'yes'
        row.alignment = 'LEFT'

        if len(nagato.kitsu.current_project) == 0:
            project_label = 'select project'
        else:
            project_label = nagato.kitsu.current_project[0]
        row.menu("nagato.select_project", text = project_label)
        row = layout.row()
        row.alignment = 'LEFT'
        row.operator('nagato.svn_url')

        # set kitsu file tree
        box = layout.box()
        box.label(text="root")
        box.prop(self, "root")
        box_2 = box.box()
        box_2.label(text="folder path:")
        box_2.prop(self, "asset_path")
        box_2.prop(self, "shot_path")
        box_2.prop(self, "sequence_path")
        box_2.prop(self, "scenes_path")
        box_3 = box.box()
        box_3.label(text="file name:")
        box_3.prop(self, "asset_name")
        box_3.prop(self, "shot_name")
        box_3.prop(self, "sequence_name")
        box_3.prop(self, "scenes_name")
        # layout = self.layout
        # layout.operator('nagato.login')


# registration
def register():
    bpy.utils.register_class(NAGATO_PT_TaskManagementPanel)
    # bpy.utils.register_class(NAGATO_PT_VersionControlPanel)
    bpy.utils.register_class(NAGATO_PT_AssetBrowserPanel)
    bpy.utils.register_class(NagatoGenesis)

def unregister():
    bpy.utils.unregister_class(NAGATO_PT_TaskManagementPanel)
    # bpy.utils.unregister_class(NAGATO_PT_VersionControlPanel)
    bpy.utils.unregister_class(NAGATO_PT_AssetBrowserPanel)
    bpy.utils.unregister_class(NagatoGenesis)