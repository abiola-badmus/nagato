import bpy
from bpy.types import Menu
from bpy.props import StringProperty, EnumProperty, BoolProperty
from .. import profile, nagato_icon
from bpy.types import Menu

NagatoProfile = profile.NagatoProfile

use_filter = True
class TASKS_UL_list(bpy.types.UIList):
    comment: StringProperty(
        name = '',
        default = 'Add a comment',
        description = 'type your comment'
        )

    preview_path: StringProperty(
        name = 'add preview',
        default = '',
        description = 'path to preview file'
        )
    status: EnumProperty(
        items={
            ('todo', 'todo', 'set task status to todo'),
            ('wip', 'wip', 'set task status to work in progress'),
            ('wfa', 'wfa', 'set task status to waiting for approver')},
        default='wip',
        name= "",
        description="update task status",
        )
    filter_by_status: BoolProperty(default=False)

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        global use_filter
        if use_filter == True:
            self.use_filter_show = True
            use_filter = False
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            active_task_type = NagatoProfile.active_task_type
            active_task_id = NagatoProfile.lastest_openfile['task_id']
            active_task_file = NagatoProfile.lastest_openfile['file_path']
            if active_task_type == None:
                task_icon='BLENDER'
            elif item.task_id == active_task_id:
                task_icon='REC'
            elif active_task_type.lower() in {'modeling'}:
                task_icon='CUBE'
            elif active_task_type.lower() in {'shading', 'texturing'}:
                task_icon='SHADING_RENDERED'
            elif active_task_type.lower() in {'lighting'}:
                task_icon='OUTLINER_DATA_LIGHT'
            elif active_task_type.lower() in {'anim', 'animation'}:
                task_icon='ARMATURE_DATA'
            elif active_task_type.lower() in {'fx'}:
                task_icon='SHADERFX'
            elif active_task_type.lower() in {'rigging'}:
                task_icon='BONE_DATA'
            elif active_task_type.lower() in {'layout'}:
                task_icon='MOD_ARRAY'
            else:
                task_icon='BLENDER'

            # split = layout.split(factor= 0.7, align=True)
            split = layout.split(factor= 0.1, align=True)
            # split.prop(item, 'click',icon = task_icon, text=item.tasks, emboss=False, translate=False)
            split.prop(item, 'click',icon = task_icon, text='', emboss=False, translate=False)
            # split.factor = 0.7
            split = split.split(factor= 0.7, align=True)
            # split.label(text = item.tasks, icon = task_icon)
            split.label(text = item.tasks)
            split.label(text = item.tasks_status)
            if item.file_status == 'not_existing':
                split.label(text = '', icon = 'ERROR')
            elif item.file_status == 'normal':
                split.label(text = '', icon_value = nagato_icon.icon('NormalIcon'))
            elif item.file_status == 'modified':
                split.label(text = '', icon_value = nagato_icon.icon('ModifiedIcon'))
            elif item.file_status == 'conflicted':
                split.label(text = '', icon_value = nagato_icon.icon('ConflictIcon'))
            elif item.file_status == 'unversioned':
                split.label(text = '', icon_value = nagato_icon.icon('UnversionedIcon'))
            elif item.file_status == 'added':
                split.label(text = '', icon_value = nagato_icon.icon('AddedIcon'))
            elif item.file_status == 'missing':
                split.label(text = '', icon = 'ERROR')
            elif item.file_status == 'deleted':
                split.label(text = '', icon_value = nagato_icon.icon('DeletedIcon'))
        elif self.layout_type in {'GRID'}:
            pass

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        filtered = []
        ordered = []
        # for item in items:
        #     print(items)
        # x = items.sort(key=lambda x: x.tasks_status)
        # print(x)
        if self.filter_by_status:
            filter_name = "tasks_status"
        else:
            filter_name = "tasks"
        filtered = [self.bitflag_filter_item] * len(items)
        helpers = bpy.types.UI_UL_list
        filtered = helpers.filter_items_by_name(
            self.filter_name, 
            self.bitflag_filter_item, 
            items, filter_name, reverse=False
            )
        # ordered = [index for index, item in enumerate(items)]
        # print(ordered)
        items_list = [item.tasks_status for item in items]
        
        # for i, item in enumerate(items):
        #     print(i)
        def sort_tasks_by_status(items):
            wip = list()
            wfa = list()
            todo = list()
            retake = list()
            for i, item in enumerate(items):
                if item.tasks_status == 'wip':
                    wip.append(i)
                elif item.tasks_status == 'wfa':
                    wfa.append(i)
                elif item.tasks_status == 'todo':
                    todo.append(i)
                elif item.tasks_status == 'retake':
                    retake.append(i)
            ordered = todo + retake + wip + wfa
            # merge lists
            return ordered
        # if self.filter_by_status:
        #     # sort_items = bpy.types.UI_UL_list.sort_items_helper
        #     sort_items_by_name = bpy.types.UI_UL_list.sort_items_by_name
        #     ordered = sort_items_by_name(items, "tasks_status")
        #     orderedi = sort_tasks_by_status(items)
        #     # print(len(ordered))
        #     # print(len(items))
        #     print(ordered)
        #     print(orderedi)
        # filtered[0] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        layout.separator()
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, 'filter_name', text='', icon='VIEWZOOM')
        row.prop(self, 'use_filter_invert', text='', icon='ARROW_LEFTRIGHT')
        row.prop(self, 'filter_by_status', text='', icon='SORTALPHA')
        layout.separator()
        layout.prop(context.scene, "comment")
        col = layout.column(align=True)
        row = col.row()
        row.alignment = 'LEFT'
        row.prop(context.scene, "status")
        # layout.prop(self, "preview_path")
        # context.window_manager.preview_path
        row.alignment = 'EXPAND'
        row.prop(context.window_manager, "preview_path")
        layout.operator('nagato.post_comment')
        ########## task description ####################
        task_list_index = bpy.context.scene.tasks_idx
        row = layout.row(align=True)
        row.alignment = 'LEFT'
        if context.scene.show_description:
            row.prop(context.scene, "show_description", icon="DOWNARROW_HLT", text="task description", emboss=False)
        else:
            row.prop(context.scene, "show_description", icon="RIGHTARROW", text="task description", emboss=False)
        if context.scene.show_description:
            for a in  bpy.context.screen.areas:
                if a.type == "PROPERTIES":
                    wrap_width = a.width/5.93
            row = layout.row(align=True)
            box = row.box()
            import textwrap
            
            try:
                active_project = NagatoProfile.active_project['name']
                active_task_type = NagatoProfile.active_task_type
                description = NagatoProfile.tasks[active_project][active_task_type][task_list_index]['entity_description']
            except (TypeError, KeyError, IndexError):
                description = 'no description'
            if description:
                wrapped_description = textwrap.wrap(description, wrap_width)
                for text in wrapped_description:
                    box.label(text=text)
            else:
                description = 'no description'
                wrapped_description = textwrap.wrap(description, wrap_width)
                for text in wrapped_description:
                    box.label(text=text)



class NAGATO_MT_Projects(Menu):
    bl_label = 'select project'
    bl_idname = "NAGATO_MT_Projects"
    
    def draw(self, context):
        for project in sorted(NagatoProfile.tasks):
            layout = self.layout
            layout.operator('nagato.projects', text= project).project= project


class NAGATO_MT_FilterTask(Menu):
    bl_label = 'select filter'
    bl_idname = "NAGATO_MT_FilterTask"
    
    def draw(self, context):
        
        for task_type in sorted(NagatoProfile.tasks[NagatoProfile.active_project['name']]):
            layout = self.layout
            layout.operator('nagato.filter', text= task_type).filter = task_type

############### all classes ####################    
classes = [
        NAGATO_MT_FilterTask,
        NAGATO_MT_Projects,
        TASKS_UL_list,
        ]  
    
    
# registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)   

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)    