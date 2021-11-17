import bpy
from bpy.types import UIList

class REVISIONS_UL_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor= 0.1, align=True)
            split.label(text = item.revision)
            split.label(text = item.author)
            # split.label(text = item.message)
            split.label(text = item.date)
        elif self.layout_type in {'GRID'}:
            pass


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


# registration
classes = [
    REVISIONS_UL_list,
]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)  