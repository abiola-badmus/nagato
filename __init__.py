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

modulesNames = ['svn', 'ui', 'kitsu', 'asset_browser']
import bpy
import sys
import importlib
import shutil
import ctypes
import filecmp
import os.path


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# moves pysvn and gazu to blenders python directory
def are_dir_trees_equal(dir1, dir2):
    """
    Compare two directories recursively. Files in each directory are
    assumed to be equal if their names and contents are equal.

    @param dir1: First directory path
    @param dir2: Second directory path

    @return: True if the directory trees are the same and 
        there were no errors while accessing the directories or files, 
        False otherwise.
   """
    print('runing')
    dirs_cmp = filecmp.dircmp(dir1, dir2)
    if len(dirs_cmp.left_only)>0 or len(dirs_cmp.right_only)>0 or \
        len(dirs_cmp.funny_files)>0:
        return False
    (_, mismatch, errors) =  filecmp.cmpfiles(
        dir1, dir2, dirs_cmp.common_files, shallow=False)
    if len(mismatch)>0 or len(errors)>0:
        return False
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if not are_dir_trees_equal(new_dir1, new_dir2):
            return False
    return True


def dependecy(directory, destination):
    try:
        if are_dir_trees_equal(directory, destination) is False:
            shutil.rmtree(destination)
            shutil.copytree(directory, destination)
    except FileNotFoundError:
        shutil.copytree(directory, destination)


def move_dependecies():
    directory_pysvn = bpy.utils.script_path_user() + '/addons/nagato/pysvn'
    destination_pysvn = bpy.app.binary_path_python + '/../../lib/site-packages/pysvn'
    directory_gazu = bpy.utils.script_path_user() + '/addons/nagato/gazu'
    destination_gazu = bpy.app.binary_path_python + '/../../lib/site-packages/gazu'
    if is_admin():
        dependecy(directory_pysvn, destination_pysvn)
        dependecy(directory_gazu, destination_gazu)
    else:
        try:
            dependecy(directory_pysvn, destination_pysvn)
            dependecy(directory_gazu, destination_gazu)
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