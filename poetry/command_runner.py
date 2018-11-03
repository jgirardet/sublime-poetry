import threading
import sublime
import time
import logging

from .consts import PACKAGE_NAME
from .theme import flash_status_bar

LOG = logging.getLogger(PACKAGE_NAME)


class PoetryThread(threading.Thread):
    def __init__(self, command, poetry, output):
        threading.Thread.__init__(self)
        self.poetry = poetry
        self.command = command
        self.output = output

    def run(self):
        LOG.debug("starting %s", self.command)

        self.poetry.run(self.command)

        while self.poetry.poll is None:
            time.sleep(0.5)
        output = self.poetry.output
        self.output.put_nowait(output)
        LOG.debug("Output of command %s : %s", self.command, output.decode())
        # ThreadProgress(self, 'installing package', "installed")

        # self.output.task_done()


class ThreadProgress:

    """
    Animates an indicator, [=   ], in the status area while a thread runs
    :param thread:
        The thread to track for activity
    :param message:
        The message to display next to the activity indicator
    :param success_message:
        The message to display once the thread is complete

    code modified from github.com/wbond/package_control
    """

    def __init__(self, thread, success_message):
        self.thread = thread
        self.message = "Poetry " + thread.command
        self.success_message = self.message + " successful"
        self.failure_message = self.message + " fail"
        self.addend = 1
        self.size = 8
        self.last_view = None
        self.window = None
        sublime.set_timeout(lambda: self.run(0), 100)

    def run(self, i):

        if self.window is None:
            self.window = sublime.active_window()
        active_view = self.window.active_view()

        if self.last_view is not None and active_view != self.last_view:
            self.last_view.erase_status("PACKAGE_NAME")
            self.last_view = None

        settings = sublime.load_settings("Preferences.sublime-settings")
        if not settings.get("poetry_is_orange"):
            flash_status_bar("poetry_is_orange", toggle=True)

        if not self.thread.is_alive():

            def cleanup():
                active_view.erase_status("PACKAGE_NAME")

            cleanup()
            flash_status_bar("poetry_is_orange", toggle=True)
            if self.thread.poetry.popen.returncode == 0:
                active_view.set_status("PACKAGE_NAME", self.success_message)

                flash_status_bar("poetry_is_green")

            else:
                active_view.set_status("PACKAGE_NAME", self.failure_message)
                flash_status_bar("poetry_is_red")

            sublime.set_timeout(cleanup, 1000)

            return

        before = i % self.size
        after = (self.size - 1) - before

        active_view.set_status(
            "PACKAGE_NAME",
            "%s \u266c%s\u266c%s\u266c" % (self.message, " " * before, " " * after),
        )
        if self.last_view is None:
            self.last_view = active_view

        if not after:
            self.addend = -1
        if not before:
            self.addend = 1
        i += self.addend

        sublime.set_timeout(lambda: self.run(i), 100)
