from github import Github
import json
import random

# For this to work, you need to provide an API key with write
# permission (in a file fme_github_keys.py and var fme_github_key)
from fme_github_keys import fme_github_key

# Github repository with course data
courses_repo = 'fme-teaching/fm-courses'

# List of countries
with open("country.json", "r") as read_file:
        data = json.load(read_file)

c_labels = list(data.values())

# Connect to Github
g = Github(fme_github_key)
repo = g.get_repo(courses_repo)

# Get labels that already exist
labels = repo.get_labels()
repo_labels = []
for l in labels:
    repo_labels += [l.name.lower()]

# Add countries as labels
for label in data.values():
    color = "%06x" % random.randint(0, 0xFFFFFF)
    if not label.lower() in repo_labels:
        print("repo.create_label("+label+","+color+")")
        repo.create_label(label, color)
