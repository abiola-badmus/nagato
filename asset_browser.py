import bpy
import os
from bpy.types import (Operator, PropertyGroup, CollectionProperty, Menu)
from bpy.props import (StringProperty, IntProperty, BoolProperty)
from nagato.kitsu import current_project
assets_data = {
   'chars': [] , 'envs': [], 'props': []
}
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
            elif active_asset_type[0] == 'props':
                layout.label(text = item.asset, icon='MATCUBE')
            elif active_asset_type[0] == 'chars':
                layout.label(text = item.asset, icon='MONKEY')
            elif active_asset_type[0] == 'envs':
                layout.label(text = item.asset, icon='WORLD_DATA')

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
        print(current_project)
        print(len(current_project))
        assets_data['chars'].clear()
        assets_data['envs'].clear()
        assets_data['props'].clear()
        try:
            mount_point = context.preferences.addons['nagato'].preferences.project_mount_point
            project_path = mount_point.replace("\\","/") + '/' + 'projects' + '/' + current_project[0] + '/lib/'
            for path in os.listdir(project_path):
                for asset in os.listdir(project_path + path):
                    if path == 'chars':
                        if asset.rsplit('.', 1)[-1] == 'blend':
                            assets_data['chars'].append(asset.rsplit('.', 1)[0])
                    if path == 'envs':
                        if asset.rsplit('.', 1)[-1] == 'blend':
                            assets_data['envs'].append(asset.rsplit('.', 1)[0])
                    if path == 'props':
                        if asset.rsplit('.', 1)[-1] == 'blend':
                            assets_data['props'].append(asset.rsplit('.', 1)[0])
            self.report({'INFO'}, 'Refreshed')
        except:
            self.report({'INFO'}, 'Not Logged in')
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
        for asset_type in assets_data:
            if asset_type == self.asset_type:
                for asset in assets_data[asset_type]:
                    displayed_assets.append(asset)
        update_asset_list(scene)
        active_asset_type.clear()
        active_asset_type.append(self.asset_type)
        print(active_asset_type)
        bpy.context.scene.update_tag()
        self.report({'INFO'}, 'Asset_type: ' + self.asset_type)
        return{'FINISHED'}


class NAGATO_OT_LinkAsset(Operator):
    bl_label = 'link asset'
    bl_idname = 'nagato.link_asset'
    bl_description = 'link in selected asset'    

    def execute(self, context):
        asset_list_index = bpy.context.scene.assets_idx
        file_name = displayed_assets[asset_list_index]
        mount_point = context.preferences.addons['nagato'].preferences.project_mount_point
        asset_path = mount_point.replace("\\","/") + '/' + 'projects' + '/' + current_project[0] + '/lib/' + active_asset_type[0]
        blend_file = asset_path + '/' + file_name + '.blend'
        section = "\\Collection\\"
        file_path = blend_file + section + file_name
        directory = blend_file + section

        bpy.ops.wm.link(
            filepath=file_path,
            filename=file_name,
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
                mount_point = context.preferences.addons['nagato'].preferences.project_mount_point
                asset_path = mount_point.replace("\\","/") + '/' + 'projects' + '/' + current_project[0] + '/lib/' + active_asset_type[0]
                blend_file = asset_path + '/' + file_name + '.blend'
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
        mount_point = context.preferences.addons['nagato'].preferences.project_mount_point
        asset_path = mount_point.replace("\\","/") + '/' + 'projects' + '/' + current_project[0] + '/lib/' + active_asset_type[0]
        blend_file = asset_path + '/' + file_name + '.blend'
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
                mount_point = context.preferences.addons['nagato'].preferences.project_mount_point
                asset_path = mount_point.replace("\\","/") + '/' + 'projects' + '/' + current_project[0] + '/lib/' + active_asset_type[0]
                blend_file = asset_path + '/' + file_name + '.blend'
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
    bl_idname = "nagato.select_asset_type"

    def draw(self, context):
        asset_types = ['chars', 'envs', 'props']
        for i in asset_types:
            layout = self.layout
            layout.operator('nagato.assets', text= i).asset_type = i


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
        NAGATO_OT_AppendSelectedAsset
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