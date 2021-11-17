import bpy

def set_error_message(message, context):
    context.preferences.addons['nagato'].preferences.error_message =  message

def set_ok_message(message, context):
    context.preferences.addons['nagato'].preferences.ok_message =  message
    set_error_message("", context)


