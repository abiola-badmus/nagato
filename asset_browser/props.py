import bpy
from bpy.types import (PropertyGroup,)
from bpy.props import (StringProperty,BoolProperty)


class Asset(PropertyGroup):
     asset: StringProperty()
     multi_select: BoolProperty(default=False)
     

classes = [
        Asset,
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