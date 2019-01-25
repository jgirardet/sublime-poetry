from .helpers import Poetry, PoetryCommand, titleise, SimpleListInputHandler
from ..consts import PACKAGE_NAME
import logging

LOG = logging.getLogger(PACKAGE_NAME)


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
