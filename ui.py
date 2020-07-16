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
        
        row = layout.row()
        box = row.box()
        col = box.column(align= True)
        col.operator('nagato.add', icon = 'ADD')
        col.operator('nagato.publish', icon = 'EXPORT')
        col.operator('nagato.update', icon = 'IMPORT')
        col.operator('nagato.update_all', icon = 'IMPORT')

        row = layout.row()
        box = row.box()
        col = box.column(align= True)
        col.operator('nagato.revert', icon='LOOP_BACK')
        col.operator('nagato.resolve', icon = 'OUTLINER_DATA_GREASEPENCIL')
        col.operator('nagato.clean_up', icon = 'BRUSH_DATA')

        row = layout.row()
        row.operator('nagato.check_out', text= 'download project files',icon = 'IMPORT')
        row = layout.row()
        row.operator('nagato.consolidate', text= 'consolidate maps', icon = 'FULLSCREEN_EXIT')
        

class NAGATO_PT_TaskManagementPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Task Management"
    bl_idname = "SASORI_PT_ui"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    
    
    def draw(self, context):
        layout = self.layout
        
        task_list_index = bpy.context.scene.col_idx
        col = context.scene.col
        idx = context.scene.col_idx
        
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
        coll = row.column()
        coll.operator('nagato.login', icon = 'USER')   
        coll = row.column()
        coll.operator('nagato.refresh', icon= 'FILE_REFRESH', text= '')
        
        ####### projects menu  #####################
        if len(nagato.kitsu.project_names) == 0:
            r = 'no'
        else:
            r = 'yes'
        row = layout.row()
        row.enabled = r == 'yes'
        row = row.column()
        if len(nagato.kitsu.current_project) == 0:
            project_label = 'select project'
        else:
            project_label = nagato.kitsu.current_project[0]
        row.menu("nagato.select_project", text = project_label)
        
        ############# filter menu #############################
        if len(nagato.kitsu.task_tpyes) == 0:
            rf = 'no'
        else:
            rf = 'yes'
        row = layout.row()
        row.enabled = rf == 'yes'
        if len(nagato.kitsu.current_filter) == 0:
            filter_label = 'select filter'
        else:
            filter_label = nagato.kitsu.current_filter[0]
        row.menu("nagato.filter_tasks", text = filter_label)
        
        ######### task list ######################################
        row = layout.row()
        row.template_list("TASKS_UL_list", "", context.scene, "col", context.scene, "col_idx")
        
        #lists the amount of task in selected category
        layout.prop(context.scene, 'col')
        
        layout.operator('nagato.open', icon= 'FILEBROWSER', text= 'open file') 
        
        ########## task description ####################
        try:
            row = layout.row()
            box = row.box()
            box.label(text= 'description:')
            box.label(text= nagato.kitsu.filtered_todo[task_list_index]['entity_description'])
            
        except:
            pass        
        
        ########### update status ######################33
        row = layout.row()
        row.enabled = text == "Task file"
        row.operator('nagato.update_status', icon ='OUTLINER_DATA_GP_LAYER')


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

        if len(nagato.asset_browser.active_asset_type) == 0:
            asset_type_label = 'select asset type'
        else:
            asset_type_label = nagato.asset_browser.active_asset_type[0]
        row.menu("nagato.select_asset_type", text = asset_type_label)
        
        ######### task list ######################################
        row = layout.row()
        row.template_list("ASSETS_UL_list", "", context.scene, "assets", context.scene, "assets_idx")
        row = layout.row()
        row.operator('nagato.link_asset', icon= 'LINKED', text= 'link asset')
        row.operator('nagato.link_selected_asset', icon= 'LINKED', text= 'link selected assets')
               


#####preferences###################################
class NagatoGenesis(bpy.types.AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = 'nagato'
    user = os.environ.get('homepath').replace("\\","/")
    local_host_url: StringProperty(
        name="Local url of server",
        default='http://rukia/api',
    )

    remote_host_url: StringProperty(
        name="Remote url of server",
        default='',
    )

    project_mount_point: StringProperty(
        name="Project mounting point",
        default='C:' + user,
    )

    def draw(self, context):
        layout = self.layout
        # layout.label(text="Nagato Preferences")
        layout.prop(self, "local_host_url")
        layout.prop(self, "remote_host_url")
        layout.prop(self, "project_mount_point")
        layout.operator('nagato.login')


# registration
def register():
    bpy.utils.register_class(NAGATO_PT_TaskManagementPanel)
    bpy.utils.register_class(NAGATO_PT_VersionControlPanel)
    bpy.utils.register_class(NAGATO_PT_AssetBrowserPanel)
    bpy.utils.register_class(NagatoGenesis)

def unregister():
    bpy.utils.unregister_class(NAGATO_PT_TaskManagementPanel)
    bpy.utils.unregister_class(NAGATO_PT_VersionControlPanel)
    bpy.utils.unregister_class(NAGATO_PT_AssetBrowserPanel)
    bpy.utils.unregister_class(NagatoGenesis)