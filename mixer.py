import bpy
from bpy.types import (
    Operator,
    Panel,
    AddonPreferences,
    PropertyGroup,
    Menu
)
from bpy.props import (StringProperty)
# import winapps
import os
import subprocess
import xml.etree.ElementTree as ET
import pysvn
import gazu
from . import kitsu, nagato_icon
from nagato.kitsu import NagatoProfile
import shutil


def process_exists(process_name):
    call = 'TASKLIST', '/FI', 'imagename eq %s' % process_name
    # use buildin check_output right away
    output = subprocess.check_output(call).decode()
    # check in last line for process name
    last_line = output.strip().split('\r\n')[-1]
    # because Fail message could be translated
    return last_line.lower().startswith(process_name.lower())

########## operators ################################
client = pysvn.Client()

class NAGATO_OT_LunchMixer(Operator):
    bl_label = 'Add file to SVN'
    bl_idname = 'nagato.lunch_mixer'
    bl_description = 'Add current file to project repository'
    
    @classmethod
    def poll(cls, context):
        return bool(NagatoProfile.user) and NagatoProfile.active_project != None


    def execute(self, context):
        subprocess.run(["taskkill","/F","/IM","Quixel Mixer.exe"])
        while process_exists('Quixel Mixer.exe'):
            pass  
        mixer_pref_path = "C:/Users/Itadori/AppData/Roaming/Quixel/Quixel Mixer/Settings/MixerPrefs.xml"

        mount_point = NagatoProfile.active_project['file_tree']['working']['mountpoint']
        root = NagatoProfile.active_project['file_tree']['working']['root']
        project_name = NagatoProfile.active_project['name'].replace(' ','_').lower()
        project_folder = os.path.expanduser(os.path.join(mount_point, root, project_name))

        mixer_project_folder = os.path.expanduser(os.path.join(project_folder, "lib", "mixer"))
        mixer_project = os.path.join(mixer_project_folder, "Projects", project_name)
        file_name = bpy.path.basename(bpy.context.blend_data.filepath)[0:-6]
        mixer_mix = os.path.join(mixer_project, file_name)
        mixer_mix_xml = os.path.join(mixer_mix, f"{file_name}.xml")

        os.makedirs(mixer_project, exist_ok=True)
        mix_template_dir = os.path.join(os.path.dirname(__file__), 'mix_template')
        if not os.path.isdir(mixer_mix):
            shutil.copytree(mix_template_dir, mixer_mix)
        if not os.path.isfile(mixer_mix_xml):
            os.rename(os.path.join(mixer_mix, "template.xml"), mixer_mix_xml)
        
        mixer_pref_tree = ET.parse(mixer_pref_path)
        mixer_pref_tree.find("MixerFilesFolderPath").text = mixer_project_folder
        mixer_pref_tree.write(mixer_pref_path)

        mixer_mix_tree = ET.parse(mixer_mix_xml)
        mixer_mix_tree.find("ProjectName").text = file_name
        mixer_mix_tree.find("FoundPath").text = mixer_mix_xml
        mix_custom_mesh_location = os.path.join(mixer_mix, "Custom Sources", f"{file_name}.fbx")
        bpy.ops.export_scene.fbx(filepath=mix_custom_mesh_location, use_selection=True, object_types={'MESH'})
        mixer_mix_tree.find("BaseLayer/MeshUIContext/CustomMeshPath").text = mix_custom_mesh_location
        mixer_mix_tree.find("BaseLayer/MeshUIContext/MeshType").text = "2"
        mixer_mix_tree.write(mixer_mix_xml)

        

        # for item in winapps.search_installed('Quixel Mixer'):
        #     if item.name in ('Quixel Mixer'):
        #         mixer_install_location = item.install_location
        #         mixer_luncher = os.path.join(mixer_install_location, 'Quixel Mixer.exe')
        mixer_luncher ='C:/Users/Itadori/Eaxum/Software/Quixel/QuixelMixer-2021.1.1/Quixel Mixer.exe'

        print(mixer_luncher)
        subprocess.Popen(mixer_luncher, cwd="C:/Users/Itadori/Eaxum/Software/Quixel/QuixelMixer-2021.1.1")
        self.report({'WARNING'}, "completed")
        return {"FINISHED"}


############### all classes ####################    
classes = [
        NAGATO_OT_LunchMixer,
        ]  
    
    
# registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)   

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)  
