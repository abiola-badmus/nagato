import importlib
from . import operators, ui, props


# ---------REGISTER ----------


def reload():
    global operators

    operators = importlib.reload(operators)


def register():
    operators.register()
    ui.register()
    props.register()


def unregister():
    operators.unregister()
    ui.unregister()
    props.unregister()