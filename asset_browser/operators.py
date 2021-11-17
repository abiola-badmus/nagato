import bpy
import os
from nagato.gazu.exception import NotAuthenticatedException
from bpy.types import Operator
from bpy.props import StringProperty
from nagato.kitsu import NagatoProfile
assets_lib = dict()
displayed_assets = []
active_asset_type = []
#TODO slugify names in asset browser
def update_asset_list(scene):
    try:
        scene.assets.clear()
    except:
        pass

    for asset in displayed_assets:  
        colection = scene.assets.add()   
        colection.asset = asset

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


############### all classes ####################    
classes = [
        NAGATO_OT_AssetRefresh,
        NAGATO_OT_Assets,
        NAGATO_OT_LinkAsset,
        NAGATO_OT_LinkSelectedAsset,
        NAGATO_OT_AppendAsset,
        NAGATO_OT_AppendSelectedAsset,
        ]  
    
    
# registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)