"""

Poem

Order of imports should not be changed
"""
import logging
import sublime
import os

from .poem import PACKAGE_NAME#, get_settings, PoemSetPythonInterpreterCommand  # flake8: noqa


LOG = logging.getLogger(PACKAGE_NAME)

if not os.environ.get("CI", None):
    LOG.propagate = False


# def plugin_loaded():
#     # load config
#     current_view = sublime.active_window().active_view()
#     config = get_settings(current_view)

#     # Setup  logging
#     if not LOG.handlers:
#         debug_formatter = logging.Formatter(
#             "[{}:%(filename)s](%(levelname)s) %(message)s".format(PACKAGE_NAME)
#         )
#         dh = logging.StreamHandler()
#         dh.setLevel(logging.DEBUG)
#         dh.setFormatter(debug_formatter)
#         LOG.addHandler(dh)

#     try:
#         LOG.setLevel(config.get("poem_log", "").upper())
#     except ValueError as err:
#         LOG.error(err)
#         LOG.setLevel("ERROR")
#         LOG.error("fallback to loglevel ERROR")

#     LOG.info("Loglevel set to %s", config["poem_log"].upper())
