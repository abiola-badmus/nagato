bl_info = {
    "name": "Nagato",
    "author": "Adesada J. Aderemi, Taiwo Folu",
    "version": (2, 7),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > New Object",
    "description": "Perform version control commands and project managements",
    "warning": "",
    "wiki_url": "",
    "category": "Version Control/Project Management",
}

modulesNames = ['svn', 'panel', 'kitsu']
import bpy
import sys
import importlib
import shutil
 
modulesFullNames = {}
for currentModuleName in modulesNames:
    modulesFullNames[currentModuleName] = ('{}.{}'.format(__name__, currentModuleName))
 
for currentModuleFullName in modulesFullNames.values():
    if currentModuleFullName in sys.modules:
        importlib.reload(sys.modules[currentModuleFullName])
    else:
        globals()[currentModuleFullName] = importlib.import_module(currentModuleFullName)
        setattr(globals()[currentModuleFullName], 'modulesNames', modulesFullNames)
 
def register():
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'register'):
                sys.modules[currentModuleName].register()
    destination_pysvn = bpy.app.binary_path_python + '/../../lib/site-packages/pysvn'
    destination_gazu = bpy.app.binary_path_python + '/../../lib/site-packages/gazu'
    directory_pysvn = bpy.utils.script_path_user() + '/addons/nagato/pysvn'
    directory_gazu = bpy.utils.script_path_user() + '/addons/nagato/gazu'
    shutil.copytree(directory_pysvn, destination_pysvn)
    shutil.copytree(directory_gazu, destination_gazu)

 
def unregister():
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'unregister'):
                sys.modules[currentModuleName].unregister()
 
if __name__ == "__main__":
    register()