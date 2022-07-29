import pathlib
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import json
import subprocess

from git import Repo

REPO_NAMES = [
    "vector-im/element-builder",
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
    print("Scanning", repo.working_dir)

    by_extension = defaultdict(int)
    res = subprocess.run(
        f"sloc --format cli-table --exclude modernizr.js --keys source --format-option no-head {repo.working_dir}/src",
        stdout=subprocess.PIPE,
        # stderr=subprocess.STDOUT,
        shell=True,
        cwd=repo.working_dir)

    print(res.stdout.decode("utf-8"))

    for line in res.stdout.splitlines():
        l = line.decode("utf-8")[2:-2]
        r = regex.match(l)
        if not r:
            continue

        by_extension[r.group(1)] += int(r.group(2))

    res = subprocess.run(
        'tsc --strict --pretty false | grep "error" | wc -l',
        stdout=subprocess.PIPE,
        # stderr=subprocess.STDOUT,
        shell=True,
        cwd=repo.working_dir)

    print(res.stdout.decode("utf-8"))

    return by_extension, int(res.stdout.strip().decode("utf-8"))


REPOS = list(map(get_repo, REPO_NAMES))

results = []
for i, repo in enumerate(REPOS):
    commit = repo.head.commit
    by_extension, error_count = scan(repo)

    print(commit, error_count, by_extension)

    results.append((dict(by_extension), error_count))

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
        *x,
    ) for i, x in enumerate(results)],
))

sorted(existing_data, key=lambda x: x[0])

with open("results.json", "w") as f:
    json.dump(existing_data, f, indent=4)
