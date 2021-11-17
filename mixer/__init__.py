import importlib
from . import operators


# ---------REGISTER ----------


def reload():
    global operators

    operators = importlib.reload(operators)


def register():
    operators.register()
    # ui.register()


def unregister():
    operators.unregister()
    # ui.unregister()