bl_info = {
    "name": "Nagato",
    "author": "Adesada J. Aderemi, Taiwo Folu",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > New Object",
    "description": "Perform svn commit and update directly from blender",
    "warning": "",
    "wiki_url": "",
    "category": "Version Control",
}

import bpy
from bpy.types import (
    Operator,
    Panel,
    AddonPreferences,
    PropertyGroup
)
from bpy.props import (StringProperty)
import pysvn


# classes
client = pysvn.Client()

class OBJECT_OT_SvnAdd(Operator):
    bl_label = 'Add file to SVN'
    bl_idname = 'svn.add'
    bl_description = 'Add current file to project repository'
    
    
    def execute(self, context):
        client.add(f'{bpy.context.blend_data.filepath}')
        self.report({'INFO'}, "File Added to Repository")
        return{'FINISHED'}
        

class OBJECT_OT_SvnCommit(Operator):
    bl_label = 'Publish file'
    bl_idname = 'svn.commit'
    bl_description = 'Publish current file to project repository'
    
    comment: StringProperty(
        name = 'comment',
        default = 'file published',
        description = 'comment for publishing'
        )
        
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    
    def execute(self, context):
        bpy.ops.wm.save_mainfile()
        client.checkin([f'{bpy.context.blend_data.filepath}'], self.comment)
        self.report({'INFO'}, "Publish successful")
        return{'FINISHED'}

    
class OBJECT_OT_SvnUpdate(Operator):
    bl_label = 'Update file'
    bl_idname = 'svn.update'
    bl_description = 'Update current file from project repository'
    
    
    def execute(self, context):
        client.update(f'{bpy.context.blend_data.filepath}')
        bpy.ops.wm.revert_mainfile()
        self.report({'INFO'}, "Update Successful")
        return{'FINISHED'}




class PysvnPanel(bpy.types.Panel):
    bl_label = 'Nagato'
    bl_idname = 'SVN_PT_Pysvn'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    
    
    # panel functions
    def draw(self, context):
        layout = self.layout
        
        layout.label(text='SVN version control')
        
        row = layout.row()
        col = row.column()
        col.operator('svn.add')
        col.operator('svn.commit')
        col.operator('svn.update')
        
        
# registration
def register():
    bpy.utils.register_class(OBJECT_OT_SvnAdd)
    bpy.utils.register_class(OBJECT_OT_SvnCommit)
    bpy.utils.register_class(OBJECT_OT_SvnUpdate)
    bpy.utils.register_class(PysvnPanel)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_SvnAdd)
    bpy.utils.unregister_class(OBJECT_OT_SvnCommit)
    bpy.utils.unregister_class(OBJECT_OT_SvnUpdate)
    bpy.utils.unregister_class(PysvnPanel)


if __name__ == "__main__":
    register()
