from . import gazu
import bpy
from bpy.types import PropertyGroup, Menu
from bpy.props import StringProperty, IntProperty, EnumProperty
import os
from . import nagato_icon, profile
NagatoProfile = profile.NagatoProfile
slugify = NagatoProfile.slugify

class NAGATO_PT_TaskManagementPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Nagato"
    bl_idname = "NAGATO_PT_ui"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"

    def draw_header(self, context):
        self.layout.operator('nagato.setting', icon = 'PREFERENCES', text="")
    
    def draw(self, context):
        layout = self.layout

        if context.preferences.addons['nagato'].preferences.error_message:
            sub = layout.row()
            sub.alert = True
            sub.label(text=context.preferences.addons['nagato'].preferences.error_message, icon='ERROR')
        elif context.preferences.addons['nagato'].preferences.ok_message:
            sub = layout.row()
            sub.label(text=context.preferences.addons['nagato'].preferences.ok_message, icon='FILE_TICK')
        
        task_list_index = bpy.context.scene.tasks_idx
        col = context.scene.tasks
        idx = context.scene.tasks_idx
        
        if idx >= len(col):
            text = "(index error)"
        else:
            text = "Task file"
        
        if NagatoProfile.user == None:
            layout.label(text= f'user: Not logged in')
        else:
            layout.label(text= f'user: {NagatoProfile.user["full_name"]}')
        row = layout.row()
        row.alignment = 'LEFT'
        coll = row.column()
        coll.operator('nagato.login', icon = 'USER')   
        coll = row.column()
        coll.operator('nagato.logout', icon = 'USER')   
        coll = row.column()
        coll.enabled = bool(NagatoProfile.user)
        coll.operator('nagato.refresh', icon = 'FILE_REFRESH', text= '')
        
        ####### projects menu  #####################
        row = layout.row()
        row.enabled = bool(NagatoProfile.tasks)
        row.alignment = 'LEFT'

        if bool(NagatoProfile.active_project):
            project_label = NagatoProfile.active_project['name']
        else:
            project_label = 'select project'
        row.menu("NAGATO_MT_Projects", text = project_label)
        if NagatoProfile.active_project:
            mount_point = NagatoProfile.active_project['file_tree']['working']['mountpoint'] #context.preferences.addons['nagato'].preferences.project_mount_point
            root = NagatoProfile.active_project['file_tree']['working']['root']
        else:
            mount_point = 'None'
            root = 'None'
        if bool(NagatoProfile.active_project):
            project_file_name = slugify(NagatoProfile.active_project['name'], separator = '_')
        else:
            project_file_name = 'none'
        project_folder = os.path.expanduser(os.path.join(mount_point, root, project_file_name))
        if os.path.isdir(project_folder):
            row.operator('nagato.update_all', text= 'update all files', icon = 'IMPORT')
        else:
            row.operator('nagato.check_out', text= 'download project files', icon = 'IMPORT')
        #TODO add delete button to ui
        # row.alert = True
        # row.operator('nagato.delete', icon= 'TRASH', text= '')
        # row.alert = False
        row.operator('nagato.project_open_in_browser', icon= 'WORLD', text= '')
        # row = layout.row()
        if context.scene.progress_bar != 0 and context.scene.progress_bar < 100:
            layout.prop(context.scene, "progress_bar", text="Progress", slider=True)
        
        ############# filter menu #############################
        row = layout.row()
        row.enabled = bool(NagatoProfile.active_project)
        row.alignment = 'LEFT'
        if NagatoProfile.active_task_type == None:
            filter_label = 'select filter'
        else:
            filter_label = NagatoProfile.active_task_type
        row.menu("NAGATO_MT_FilterTask", text = filter_label)
        
        ######### task list ######################################
        row = layout.row()
        row.template_list("TASKS_UL_list", "", context.scene, "tasks", context.scene, "tasks_idx", rows=5)
        col = row.column()
        col.operator("nagato.open", icon_value = nagato_icon.icon('open_file'), text="")
        col.enabled = text == "Task file"
        col.operator('nagato.revision_log', icon_value = nagato_icon.icon('version_history'), text='')
        col.separator()
        col.menu("NAGATO_MT_ProjectFiles", icon="DOWNARROW_HLT", text="")
        col.separator()
        col.operator('nagato.publish_selected', icon_value = nagato_icon.icon('publish_file'), text='')
        col.operator('nagato.update_selected', icon_value = nagato_icon.icon('update_file'), text='')

        
        #lists the amount of task in selected category
        layout.prop(context.scene, 'tasks')
        #TODO add more render for artist
        if NagatoProfile.lastest_openfile['file_path'] == bpy.context.blend_data.filepath:
            entity_id = NagatoProfile.lastest_openfile['entity_id']
            task_type = NagatoProfile.lastest_openfile['task_type']
            
            if task_type.lower() in {'layout'}:
                render_type = "previz"
            elif task_type.lower() in {"animation", "anim"}:
                render_type = "play_blast"
            elif task_type.lower() in {"lighting"}:
                render_type = "look_dev"
            else:
                render_type = None
            if render_type:
                layout.operator("nagato.render", text = f"render {render_type}")
                
        layout.operator('nagato.get_dependencies', icon= 'LINKED', text= 'Get Dependencies')
        # mixer buttons
        if context.preferences.addons['nagato'].preferences.use_mixer:
            box = layout.box()
            row = box.row()
            row.operator('nagato.lunch_mixer', text= 'Send to Mixer')
            row.operator('nagato.import_textures', text= 'Import Mixer Textures')
        

class NAGATO_MT_ProjectFiles(Menu):
    bl_label = 'project files operators'
    bl_idname = "NAGATO_MT_ProjectFiles"
    
    def draw(self, context):
        layout = self.layout
        # layout.operator('nagato.add', icon = 'ADD')
        # layout.separator()
        # layout.operator('nagato.update_all', text= 'update all files')
        # layout.operator('nagato.check_out', text= 'download project files')
        # layout.separator()
        layout.operator('nagato.consolidate', text= 'consolidate maps', icon = 'FULLSCREEN_EXIT')
        # TODO get reference images and send image to kitsu
        # FIX Consolidate maps
        # layout.operator('nagato.get_ref', text= 'get refernce images', icon='IMAGE_REFERENCE')
        layout.separator()
        # layout.operator('nagato.revision_log', icon='FILE_TEXT')
        layout.operator('nagato.revert_selected', icon='LOOP_BACK')
        # layout.operator('nagato.update_to_revision')
        layout.operator('nagato.resolve', icon_value = nagato_icon.icon('resolve_conflict'))
        layout.operator('nagato.clean_up', icon = 'BRUSH_DATA')



# registration
classes = [
    NAGATO_MT_ProjectFiles,
    NAGATO_PT_TaskManagementPanel,
]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.show_description = bpy.props.BoolProperty(name='description', default=False)
    bpy.types.WindowManager.preview_path = StringProperty(name="Preview",subtype='FILE_PATH',default="")
    bpy.types.Scene.comment = StringProperty(name="comment",default = '',description = 'type your comment')
    bpy.types.Scene.status = EnumProperty(
                                    items={
                                        ('todo', 'todo', 'set task status to todo'),
                                        ('wip', 'wip', 'set task status to work in progress'),
                                        ('wfa', 'wfa', 'set task status to waiting for approver')},
                                    default='wip',
                                    name= "",
                                    description="update task status",
                                    ) 

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)  