from collections import defaultdict
import logging
import shutil
import time
import re
import os

import sublime_plugin
import sublime

from .poetry import Poetry, Venv
from .compat import VENV_BIN_DIR
from .utils import poetry_used, timed, flatten_dict
from .consts import (
    PACKAGE_NAME,
    POETRY_STATUS_BAR_TIMEOUT,
    ACTIVE_VERSION,
    CHOICE_SEPARATOR,
)
from .interpreters import PythonInterpreter
from .command_runner import PoetryThread, ThreadProgress
from .helpers import SimpleListInputHandler, titleise

LOG = logging.getLogger(PACKAGE_NAME)


class PoetryCommand(sublime_plugin.WindowCommand):
    def is_active(self):
        return poetry_used(self.window.active_view())

    is_enabled = is_active

    def run_poetry_command(
        self, command, *args, show_out=False, end_duration=POETRY_STATUS_BAR_TIMEOUT
    ):
        if not hasattr(self, "poetry"):
            self.poetry = Poetry(self.window)
        self.runner = PoetryThread(command, self.poetry, *args)
        self.runner.start()
        ThreadProgress(self.runner, show_out, end_duration)
        return self.runner

    def run_input_command(self, caption, command, initial="", custom=""):
        def to_run(res):
            self.run_poetry_command(command, res)

        if custom:
            self.run_poetry_command(command, custom)
        else:
            self.window.show_input_panel(
                caption, initial, lambda x: to_run(x), None, None
            )

    def run_after_command(self, fn, sleep):
        """run a  fn after checking after ThreadProgress end"""

        if not hasattr(self, "view"):
            self.view = self.window.active_view()

        def reloader():
            sublime.set_timeout_async(lambda: checker(fn, sleep), sleep)

        def checker(fn, sleep):
            if "succes" in self.view.get_status(PACKAGE_NAME):
                sublime.set_timeout_async(fn, 0)
                return
            if "fail" in self.view.get_status(PACKAGE_NAME):
                return
            reloader()

        reloader()

    # def wait_complete(self, fn):
    #     if self.runner.is_alive():
    #         sublime.set_timeout(lambda: self.wait(), 0.2)
    #     else:
    #         fn()

    def quick_status(self, message, timeout=POETRY_STATUS_BAR_TIMEOUT):
        if not hasattr(self, "view"):
            self.view = self.window.active_view()
        self.view = self.window.active_view()
        self.view.set_status(PACKAGE_NAME, message)
        sublime.set_timeout(lambda: self.view.erase_status(PACKAGE_NAME), timeout)

    def set_sb_version(self, version):
        print("set sb")
        if not hasattr(self, "view"):
            self.view = self.window.active_view()

        self.view.set_status(ACTIVE_VERSION, "Poetry: {}".format(version))


class PoetrySetPythonInterpreterCommand(PoetryCommand):
    def run(self):
        self.poetry = Poetry(self.window)
        sublime.set_timeout_async(self._run, 0)

    def _run(self):
        venv = self.poetry.used_venv()
        project = defaultdict(dict)
        project.update(self.window.project_data())
        prefix = ""

        if not venv:
            self.quick_status("Python Interpreter could not be set")
            if "python_interpreter" in project["settings"]:
                del project["settings"]["python_interpreter"]
            prefix = "No "

        else:
            python_interpreter = venv / VENV_BIN_DIR / "python"
            project["settings"]["python_interpreter"] = str(python_interpreter)

        self.window.set_project_data(project)
        self.quick_status(prefix + "python interpreter set")


class PoetryInstallCommand(PoetryCommand):
    def run(self):
        self.run_poetry_command("install")


class PoetryInstallNoDevCommand(PoetryCommand):
    def run(self):
        self.run_poetry_command("install --no-dev")


class PoetryUpdateCommand(PoetryCommand):
    def run(self):
        self.run_poetry_command("update")


class PoetryAddCommand(PoetryCommand):
    def run(self, custom="", package=None, dev=False):
        dev = "-D" if dev else ""
        cmd_line = "add {}".format(dev)
        if package:
            self.run_poetry_command(cmd_line, package)
        else:
            self.run_input_command(
                "Poetry {}".format(cmd_line), cmd_line, custom=custom
            )


class PoetryRemoveCommand(PoetryCommand):
    def remove_callback(self, id):
        choice = self.packages[id]
        dev = "-D" if "dev" in choice else ""
        package = choice.split()[0]

        self.run_poetry_command("remove", dev, package)

    def run(self, custom=""):
        self.poetry = Poetry(self.window)
        base, dev = self.poetry.packages
        dev_normalized = [
            " ".join((name, "   ", str(version), "  **dev** ")) for name, version in dev
        ]
        base_normalized = [
            " ".join((name, "   ", str(version)))
            for name, version in base
            if name != "python"
        ]

        self.packages = base_normalized + dev_normalized

        if custom:
            self.run_poetry_command("remove", custom)
        else:
            self.window.show_quick_panel(
                base_normalized + dev_normalized,
                lambda choice: self.remove_callback(choice),
            )


class PoetryEnvUseCommand(PoetryCommand):
    def run(self, choice):

        if choice in self.envs:
            # already know interpreters
            if "Activated" in choice:
                self.quick_status(choice + " nothing to do")
                return
            else:
                self.run_poetry_command("env use", choice[-3:])
        else:
            # not known interpreters
            self.run_poetry_command("env use", choice)

        self.run_after_command(
            lambda: self.window.run_command("poetry_set_python_interpreter"), 50
        )

    @property
    def all_envs(self):
        # poetry known envs
        self.envs = self.poetry.env_list

        # systems envs
        interpreters = []
        python_interpreter = PythonInterpreter()
        interpreters = [
            interpreter[0] for interpreter in python_interpreter.execs_and_pyenv
        ]

        # merge
        return (
            [titleise("available envs")]
            + self.envs
            + ["", titleise("available interpereters")]
            + interpreters
        )

    def input(self, args):
        self.poetry = Poetry(self.window)
        return SimpleListInputHandler(self.all_envs)


class PoetryEnvRemoveCommand(PoetryCommand):
    def run(self, choice):
        env = choice.split()[0]
        self.run_poetry_command("env remove", env)
        self.run_after_command(
            lambda: self.window.run_command("poetry_set_python_interpreter"), 100
        )

    def input(self, args):
        self.poetry = Poetry(self.window)
        envs = self.poetry.env_list
        if not envs:
            envs = [titleise("nothing to do")]
        return SimpleListInputHandler(envs)


class PoetryBuildCommand(PoetryCommand):
    def run(self):
        self.run_poetry_command("build")


class PoetryPublishCommand(PoetryCommand):
    def get_credential(self, target_repo):
        # then check fpr username and password
        for method, repos in self.poetry.auth.items():
            for repo, values in repos.items():
                if repo == target_repo:
                    return values["username"], values["password"]

        return None

    def run_publish(self, credos):
        if not credos:
            return
        else:
            cmd = ["publish"]
            if self.repo != "pypi":
                cmd.append("--repository={}".format(self.repo))

            cmd.append("--username={} --password={}".format(*credos))

            self.run_poetry_command(" ".join(cmd))

    def setup_publish(self, choice):
        if choice == "pypi":
            self.repo = choice
        elif choice == -1:
            return
        else:

            self.repo = self.repos[choice]

        LOG.debug("repos in poetry config %s", self.repo)

        credos = self.get_credential(self.repo)

        if not credos:
            self.window.show_input_panel(
                "username password",
                "",
                lambda x: self.run_publish(x.split()),
                None,
                self.run_publish(False),
            )
        else:
            self.run_publish(credos)

    def run(self):
        self.repo = None
        self.poetry = Poetry(self.window)
        # if many repo : choose repo
        self.repos = list(self.poetry.config["repositories"].keys())
        if self.repos:
            self.repos.insert(0, "pypi")

            self.window.show_quick_panel(
                self.repos, lambda choice: self.setup_publish(choice)
            )
        else:
            self.setup_publish("pypi")


class PoetryVersionCommand(PoetryCommand):
    def run(self, choice):
        LOG.debug("Bump version {}".format(choice))
        self.run_poetry_command(
            "version {}".format(choice), show_out=True, end_duration=3000
        )

    def input(self, args):
        self.poetry = Poetry(self.window)
        actions = "patch minor major prepatch preminor premajor prerelease".split()
        current = titleise("current {} ".format(self.poetry.package_version))
        actions.insert(0, current)
        return SimpleListInputHandler(actions)


class PoetryInitCommand(sublime_plugin.WindowCommand):
    def run(self):
        poetry = Poetry(self.window)
        runner = PoetryThread("init -n", poetry)
        runner.start()
        ThreadProgress(runner)


class PoetryConfigCommand(PoetryCommand):
    def input(self, args):
        self.poetry = Poetry(self.window)
        # creation ds choix : mise à plat clé valuer et on pass clé et value
        base = sorted(
            [
                ("{} : {}".format(x, y), (x, y))
                for x, y in flatten_dict(self.poetry.config).items()
            ]
        )

        fconfig = [titleise("Global Settings")]
        fconfig.extend([b for b in base if b[0].startswith("settings")])

        fconfig.append(titleise("Reposiories"))
        fconfig.extend([b for b in base if b[0].startswith("repositories")])

        fconfig.append(("Add new repository", ("repo", "+")))

        # Auth
        fconfig.append(titleise("Configure auth"))

        fconfig.extend(self.get_credentials())

        return SimpleListInputHandler(fconfig)

    def run(self, choice):
        self.choice = choice
        print(choice)
        if isinstance(self.choice[1], bool):
            self.configure_bool()

        elif isinstance(self.choice[1], str):
            if self.choice[1] == "+":
                self.configure_add_new_repo()
            else:
                self.configure_str()
        else:
            return
        # relance config quand terminer
        self.run_after_command(lambda: self.window.run_command("poetry_config"), 50)

    def configure_str(self):
        action = sublime.yes_no_cancel_dialog(self.choice[0], "Unset", "Modify")
        if action == 0:
            LOG.debug("update of %s cancelled", self.choice[0])
            return

        if action == 2:
            # start to
            self.choice[0] = self.choice[0].rstrip(".url")  # normalize if repo
            self.choice[1] = self.choice[1].strip()  # normalize if credo
            self.run_input_command(
                self.choice[0], "config {}".format(self.choice[0]), self.choice[1]
            ),

        elif action == 1:
            LOG.debug("unsetting %s", self.choice[0])
            self.run_poetry_command("config {} --unset".format(self.choice[0]))

    def configure_bool(self):
        res = not self.choice[1]
        self.run_poetry_command("config {} {}".format(self.choice[0], str(res).lower()))

    def configure_add_new_repo(self):
        self.run_input_command("New repository : repo.name url", "config", "repo.")

    def get_credentials(self):
        temp_repos = dict(self.poetry.config["repositories"])
        temp_repos.update(self.poetry.auth["http-basic"])

        new_repos = [
            [
                "http-basic." + k,
                [
                    "http-basic." + k,
                    " ".join([v.get("username", " "), v.get("password", " ")]),
                ],
            ]  # keep space to result not b false
            for k, v in temp_repos.items()
        ]
        if "pypi" not in temp_repos:
            new_repos.insert(0, ["http-basic.pypi", " "])
        return new_repos


class PoetrySearchCommand(PoetryCommand):
    def write_view(self):
        if not self.runner.poetry.popen.returncode:
            self.result = self.window.new_file()
            self.result.set_scratch(True)
            self.result.set_name("poetry_search_result")
            output = self.runner.output
            results = [i.strip() for i in output.splitlines()]
            self.result.run_command("insert", args={"characters": "\n".join(results)})

    def wait(self):
        if self.runner.is_alive():
            sublime.set_timeout(lambda: self.wait(), 0.2)
        else:
            self.write_view()

    def search(self, name):
        self.run_poetry_command("search -N {}".format(name))
        self.wait()

    def run(self):
        self.poetry = Poetry(self.window)
        self.window.show_input_panel("name", "", lambda x: self.search(x), None, None)


class PoetryAddPackageUnderCursorCommand(sublime_plugin.TextCommand):
    def is_active(self):
        return self.view.name() == "poetry_search_result"

    is_enabled = is_active

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.re_package = re.compile(r"([a-zA-Z0-9\-\_+]+) \(.+\)")

    def run(self, edit):
        line = self.view.substr(self.view.line(self.view.sel()[0]))
        to_find = self.re_package.search(line)
        if to_find:
            package = to_find.group(1)
        else:
            LOG.error("No matching package was found with line %s", line)
            return

        choice = sublime.yes_no_cancel_dialog(
            "Add package  {} to ?".format(package), "dev-dependencies", "dependencies"
        )

        if choice:
            dev = True if choice == 1 else False
            self.view.window().run_command(
                "poetry_add", args={"package": package, "dev": dev}
            )
        else:
            LOG.debug("Add package under cursor cancelled")


class PoetryShellCommand(PoetryCommand):
    def is_enabled(self):
        if not super().is_enabled():
            return False

        try:
            from Terminus import terminus  # noqa
        except ImportError:
            return False
        return True

    def is_active(self):
        if not super().is_active():
            return False

        try:
            from Terminus import terminus  # noqa
        except ImportError:
            return False
        return True

    def run(self):
        LOG.debug("Running Poetry Shell Command")
        self.poetry = Poetry(self.window)

        used_venv = self.poetry.used_venv()

        if used_venv is None:
            self.quick_status("No virtualenv installed, aborting")
            return

        activate = "activate"

        if self.poetry.platform != "windows":
            default_shell = os.environ["SHELL"]
            if "fish" in default_shell:
                activate += ".fish"
            if "csh" in default_shell:
                activate += ".csh"

        cmd_line = used_venv / VENV_BIN_DIR / activate

        if self.poetry.platform != "windows":
            cmd_line = ". {}\n".format(str(cmd_line))
        else:
            cmd_line = "{}\n".format(str(cmd_line))

        self.window.run_command(
            "terminus_open", {"config_name": "Default", "panel_name": "Poetry_shell"}
        )
        sublime.set_timeout(
            lambda: self.window.run_command(
                "terminus_send_string", {"string": cmd_line}
            )
        )
