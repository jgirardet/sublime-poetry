import threading
import sublime
import time
import logging

from .consts import PACKAGE_NAME

LOG = logging.getLogger(PACKAGE_NAME)


class PoetryThread(threading.Thread):
    def __init__(self, command, poetry, output):
        threading.Thread.__init__(self)
        self.poetry = poetry
        self.command = command
        self.output = output


    def run(self):
        LOG.debug('starting %s', self.command)

        self.poetry.run(self.command)

        while self.poetry.poll is None:
            time.sleep(0.5)
        output  = self.poetry.output
        self.output.put_nowait(output)
        LOG.debug("Output of command %s : %s",self.command,  output.decode())

        # self.output.task_done()
