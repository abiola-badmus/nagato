import bpy
import os
from .gazu.exception import NotAuthenticatedException
from bpy.types import (Operator, PropertyGroup, CollectionProperty, Menu)
from bpy.props import (StringProperty, IntProperty, BoolProperty)
from nagato.kitsu import NagatoProfile
assets_lib = dict()
displayed_assets = []
active_asset_type = []

def update_asset_list(scene):
    try:
        scene.assets.clear()
    except:
        pass

    for asset in displayed_assets:  
        colection = scene.assets.add()   
        colection.asset = asset

class ASSETS_UL_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}: 
            # split = layout.split(factor= 0.6, align=True) 
            if len(active_asset_type) == 0:
                layout.label(text = item.asset, icon='BLENDER')
            elif active_asset_type[0].lower() in {'props'}:
                layout.label(text = item.asset, icon='MATCUBE')
            elif active_asset_type[0].lower() in {'chars', 'characters'}:
                layout.label(text = item.asset, icon='MONKEY')
            elif active_asset_type[0].lower() in {'envs', 'environment'}:
                layout.label(text = item.asset, icon='WORLD_DATA')
            else:
                layout.label(text = item.asset, icon='BLENDER')

            if item.multi_select:
                layout.prop(item, 'multi_select', text='', icon = 'CHECKBOX_HLT', emboss=False, translate=False)
            else:
                layout.prop(item, 'multi_select', text='', icon = 'CHECKBOX_DEHLT', emboss=False, translate=False)

            # split.prop(text = item.multi_select)
        elif self.layout_type in {'GRID'}:
            pass


class NAGATO_MT_AssetType(Menu):
    bl_label = 'select asset type'
    bl_idname = "NAGATO_MT_AssetType"

    def draw(self, context):
        mount_point = NagatoProfile.active_project['file_tree']['working']['mountpoint']
        root = NagatoProfile.active_project['file_tree']['working']['root']
        project_folder = os.path.expanduser(os.path.join(mount_point, root, NagatoProfile.active_project['name'].replace(' ', '_')))
        project_lib_folder = os.path.join(project_folder, 'lib')
        asset_types = os.listdir(project_lib_folder)
        # asset_types = ['chars', 'envs', 'props']
        for i in asset_types:
            layout = self.layout
            layout.operator('nagato.assets', text= i).asset_type = i


class NAGATO_MT_AssetFiles(Menu):
    bl_label = 'project files operators'
    bl_idname = "NAGATO_MT_AssetFiles"
    
    def draw(self, context):
        layout = self.layout
        layout.operator('nagato.link_selected_asset', text= 'link selected assets')
        layout.operator('nagato.append_asset', text= 'append selected assets')


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

classes = [
        ASSETS_UL_list,
        NAGATO_MT_AssetType,
        NAGATO_MT_AssetFiles,
        NAGATO_PT_AssetBrowserPanel,
        ]  
    
    
# registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls) 

