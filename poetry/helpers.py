import sublime_plugin
from .consts import CHOICE_SEPARATOR


class SimpleListInputHandler(sublime_plugin.ListInputHandler):
    def __init__(self, items):
        self.items = items

    def list_items(self):
        return self.items

    def name(self):
        return "choice"

    def validate(self, value):
        if isinstance(value, list):
            return True

        elif not value or value.startswith(CHOICE_SEPARATOR):
            return False
        return True


def titleise(title):
    return " ".join((CHOICE_SEPARATOR, title.strip(), CHOICE_SEPARATOR))