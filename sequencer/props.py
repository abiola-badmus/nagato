import bpy


class KITSU_property_group_sequence(bpy.types.PropertyGroup):
    """
    Property group that will be registered on sequence strips.
    They hold metadata that will be used to compose a data structure that can
    be pushed to backend.
    """

    # def _get_shot_description(self):
    #     return self.shot_description

    # def _get_sequence_name(self):
    #     return self.sequence_name

    # shot
    shot_id: bpy.props.StringProperty(name="Shot ID")  # type: ignore
    shot_name: bpy.props.StringProperty(name="Shot", default="")  # type: ignore
    shot_description: bpy.props.StringProperty(name="Description", default="", options={"HIDDEN"})  # type: ignore

    # sequence
    sequence_name: bpy.props.StringProperty(name="Sequence", default="")  # type: ignore
    sequence_id: bpy.props.StringProperty(name="Seq ID", default="")  # type: ignore

    # project
    project_name: bpy.props.StringProperty(name="Project", default="")  # type: ignore
    project_id: bpy.props.StringProperty(name="Project ID", default="")  # type: ignore

    # meta
    # initialized: bpy.props.BoolProperty(  # type: ignore
    #     name="Initialized", default=False, description="Is Kitsu shot"
    # )
    linked: bpy.props.BoolProperty(  # type: ignore
        name="Linked", default=False, description="Is linked to an ID on server"
    )

    # frame range
    # frame_start_offset: bpy.props.IntProperty(name="Frame Start Offset")

    # media
    # media_outdated: bpy.props.BoolProperty(
    #     name="Source Media Outdated",
    #     default=False,
    #     description="Indicated if there is a newer version of the source media available",
    # )

    # display props
    # shot_description_display: bpy.props.StringProperty(name="Description", get=_get_shot_description)  # type: ignore
    # sequence_name_display: bpy.props.StringProperty(name="Sequence", get=_get_sequence_name)  # type: ignore

    # def to_dict(self):
    #     return {
    #         "id": self.id,
    #         "name": self.shot,
    #         "sequence_name": self.sequence,
    #         "description": self.description,
    #     }

    # def clear(self):
    #     self.shot_id = ""
    #     self.shot_name = ""
    #     self.shot_description = ""

    #     self.sequence_id = ""
    #     self.sequence_name = ""

    #     self.project_name = ""
    #     self.project_id = ""

    #     self.initialized = False
    #     self.linked = False

    #     self.frame_start_offset = 0

    # def unlink(self):
    #     self.sequence_id = ""

    #     self.project_name = ""
    #     self.project_id = ""

    #     self.linked = False

classes = [
    KITSU_property_group_sequence,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Sequence.kitsu = bpy.props.PointerProperty(
        name="Kitsu",
        type=KITSU_property_group_sequence,
        description="Metadata that is required for blender_kitsu",
    )

    bpy.types.Scene.render_type = bpy.props.EnumProperty(
                                        items=[('play_blast', 'play_blast', 'play_blast'),
                                                ('look_dev', 'look_dev', 'look_dev'),
                                                ('previz', 'previz', 'previz'),
                                                ],
                                        #update=update_render_type)
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Sequence.kitsu
    del bpy.types.Scene.render_type
