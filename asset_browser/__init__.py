import importlib
from . import operators, props


# ---------REGISTER ----------


def reload():
    global operators

    operators = importlib.reload(operators)


def register():
    operators.register()
    props.register()
    # ui.register()


def unregister():
    operators.unregister()
    props.unregister()
    # ui.unregister()