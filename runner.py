import ansible_runner

from pathlib import Path
from git import Repo


class GitRunner:
    def __init__(self, repo_url, repo_dir=None, workdir="."):
        self.repo_url = repo_url
        self.workdir = Path(workdir)
        if repo_dir is None:
            repo_dir = repo_url.split("/")[-1]
        self.repo_dir = self.workdir / Path(repo_dir)

    def updateRepository(self, ref="origin/HEAD"):
        if self.repo_dir.is_dir():
            repo = Repo(self.repo_dir)
        else:
            repo = Repo.clone_from(self.repo_url, self.repo_dir)

        remote = repo.remotes.origin
        remote.update()
        repo.git.reset('--hard', repo.refs[ref])

    def run(self, playbook, ref='origin/HEAD', update=True, limit=None):
        if update:
            self.updateRepository(ref=ref)

        if limit:
            limit_arg = ','.join(limit)
        else:
            limit_arg = None

        res = ansible_runner.run(
                envvars={'ANSIBLE_NOCOLOR': '1'},
                private_data_dir=str(self.repo_dir),
                playbook=playbook,
                limit=limit_arg,
                )

        return res
