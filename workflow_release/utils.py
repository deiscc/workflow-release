import os
import json
import requests
import collections
from ruamel import yaml
from jinja2 import Template

GITHUB_API = "https://api.github.com/repos"

ALLOWED_COMMIT_TYPE = ["feat", "fix", "docs", "style", "ref", "test", "chore"]

TEMPLATE_DIR = "templates"

class WorkflowUtils(object):

    def __init__(self, org, user, version, pre_version):
        self.org = org
        self.user = user
        self.version = version
        if version != pre_version:
            self.requirements = self._load_requirements()
            self.requirements["workflow"] = {"version": pre_version}
            self.request = self._get_request()
            self.releases = self._generate_releases()
        else: # local build
            self.requirements = {}
            self.releases = {}



    def _get_request(self):
        request = requests.Session()
        request.auth = self.user
        return request

    def _get_template(self, name):
        with open(os.path.join(TEMPLATE_DIR, name)) as f:
            return f.read()

    def _get_version(self, name, pre_version, is_minor=False):
        """
            version format: {major}.{minor}.{patch}
        """
        print(name, "fasfsadfasfsafsda")
        if name == "workflow":
            return self.version
        major, minor, patch = pre_version.split(".")
        if is_minor:
            patch = 0
            minor = int(minor) + 1
        else:
            patch = int(patch) + 1
        return "%s.%s.%s" % (major, minor, patch)

    def _load_requirements(self):
        """
            {
                'slugrunner':{
                    'name': 'slugrunner',
                    'repository': 'https://charts.teamhephy.com',
                    'version': 'v2.6.0'
                }
            }
        """
        result = {}
        with open(os.path.join(TEMPLATE_DIR, "requirements.lock")) as f:
            for node in yaml.safe_load(f)["dependencies"]:
                result[node['name']] = node
        return result

    def _get_commit_type(self, message):
        for t in ALLOWED_COMMIT_TYPE:
            if message.startswith(t):
                return t
        return None

    def _format_message(self, commit_type, message):
        message = message.replace(commit_type+"(", "", 1).replace(")", "", 1) 
        if "\n" in message:
            message = message[:message.index('\n')]
        if "\r" in message:
            message = message[:message.index('\r')]
        return message

    def _generate_release(self, name, version):
        url_tpl = GITHUB_API + "/{org}/{repo}/compare/{version}...master"
        data = self.request.get(url_tpl.format(
            org=self.org, repo=name, version=version)).json()
        release = {"commits": {}, "name": name, "version": version}
        if "commits" in data:
            is_minor = False
            for item in data["commits"]:
                tree = item['commit']['tree']
                message = item['commit']['message']
                author = item['commit']['author']['name']
                commit_type = self._get_commit_type(message)
                if not commit_type: continue
                if commit_type not in release["commits"]:
                    release["commits"][commit_type] = []
                release["commits"][commit_type].append({
                    "name": name,
                    "tree": tree,
                    "author": author,
                    "message": self._format_message(commit_type, message),
                })
                if not is_minor and commit_type == "feat":
                    is_minor = True
            release["version"] = self._get_version(name, version, is_minor)
        return release

    def _generate_releases(self):
        releases = {}
        for key, value in self.requirements.items():
            cache_dir = os.path.join("cache")
            if not os.path.exists(cache_dir): os.makedirs(cache_dir)
            cache_release_file = os.path.join(
                cache_dir, "{name}-{version}.json".format(
                    name=key, version=value['version']))
            if os.path.exists(cache_release_file):
                with open(cache_release_file) as f:
                    releases[key] = json.load(f)
            else:
                print("downloading %s changelog" % key)
                releases[key] = self._generate_release(key, value['version'])
                with open(cache_release_file, "w") as f:
                    json.dump(releases[key], f)
        return releases

    def _generate_release_log(self, key, value):
        commits = collections.OrderedDict(
            sorted(
                value["commits"].items(),
                key=lambda key: ALLOWED_COMMIT_TYPE.index(key[0])
            )
        )
        version = value["version"]
        pre_version = self.requirements[key]
        template = Template(
            self._get_template("release_log.tpl"), trim_blocks=True)
        return template.render(
            commits=commits, version=version, pre_version=version)

    def _post_release(self, name, info):
        """
        post github release format:
        {
            "tag_name": "v1.0.0",
            "target_commitish": "master",
            "name": "v1.0.0",
            "body": "Description of the release",
            "draft": false,
            "prerelease": false
        }
        """
        def get_release_name(name, version):
            tpl = "Deis %s Release %s"
            if name == "workflow":
                name = "Workflow Documentation"
            return tpl.format(name=name.capitalize(), version=version)
        post_data = {
            "name": get_release_name(name, version=info["version"]),
            "tag_name": info["version"],
            "target_commitish": "master",
            "body": self._generate_release_log(name, info),
            "draft": False,
            "prerelease": False
        }
        self.request.post(
            GITHUB_API + "/:org/:repo/releases".format(
                org=self.org, repo=key),
            data=post_data
        )


    def _generate_change_log(self):
        change_versions = []
        change_logs = collections.OrderedDict(
            (key, [])for key in ALLOWED_COMMIT_TYPE)
        for key, value in self.releases.items():
            if self.requirements[key] == value["version"]:
                continue
            change_versions.append(
                (key, self.requirements[key]["version"], value["version"]))
            for commit_type, commits in value["commits"].items():
                change_logs[commit_type].extend(commits)
        version = self.releases["workflow"]["version"]
        pre_version = self.requirements["workflow"]["version"]
        for commit_type in ALLOWED_COMMIT_TYPE:
            commits = change_logs[commit_type]
            if len(commits) == 0: del change_logs[commit_type]
            else: commits.sort(key=lambda key: key["name"])
        template = Template(
            self._get_template("change_log.tpl"), trim_blocks=True)
        return template.render(change_versions=change_versions,
            change_logs=change_logs, version=version, pre_version=pre_version)

    def get_version(self, name):
        if name in self.releases:
            return self.releases[name]["version"]
        return "v0.0.0"

    def post_components_releases(self):
        for key, value in self.releases.items():
            if key == "workflow": continue
            self._post_release(key, value)
    
    def post_workflow_release(self):
        if len(self.releases) == 0: return
        change_log = self._generate_change_log()