bl_info = {
    "name": "Nagato",
    "author": "Adesada J. Aderemi, Taiwo Folu",
    "version": (0, 5, 0),
    "blender": (2, 93, 0),
    "location": "View3D > Add > Mesh > New Object",
    "description": "Perform version control commands and project managements",
    "warning": "",
    "wiki_url": "",
    "category": "Version Control/Project Management",
}

modulesNames = ['svn', 'ui', 'kitsu', 'asset_browser', 'mixer']
import bpy
import sys
import importlib
from . import nagato_icon

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
    nagato_icon.init()
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'register'):
                sys.modules[currentModuleName].register()
    

 
def unregister():
    nagato_icon.clear()
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'unregister'):
                sys.modules[currentModuleName].unregister()
 
if __name__ == "__main__":
    register()
