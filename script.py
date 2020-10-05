import pathlib
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import json
import subprocess

from git import Repo

REPO_NAMES = [
    "vector-im/element-desktop",
    "vector-im/element-web",
    "matrix-org/matrix-react-sdk",
    "matrix-org/matrix-js-sdk",
]

day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

BASE_PATH = Path("./repos")

regex = re.compile(r"(\w+).+?(\d+)")


def get_repo(repo_name):
    path = BASE_PATH / repo_name
    try:
        pathlib.Path(path).mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        pass
    else:
        Repo.clone_from(f"https://github.com/{repo_name}", path)

    return Repo(path)


def scan(repo):
    args = [
        "sloc", f"{repo.working_dir}/src",
        "--format", "cli-table",
        "--keys", "source",
        "--format-option", "no-head",
    ]
    print("Scanning", repo.working_dir)

    by_extension = defaultdict(int)
    try:
        res = subprocess.run(
            args,
            capture_output=True,
            shell=True,
            cwd=repo.working_dir)

        for line in res.stdout.splitlines():
            l = line.decode("utf-8")[2:-2]
            r = regex.match(l)
            if not r:
                continue

            # print(l)
            # print(r.groups())

            by_extension[r.group(1)] += int(r.group(2))
    except FileNotFoundError as not_found:
        print("FileNotFoundError", repo.working_dir, not_found.filename, not_found.filename2)

    return by_extension


REPOS = list(map(get_repo, REPO_NAMES))

results = []
for i, repo in enumerate(REPOS):
    repo.remotes[0].pull()

    commit = repo.head.commit
    result = scan(repo)

    print(commit, result)

    results.append(dict(result))

with open("results.json", "r+") as f:
    try:
        existing_data = json.load(f) or []
    except:
        existing_data = []

existing_data.append((
    str(day.date()),
    [(
        REPO_NAMES[i],
        REPOS[i].head.commit.hexsha,
        x,
    ) for i, x in enumerate(results)],
))

with open("results.json", "w") as f:
    f.write(json.dumps(existing_data, indent=4))
