import threading
import sublime
import time
import logging

from ..consts import PACKAGE_NAME, POETRY_STATUS_BAR_TIMEOUT
from ..theme import flash_status_bar

LOG = logging.getLogger(PACKAGE_NAME)


class PoetryThread(threading.Thread):
    def __init__(self, command, poetry, *args):
        threading.Thread.__init__(self)
        self.poetry = poetry
        args = list(args)
        args.insert(0, command)
        self.command = " ".join(args)

    def run(self):
        LOG.debug("starting %s", self.command)

        self.poetry.run(self.command)

        while self.poetry.poll is None:
            time.sleep(0.5)

        self.output = self.poetry.output.decode()

        if self.poetry.popen.returncode == 0:
            LOG.debug("Output of command %s : %s", self.command, self.output)
        else:
            LOG.error("Output of command %s : %s", self.command, self.output)
            panel = self.poetry.window.get_output_panel("poetry")
            characters = "POETRY ERROR LOG\n\n" + self.output
            panel.run_command("append", args={"characters": characters})
            self.poetry.window.run_command(
                "show_panel", args={"panel": "output.poetry"}
            )


class ThreadProgress:

    """
    Animates an indicator, [=   ], in the status area while a thread runs
    :param thread:
        The thread to track for activity

    code modified from github.com/wbond/package_control
    """

    def __init__(self, thread, show_out=False, end_duration=POETRY_STATUS_BAR_TIMEOUT):
        self.thread = thread
        self.show_out = show_out
        self.end_duration = end_duration
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
        self.active_view = self.window.active_view()

        if self.last_view is not None and self.active_view != self.last_view:
            self.last_view.erase_status(PACKAGE_NAME)
            self.last_view = None

        flash_status_bar("poetry_is_orange", "show")
        flash_status_bar("poetry_is_red", "hide")
        flash_status_bar("poetry_is_green", "hide")
        self.active_view.erase_status(PACKAGE_NAME)

        self.waiting(i)

    def waiting(self, i):
        """Animation during wainting"""

        if not self.thread.is_alive():
            self.exit()
            return

        before = i % self.size
        after = (self.size - 1) - before

        self.active_view.set_status(
            PACKAGE_NAME,
            "%s \u266c%s\u266c%s\u266c" % (self.message, " " * before, " " * after),
        )
        if self.last_view is None:
            self.last_view = self.active_view

        if not after:
            self.addend = -1
        if not before:
            self.addend = 1
        i += self.addend

        sublime.set_timeout_async(lambda: self.waiting(i), 100)

    def exit(self):
        """do at exit"""

        def cleanup():
            self.active_view.erase_status(PACKAGE_NAME)

        cleanup()
        flash_status_bar("poetry_is_orange", "hide")
        if self.thread.poetry.popen.returncode == 0:
            if self.show_out:
                self.success_message = self.success_message + " " + self.thread.output
            self.active_view.set_status(PACKAGE_NAME, self.success_message)

            flash_status_bar("poetry_is_green")

        else:
            self.active_view.set_status(PACKAGE_NAME, self.failure_message)
            flash_status_bar("poetry_is_red")

        sublime.set_timeout(cleanup, self.end_duration)
