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


class Asset(PropertyGroup):
     asset: StringProperty()
     multi_select: BoolProperty(default=False)
     

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


class NAGATO_OT_AssetRefresh(Operator):
    bl_label = 'Asset Refresh'
    bl_idname = 'nagato.assets_refresh'
    bl_description = 'refresh assets'

    def execute(self, context):
        scene = context.scene
        assets_lib.clear()
        try:
            mount_point = NagatoProfile.active_project['file_tree']['working']['mountpoint']
            root = NagatoProfile.active_project['file_tree']['working']['root']
            project_folder = os.path.expanduser(os.path.join(mount_point, root, NagatoProfile.active_project['name'].replace(' ', '_')))
            project_lib_folder = os.path.join(project_folder, 'lib')

            for asset_type in os.listdir(project_lib_folder):
                if os.path.isdir(os.path.join(project_lib_folder,asset_type)):
                    assets_lib[asset_type] = list()
                    for asset in os.listdir(os.path.join(project_lib_folder,asset_type)):
                        if asset.rsplit('.', 1)[-1] == 'blend':
                            assets_lib[asset_type].append(asset.rsplit('.', 1)[0])
            self.report({'INFO'}, 'Refreshed')
        except NotAuthenticatedException:
            self.report({'INFO'}, 'Not Logged in')
        except FileNotFoundError:
            self.report({'INFO'}, 'files not found')
        scene.assets.clear()
        bpy.context.scene.update_tag()
        return{'FINISHED'}


class NAGATO_OT_Assets(Operator):
    bl_label = 'assets'
    bl_idname = 'nagato.assets'
    bl_description = 'select asset types'    
    
    asset_type: StringProperty(default='')
    
    def execute(self, context):
        scene = context.scene
        displayed_assets.clear()
        for asset_type in assets_lib:
            if asset_type == self.asset_type:
                for asset in assets_lib[asset_type]:
                    displayed_assets.append(asset)
        update_asset_list(scene)
        active_asset_type.clear()
        active_asset_type.append(self.asset_type)
        bpy.context.scene.update_tag()
        bpy.app.handlers.depsgraph_update_pre.append(update_asset_list)
        self.report({'INFO'}, 'Asset_type: ' + self.asset_type)
        return{'FINISHED'}


class NAGATO_OT_LinkAsset(Operator):
    bl_label = 'link asset'
    bl_idname = 'nagato.link_asset'
    bl_description = 'link in selected asset'    

    def execute(self, context):
        asset_list_index = bpy.context.scene.assets_idx
        file_name = displayed_assets[asset_list_index]
        mount_point = NagatoProfile.active_project['file_tree']['working']['mountpoint']
        root = NagatoProfile.active_project['file_tree']['working']['root']
        project_folder = os.path.expanduser(os.path.join(mount_point, root, NagatoProfile.active_project['name'].replace(' ', '_')))
        asset_path = os.path.join(project_folder, 'lib', active_asset_type[0])
        blend_file = os.path.join(asset_path, f'{file_name}.blend')
        # file_path = blend_file + section + file_name
        directory = f"{blend_file}/Collection"

        bpy.ops.wm.link(
            filename="main",
            directory=directory)
        self.report({'INFO'}, 'Asset Linked')
        return{'FINISHED'}


class NAGATO_OT_LinkSelectedAsset(Operator):
    bl_label = 'link asset'
    bl_idname = 'nagato.link_selected_asset'
    bl_description = 'link in all selected asset'    

    def execute(self, context):
        for asset in bpy.context.scene.assets:
            if asset.multi_select:
                file_name = asset.asset
                mount_point = NagatoProfile.active_project['file_tree']['working']['mountpoint']
                root = NagatoProfile.active_project['file_tree']['working']['root']
                project_folder = os.path.expanduser(os.path.join(mount_point, root, NagatoProfile.active_project['name']))
                asset_path = os.path.join(project_folder, 'lib', active_asset_type[0])
                blend_file = os.path.join(asset_path, f'{file_name}.blend')
                section = "\\Collection\\"
                file_path = blend_file + section + file_name
                directory = blend_file + section

                bpy.ops.wm.link(
                    filepath=file_path,
                    filename=file_name,
                    directory=directory)
        self.report({'INFO'}, 'Asset Linked')
        return{'FINISHED'}


class NAGATO_OT_AppendAsset(Operator):
    bl_label = 'append asset'
    bl_idname = 'nagato.append_asset'
    bl_description = 'append in selected asset'    

    def execute(self, context):
        asset_list_index = bpy.context.scene.assets_idx
        file_name = displayed_assets[asset_list_index]
        mount_point = NagatoProfile.active_project['file_tree']['working']['mountpoint']
        root = NagatoProfile.active_project['file_tree']['working']['root']
        project_folder = os.path.expanduser(os.path.join(mount_point, root, NagatoProfile.active_project['name']))
        asset_path = os.path.join(project_folder, 'lib', active_asset_type[0])
        blend_file = os.path.join(asset_path, f'{file_name}.blend')
        section = "\\Collection\\"
        file_path = blend_file + section + file_name
        directory = blend_file + section

        bpy.ops.wm.append(
            filepath=file_path,
            filename=file_name,
            directory=directory)
        self.report({'INFO'}, 'Asset appended')
        return{'FINISHED'}


class NAGATO_OT_AppendSelectedAsset(Operator):
    bl_label = 'append asset'
    bl_idname = 'nagato.append_selected_asset'
    bl_description = 'append in all selected asset'    

    def execute(self, context):
        for asset in bpy.context.scene.assets:
            if asset.multi_select:
                file_name = asset.asset
                mount_point = NagatoProfile.active_project['file_tree']['working']['mountpoint']
                root = NagatoProfile.active_project['file_tree']['working']['root']
                project_folder = os.path.expanduser(os.path.join(mount_point, root, NagatoProfile.active_project['name']))
                asset_path = os.path.join(project_folder, 'lib', active_asset_type[0])
                blend_file = os.path.join(asset_path, f'{file_name}.blend')
                section = "\\Collection\\"
                file_path = blend_file + section + file_name
                directory = blend_file + section

                bpy.ops.wm.append(
                    filepath=file_path,
                    filename=file_name,
                    directory=directory)
        self.report({'INFO'}, 'Asset appended')
        return {'FINISHED'}


######################################### Menu ################################################################################
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
############### all classes ####################    
classes = [
        Asset,
        ASSETS_UL_list,
        NAGATO_OT_AssetRefresh,
        NAGATO_MT_AssetType,
        NAGATO_OT_Assets,
        NAGATO_OT_LinkAsset,
        NAGATO_OT_LinkSelectedAsset,
        NAGATO_OT_AppendAsset,
        NAGATO_OT_AppendSelectedAsset,
        NAGATO_MT_AssetFiles
        ]  
    
    
# registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.assets = bpy.props.CollectionProperty(type=Asset)
    bpy.types.Scene.assets_idx = bpy.props.IntProperty(default=0)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
        
    del bpy.types.Scene.assets
    del bpy.types.Scene.assets_idx