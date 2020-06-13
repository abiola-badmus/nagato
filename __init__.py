bl_info = {
    "name": "Nagato",
    "author": "Adesada J. Aderemi, Taiwo Folu",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > New Object",
    "description": "Perform version control commands and project managements",
    "warning": "",
    "wiki_url": "",
    "category": "Version Control/Project Management",
}

modulesNames = ['svn', 'ui', 'kitsu']
import bpy
import sys
import importlib
import shutil
import ctypes


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# moves pysvn and gazu to blenders python directory
def move_dependecies():
    if is_admin():
        try:
            directory_pysvn = bpy.utils.script_path_user() + '/addons/nagato/pysvn'
            destination_pysvn = bpy.app.binary_path_python + '/../../lib/site-packages/pysvn'
            shutil.copytree(directory_pysvn, destination_pysvn)
        except FileExistsError:
            pass

        try:
            directory_gazu = bpy.utils.script_path_user() + '/addons/nagato/gazu'
            destination_gazu = bpy.app.binary_path_python + '/../../lib/site-packages/gazu'
            shutil.copytree(directory_gazu, destination_gazu)
        except FileExistsError:
            pass
    else:
        try:
            try:
                directory_pysvn = bpy.utils.script_path_user() + '/addons/nagato/pysvn'
                destination_pysvn = bpy.app.binary_path_python + '/../../lib/site-packages/pysvn'
                shutil.copytree(directory_pysvn, destination_pysvn)
            except FileExistsError:
                pass

            try:
                directory_gazu = bpy.utils.script_path_user() + '/addons/nagato/gazu'
                destination_gazu = bpy.app.binary_path_python + '/../../lib/site-packages/gazu'
                shutil.copytree(directory_gazu, destination_gazu)
            except FileExistsError:
                pass
        except PermissionError:
            loc = sys.executable
            py_loc = bpy.utils.script_path_user() + '/addons/nagato/util/activate.py'
            ctypes.windll.shell32.ShellExecuteW(None, "runas", loc, f'--python "{py_loc}"', None, 1)    
            exit()

move_dependecies()

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
    

 
def unregister():
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'unregister'):
                sys.modules[currentModuleName].unregister()
 
if __name__ == "__main__":
    register()