from collections import defaultdict
import logging
import shutil
import time

import sublime_plugin
import sublime

from .poetry import Poetry, Venv
from .compat import VENV_BIN_DIR
from .utils import poetry_used, timed, flatten_dict
from .consts import PACKAGE_NAME, POETRY_STATUS_BAR_TIMEOUT
from .interpreters import PythonInterpreter
from .command_runner import PoetryThread, ThreadProgress

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
        runner = PoetryThread(command, self.poetry, *args)
        runner.start()
        ThreadProgress(runner, show_out, end_duration)

    def run_input_command(self, caption, command, initial="", custom=""):
        def to_run(res):
            self.run_poetry_command(command, res)

        if custom:
            self.run_poetry_command(command, custom)
        else:
            self.window.show_input_panel(
                caption, initial, lambda x: to_run(x), None, None
            )


class PoetrySetPythonInterpreterCommand(PoetryCommand):
    def run(self):
        self.poetry = Poetry(self.window)
        sublime.set_timeout_async(self._run, 0)

    def _run(self):

        project = defaultdict(dict)
        project.update(self.window.project_data())
        python_interpreter = self.poetry.used_venv() / VENV_BIN_DIR / "python"

        project["settings"]["python_interpreter"] = str(python_interpreter)

        self.window.set_project_data(project)
        view = self.window.active_view()
        view.set_status(PACKAGE_NAME, "python interpreter set !")
        sublime.set_timeout(
            lambda: view.erase_status(PACKAGE_NAME), POETRY_STATUS_BAR_TIMEOUT
        )


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
    def run(self, custom=""):
        self.run_input_command("Poetry add", "add", custom)


class PoetryAddDevCommand(PoetryCommand):
    def run(self, custom=""):
        self.run_input_command("Poetry add", "add -D", custom)


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


class PoetryInstallInVenvCommand(PoetryCommand):
    def create_and_install(self, path, version):
        new_venv = Venv.create(path, version, self.poetry.cwd)

        self.window.run_command("poetry_install")

    def callback(self, id):
        path, version = self.python_interpreter.execs_and_pyenv[id]
        LOG.debug("using %s with version %s", path, version)
        LOG.debug("current .venv version : %s", self.poetry.venv.version)
        if version == self.poetry.venv.version:
            LOG.debug("version in .venv is the same as selected")
            go_on = sublime.ok_cancel_dialog(
                ".venv is already with version {}. Continue ?".format(version)
            )
            if not go_on:
                LOG.debug("Install command interupted by user")
                return

        print(self.poetry.venv)
        if self.poetry.venv.exists():
            LOG.debug("Removing old .venv")
            shutil.rmtree(str(self.poetry.venv))
        else:
            LOG.debug(".venv doesn not exists")

        sublime.set_timeout_async(lambda: self.create_and_install(path, version), 0)

    def run(self):
        self.poetry = Poetry(self.window)
        self.interpreters = []
        self.python_interpreter = PythonInterpreter()
        for i in self.python_interpreter.execs_and_pyenv:
            self.interpreters.append("{}  {}".format(*i))

        self.window.show_quick_panel(
            self.interpreters, lambda choice: self.callback(choice)
        )


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
    def _run_version(self, choice):
        if choice == -1 or choice == 0:
            LOG.debug("Bump version cancelled")
            return
        selected = self.actions[choice]
        LOG.debug("Bump version {}".format(selected))
        self.run_poetry_command(
            "version {}".format(selected), show_out=True, end_duration=3000
        )

    def run(self):
        self.poetry = Poetry(self.window)
        self.actions = "patch minor major prepatch preminor premajor prerelease".split()
        current = "current {}".format(self.poetry.package_version)
        self.actions.insert(0, current)
        self.window.show_quick_panel(
            self.actions,
            lambda choice: self._run_version(choice),
            sublime.MONOSPACE_FONT,
        )


class PoetryInitCommand(sublime_plugin.WindowCommand):
    def run(self):
        poetry = Poetry(self.window)
        runner = PoetryThread("init -n", poetry)
        runner.start()
        ThreadProgress(runner)


class PoetryConfigCommand(PoetryCommand):

    CB_SLEEP = 50

    def run_after_command(self, command, sleep):
        """run a window command checking after ThreadProgress end"""

        def reloader():
            sublime.set_timeout_async(lambda: checker(command, sleep), sleep)

        def checker(command, sleep):
            if "succes" in self.view.get_status(PACKAGE_NAME):
                sublime.set_timeout_async(lambda: self.window.run_command(command), 0)
                return
            if "fail" in self.view.get_status(PACKAGE_NAME):
                return
            reloader()

        reloader()

    @staticmethod
    def do_repo_credentials_list(repos):
        new_repos = [
            [k, " ".join((v.get("username", ""), v.get("password", ""))).strip()]
            for k, v in repos.items()
        ]
        if "pypi" not in repos:
            new_repos.insert(0, ["pypi", ""])
        print(new_repos)
        return new_repos

    def _run_credentials_command(self, x, choice):
        print("debut run cred")
        cmd = "config http-basic.{}".format(self.repos_auth_list[choice][0])
        if not x:
            self.run_poetry_command(cmd, "--unset")

        else:
            self.run_poetry_command(cmd, x)

    def _callback_credentials(self, choice):

        if choice == -1:
            LOG.debug("configure credentials cancelled")
            return

        print("vant input")
        self.window.show_input_panel(
            "username password (blank to unset)",
            "{}".format(self.repos_auth_list[choice][1]),
            lambda x: self._run_credentials_command(x, choice),
            None,
            None,
        )

    def dispatch(self, choice):
        if choice == -1:
            return
        key, res = self.fconfig_type[choice]
        LOG.debug("key: %s   res: %s", key, res)

        print("ici")
        if res == "+":
            self.run_input_command("New repository : repo.name url", "config", "repo.")

        elif res == "?":
            print("call it")
            self.window.show_quick_panel(
                self.repos_auth_list,
                lambda choice: self._callback_credentials(choice),
                sublime.MONOSPACE_FONT,
            )

        # for toggle boolean
        elif isinstance(res, bool):
            res = not res
            LOG.debug("{}update of %s cancelled", key)
            self.run_poetry_command("config {} {}".format(key, str(res).lower()))

        # unset or modify string
        elif isinstance(res, str):
            choice = sublime.yes_no_cancel_dialog(key, "Unset", "Modify")
            if choice == 0:
                LOG.debug("update of %s cancelled", key)
                return

            if choice == 2:
                LOG.debug("updating %s", key)
                self.run_input_command(key, "config {}".format(key), res),

            elif choice == 1:
                LOG.debug("unsetting %s", key)
                self.run_poetry_command("config {} --unset".format(key))

        else:
            LOG.error("unkwon")

        self.run_after_command("poetry_config", self.CB_SLEEP)

    def run(self):
        self.poetry = Poetry(self.window)
        self.view = self.window.active_view()

        self.base_config = self.poetry.config

        # quick_panel anly accept list of string and to keep boolean type
        self.fconfig_str = sorted(
            [[x, str(y)] for x, y in flatten_dict(self.base_config).items()]
        )
        self.fconfig_type = sorted(
            [[x, y] for x, y in flatten_dict(self.base_config).items()]
        )

        # append commands
        for l in [self.fconfig_str, self.fconfig_type]:
            l.append(("Add a new repository", "+"))
            l.append(("Configure credentials", "?"))

        # configure repo list for credential config
        temp_repos = dict(self.base_config["repositories"])
        temp_repos.update(self.poetry.auth["http-basic"])
        self.repos_auth_list = self.do_repo_credentials_list(temp_repos)

        # run the process
        self.window.show_quick_panel(
            self.fconfig_str,
            lambda choice: self.dispatch(choice),
            sublime.MONOSPACE_FONT,
            sublime.KEEP_OPEN_ON_FOCUS_LOST,
        )
