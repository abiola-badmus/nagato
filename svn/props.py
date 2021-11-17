import bpy

from bpy.types import PropertyGroup
from bpy.props import StringProperty

class Revision(PropertyGroup):
    revision: StringProperty()
    message: StringProperty()
    author: StringProperty()
    date: StringProperty()
# registration


classes = [
    Revision,
]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.revisions = bpy.props.CollectionProperty(type=Revision)
    bpy.types.Scene.revisions_idx = bpy.props.IntProperty(default=0)
    bpy.types.Scene.progress_bar = bpy.props.IntProperty(default=0, min=0, max=100, step=1, subtype='PERCENTAGE')

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.revisions
    del bpy.types.Scene.revisions_idx