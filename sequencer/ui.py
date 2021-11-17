import bpy
from nagato import ui
from ..profile import NagatoProfile

def act_strip(context):
    try:
        return context.scene.sequence_editor.active_strip
    except AttributeError:
        return None

class SequencerButtonsPanel():
    bl_space_type = 'SEQUENCE_EDITOR'
    bl_region_type = 'UI'

    @staticmethod
    def has_sequencer(context):
        return (context.space_data.view_type in {'SEQUENCER', 'SEQUENCER_PREVIEW'})

    @classmethod
    def poll(cls, context):
        return cls.has_sequencer(context) and (act_strip(context) is not None)


class NAGATO_PT_SequencerPanel(ui.NAGATO_PT_TaskManagementPanel):
# class NAGATO_PT_SequencerPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Nagato"
    bl_idname = "NAGATO_PT_SequencerPanel"
    bl_category = "Nagato"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = 'UI'
    
    def draw(self, context):
        super().draw(context)
        layout = self.layout

        # if context.preferences.addons['nagato'].preferences.error_message:
        #     sub = layout.row()
        #     sub.alert = True
        #     sub.label(text=context.preferences.addons['nagato'].preferences.error_message, icon='ERROR')
        # elif context.preferences.addons['nagato'].preferences.ok_message:
        #     sub = layout.row()
        #     sub.label(text=context.preferences.addons['nagato'].preferences.ok_message, icon='FILE_TICK')
        
        # if NagatoProfile.user == None:
        #     layout.label(text= f'user: Not logged in')
        # else:
        #     layout.label(text= f'user: {NagatoProfile.user["full_name"]}')
        # row = layout.row()
        # row.alignment = 'LEFT'
        # coll = row.column()
        # coll.operator('nagato.login', icon = 'USER')   
        # coll = row.column()
        # coll.operator('nagato.logout', icon = 'USER')   
        # coll = row.column()
        # coll.enabled = bool(NagatoProfile.user)
        # coll.operator('nagato.refresh', icon = 'FILE_REFRESH', text= '')

        ####### asset_types menu  #####################
        row = layout.row()
        # row.alert = True
        # col = row.column()
        row.separator()
        row = layout.row()
        row.operator('nagato.pull_shots', text= 'Pull shots from Kitsu')
        row.operator('nagato.push_shots', text= 'Push shots to Kitsu')
        
        box = layout.box()
        row = box.row()
        row.prop(context.scene, 'render_type', text= '')
        row.operator('nagato.update_strip_media', text= 'update strip media')

        
        # col.operator('nagato.submit_shots_to_kitsu', text= 'Submit Selected Shots to Kitsu')
        # col.operator('nagato.project_open_in_browser', icon= 'WORLD', text= 'Open Project in Browser')



classes = [
    NAGATO_PT_SequencerPanel
]
    
    
# registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)  