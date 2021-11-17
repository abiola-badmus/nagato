bl_info = {
    "name": "Nagato",
    "author": "Adesada J. Aderemi, Taiwo Folu",
    "version": (0, 5, 1),
    "blender": (2, 93, 0),
    "location": "View3D > Add > Mesh > New Object",
    "description": "Perform version control commands and project managements",
    "warning": "",
    "wiki_url": "",
    "category": "Version Control/Project Management",
}


import bpy
import os
import sys
import importlib
from . import nagato_icon, profile, gazu, operators, ui
from .gazu.exception import NotAuthenticatedException
from bpy.app.handlers import persistent
NagatoProfile = profile.NagatoProfile

modulesNames = ['mixer', 'sequencer', 'auth', 'prefrecences','task_management', 'svn',]
modulesFullNames = {}

for currentModuleName in modulesNames:
    modulesFullNames[currentModuleName] = (f'{__name__}.{currentModuleName}') 
for currentModuleFullName in modulesFullNames.values():
    if currentModuleFullName in sys.modules:
        importlib.reload(sys.modules[currentModuleFullName])
    else:
        globals()[currentModuleFullName] = importlib.import_module(currentModuleFullName)
        setattr(globals()[currentModuleFullName], 'modulesNames', modulesFullNames)

@persistent
def create_main_collection(dummy):
    if 'main' not in bpy.data.collections.keys():
        collection = bpy.data.collections.new('main')
        bpy.context.scene.collection.children.link(collection)
    else:
        if bpy.data.collections['main'].name_full != 'main':
            collection = bpy.data.collections.new('main')
            bpy.context.scene.collection.children.link(collection)
    if 'main' not in bpy.data.scenes.keys():
        bpy.data.scenes.new('main')



def register():
    nagato_icon.init()
    profile.register()

    active_user_profile = NagatoProfile.read_json()
    if active_user_profile['login'] == True:
        try:
            gazu.client.set_tokens(active_user_profile)
            gazu.client.set_host(active_user_profile['host'])
            gazu.client.get_current_user()

            NagatoProfile.host = active_user_profile['host']
            NagatoProfile.login = active_user_profile['login']
            NagatoProfile.user = active_user_profile['user']
            NagatoProfile.access_token = active_user_profile['access_token']
            NagatoProfile.refresh_token = active_user_profile['refresh_token']
            NagatoProfile.ldap = active_user_profile['ldap']
        except NotAuthenticatedException:
            NagatoProfile.reset()
        except ConnectionError:
            NagatoProfile.reset()

    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'register'):
                sys.modules[currentModuleName].register()
    operators.register()
    ui.register()


    # bpy.app.handlers.depsgraph_update_pre.append(update_list)
    bpy.app.handlers.load_post.append(create_main_collection)
    # bpy.app.handlers.load_factory_preferences_post.append(load_handler)
    

 
def unregister():
    nagato_icon.clear()
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'unregister'):
                sys.modules[currentModuleName].unregister()
    operators.unregister()
    ui.unregister()
 
if __name__ == "__main__":
    register()
