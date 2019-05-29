from .helpers import Poetry, PoetryCommand, titleise, SimpleListInputHandler
import sublime
from ..utils import flatten_dict
from ..consts import PACKAGE_NAME
import logging

LOG = logging.getLogger(PACKAGE_NAME)


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

        fconfig.append(titleise("Repositories"))
        fconfig.extend([b for b in base if b[0].startswith("repositories")])

        fconfig.append(("Add new repository", ("repo", "+")))

        # Auth
        fconfig.append(titleise("Configure auth"))

        fconfig.extend(self.get_credentials())

        return SimpleListInputHandler(fconfig)

    def run(self, choice):
        self.choice = choice
        print("|", choice, "|")
        # if choice == " ":
        #     self.choice == ("","")
        #     self.configure_str()

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
            self.run_poetry_command(
                "config --unset {} ".format(self.choice[0].rstrip(".url"))
            )

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
            new_repos.insert(0, ["http-basic.pypi", ["http-basic.pypi", " "]])
        print(new_repos)
        return new_repos
