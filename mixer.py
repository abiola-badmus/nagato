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
from . import pysvn
from . import gazu
from . import kitsu, nagato_icon
from nagato.kitsu import NagatoProfile
import shutil


def process_exists(process_name):
    call = 'TASKLIST', '/FI', f'imagename eq {process_name}'
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
        # print(NagatoProfile.tasks)
        # subprocess.run(["taskkill","/F","/IM","Quixel Mixer.exe"])
        if process_exists('Quixel Mixer.exe'):
            self.report({'ERROR_INVALID_CONTEXT'}, "Mixer opened, You have to close mixer to run this operation") 
            return {"CANCELLED"}
        else:
            mixer_pref_path = context.preferences.addons['nagato'].preferences.mixer_pref_path

            mount_point = NagatoProfile.active_project['file_tree']['working']['mountpoint']
            root = NagatoProfile.active_project['file_tree']['working']['root']
            project_name = NagatoProfile.active_project['name'].replace(' ','_').lower()
            project_folder = os.path.expanduser(os.path.join(mount_point, root, project_name))

            mixer_project_folder = os.path.expanduser(os.path.join(project_folder, "lib", "mixer"))
            mixer_maps_folder = os.path.expanduser(os.path.join(project_folder, "lib", "maps"))
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
            mixer_mix_tree.find("ExportPath").text = mixer_maps_folder
            mix_custom_mesh_location = os.path.join(mixer_mix, "Custom Sources", f"{file_name}.fbx")
            bpy.ops.export_scene.fbx(filepath=mix_custom_mesh_location, use_selection=True, object_types={'MESH'})
            mixer_mix_tree.find("BaseLayer/MeshUIContext/CustomMeshPath").text = mix_custom_mesh_location
            mixer_mix_tree.find("BaseLayer/MeshUIContext/MeshType").text = "2"
            mixer_mix_tree.write(mixer_mix_xml)

            mixer_luncher = context.preferences.addons['nagato'].preferences.mixer_luncher
            mixer_dir = os.path.dirname(mixer_luncher)
            subprocess.Popen(mixer_luncher, cwd=mixer_dir)
            self.report({'INFO'}, "sent to mixer")
            return {"FINISHED"}


class NAGATO_OT_ImportTextures(Operator):
    bl_label = 'Add file to SVN'
    bl_idname = 'nagato.import_textures'
    bl_description = 'Add current file to project repository'
    
    # @classmethod
    # def poll(cls, context):
    #     return bool(NagatoProfile.user) and NagatoProfile.active_project != None


    def execute(self, context):
        file_name = bpy.path.basename(bpy.context.blend_data.filepath)[0:-6]
        mount_point = NagatoProfile.active_project['file_tree']['working']['mountpoint']
        root = NagatoProfile.active_project['file_tree']['working']['root']
        project_name = NagatoProfile.active_project['name'].replace(' ','_').lower()
        project_folder = os.path.expanduser(os.path.join(mount_point, root, project_name))

        mixer_project_folder = os.path.expanduser(os.path.join(project_folder, "lib", "mixer"))
        asset_maps_folder = os.path.expanduser(os.path.join(project_folder, "lib", "maps", file_name))
        mixer_project = os.path.join(mixer_project_folder, "Projects", project_name)

        images_location = asset_maps_folder
        images = os.listdir(images_location)
        material = bpy.data.materials.get(file_name)
        def set_textures(type, loc, image, input, output, main_node_name='Principled BSDF'):
            tex = material.node_tree.nodes.new(type)
            tex.hide = True
            tex.location = loc
            main_node = material.node_tree.nodes.get(main_node_name)
            material.node_tree.links.new(main_node.inputs[input], tex.outputs[output])
            if bool(image):
                tex.image = image
        for image_name in images:
            # print(image)
            image_path = os.path.join(images_location, image_name)
            image_type = image_name.rsplit('.', 1)[1]
            texture_type = image_name.rsplit('.', 1)[0].rsplit('_', 1)[1]
            name = image_name.rsplit('.', 1)[0].rsplit('_', 1)[0]
            image_data = bpy.data.images.load(image_path, check_existing=True)
            print(image_data)

            if texture_type in {"Albedo"}:
                image = bpy.data.images[image_name]
                set_textures('ShaderNodeTexImage', (-160.0, 320), image, input='Base Color', output="Color")
            elif texture_type in {"Metalness"}:
                image = bpy.data.images[image_name]
                image.colorspace_settings.name = 'Non-Color'
                set_textures('ShaderNodeTexImage', (-160.0, 240.0), image, input="Metallic", output="Color")
            elif texture_type in {"Roughness"}:
                image = bpy.data.images[image_name]
                image.colorspace_settings.name = 'Non-Color'
                set_textures('ShaderNodeTexImage', (-160.0, 160.0), image, input="Roughness", output="Color")
            elif texture_type in {"Normal"}:
                image = bpy.data.images[image_name]
                image.colorspace_settings.name = 'Non-Color'
                set_textures('ShaderNodeNormalMap', (-60.0, -120.0), None, input="Normal", output="Normal")
                set_textures('ShaderNodeTexImage', (-320.0, -120.0), image, input="Color", output="Color", main_node_name='Normal Map')
            # elif texture_type in {"Displacement"}:
            #     image = bpy.data.images['head 2_Metalness.png']
            #     set_textures(-160.0, 240.0, image, input="Metallic")
            # elif texture_type in {"AO"}:
            #     image = bpy.data.images['head 2_Metalness.png']
            #     set_textures(-160.0, 240.0, image, input="Metallic")

        



        # texture=bpy.data.textures.new('tex', 'IMAGE')
        # texture.use_nodes = True
        # texnodes = texture.node_tree.nodes

        # for m in bpy.data.materials:
        #     img = bpy.data.images.get(m.name)
        #     print(img)
        #     if not img:
        #         continue
        #     if m.use_nodes:
        #         # done this already??
        #         continue
        #     m.use_nodes = True

        #     nodes = m.node_tree.nodes
        #     bsdf = nodes.get('Diffuse BSDF')
        #     if bsdf:
        #         # add image texture
        #         teximage = nodes.new('ShaderNodeTexImage')
        #         teximage.image = img            
        #         #link to bsdf
        #         m.node_tree.links.new(bsdf.inputs['Color'], 
        #                 teximage.outputs['Color'])


        # bpy.data.materials['head 2'].node_tree.nodes.new(
        return {"FINISHED"}


############### all classes ####################    
classes = [
        NAGATO_OT_LunchMixer,
        NAGATO_OT_ImportTextures,
        ]  
    
    
# registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)   

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)  
