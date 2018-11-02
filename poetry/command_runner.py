import threading
import sublime


class PoetryThread(threading.Thread):
    def __init__(self, poetry, command):
        self.poetry = poetry
        self.command = command

        threading.Thread__init__(self)

    def run(self):

        self.poetry.run(self.command)

        try:
            self.result = self.poetry.run(self.command)
        except Exception:
            self.result = False
            raise
