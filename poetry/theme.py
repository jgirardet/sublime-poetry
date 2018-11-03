"""
theme tweaker from https://github.com/kaste/pytest
"""

import sublime

import os
import re


POETRY_MARKERS = re.compile(r'poetry_is_(red|green|orange)')


POETRY_RULES = [
    {
        "class": "status_bar",
        "settings": ["poetry_is_green"],
        # "layer0.tint": [73, 242, 115],
        "layer0.tint": [0, 255, 64],
    },
    {
        "class": "label_control",
        "settings": ["poetry_is_green"],
        "parents": [{"class": "status_bar"}],
        # "color": [0, 255, 64],
        "color": [19, 21, 32],
    },
    {
        "class": "status_bar",
        "settings": ["poetry_is_red"],
        "layer0.tint": [155, 7, 8],
    },
    {
        "class": "label_control",
        "settings": ["poetry_is_red"],
        "parents": [{"class": "status_bar"}],
        "color": [199, 191, 192],
    },    
    {
        "class": "status_bar",
        "settings": ["poetry_is_orange"],
        "layer0.tint": [230, 106, 23],
    },
    {
        "class": "label_control",
        "settings": ["poetry_is_orange"],
        "parents": [{"class": "status_bar"}],
        "color": [240, 155, 98],
    },

]

def tweak_theme():
    view = sublime.active_window().active_view()
    if not view:
        return

    theme = view.settings().get('theme')
    if theme is None:
        print("Can't guess current theme.")
        return

    theme_path = os.path.join(sublime.packages_path(), 'User', theme)
    if os.path.exists(theme_path):
        with open(theme_path, mode='r', encoding='utf-8') as f:
            theme_text = f.read()

        if POETRY_MARKERS.search(theme_text):
            return

        safety_path = os.path.join(
            sublime.packages_path(), 'User', 'Original-' + theme)
        with open(safety_path, mode='w', encoding='utf-8') as f:
            f.write(theme_text)

        theme = sublime.decode_value(theme_text)
    else:
        theme = []

    theme.extend(POETRY_RULES)

    tweaked_theme = sublime.encode_value(theme, True)
    with open(theme_path, mode='w', encoding='utf-8') as f:
        f.write(tweaked_theme)

    print("Poetry: Done tweaking '{}'!".format(theme_path))


def flash_status_bar(flag, ms=1000, toggle=False):
    settings = sublime.load_settings('Preferences.sublime-settings')
    settings.set(flag, not settings.get(flag))

    if toggle is not True:
        sublime.set_timeout(lambda: settings.erase(flag), ms)
