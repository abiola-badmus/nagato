import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, IntProperty, BoolProperty
import time

time_queue = [0, 3]
def double_click(self, context):
    bpy.context.scene.tasks_idx = self.tasks_idx
    time_queue.pop(0)
    time_queue.append(time.time())
    if time_queue[1] - time_queue[0] <= 0.3:
        bpy.ops.nagato.open("INVOKE_DEFAULT")

class MyTasks(PropertyGroup):
    tasks_idx: IntProperty()
    tasks: StringProperty()
    tasks_status: StringProperty()
    file_status: StringProperty()
    task_id: StringProperty()
    click: BoolProperty(default=False, update=double_click)

# registration
classes = [
    MyTasks,
]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.tasks = bpy.props.CollectionProperty(type=MyTasks)
    bpy.types.Scene.tasks_idx = bpy.props.IntProperty(default=0)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.tasks
    del bpy.types.Scene.tasks_idx