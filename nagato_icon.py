import os
import bpy
import bpy.utils.previews

icons = ('update_file open_file resolve_conflict publish_file').split(' ')

icon_collection = {}


def icon(name):
    pcoll = icon_collection["main"]
    return pcoll[name].icon_id


def init():
    pcoll = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    for icon_name in icons:
        pcoll.load(icon_name, os.path.join(icons_dir, icon_name + '.png'), 'IMAGE')

    icon_collection["main"] = pcoll


def clear():
    for pcoll in icon_collection.values():
        bpy.utils.previews.remove(pcoll)
    icon_collection.clear()