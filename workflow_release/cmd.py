#!/usr/bin/env python
import os
import re
import sys
import json
import shutil
import datetime

from ruamel import yaml

from .utils import WorkflowUtils

BASE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)))
SCRIPTS_PATH = os.path.join(BASE_PATH, "scripts")

build_repo_path = os.path.join("build", "repo")
build_charts_path = os.path.join("build", "charts")
os.system("mkdir -p %s %s" % (build_repo_path, build_charts_path))

deis_registry = ""
workflow_util = None
build_settings = None
chartmuseum_api = "http://charts.deis.cc/api/stable/charts"
chartmuseum_user = "admin:admin"

def _init_env():
    if not os.path.exists("templates"):
        shutil.copytree(os.path.join(BASE_PATH, "templates"), "templates")
    if len(sys.argv) < 2:
        print("Missing parameters: deis-release {action} {args}")
    else:
        global build_settings, deis_registry, workflow_util, \
            chartmuseum_api, chartmuseum_user
        workflow_util = _get_workflow_util()
        deis_registry = os.getenv("DEIS_REGISTRY", deis_registry)
        with open(os.path.join("templates", "settings.json")) as f:
            build_settings = json.load(f)
        chartmuseum_api = os.getenv("CHARTMUSEUM_API", chartmuseum_api)
        chartmuseum_user = os.getenv("CHARTMUSEUM_USER", chartmuseum_user)
        os.environ['DEIS_REGISTRY'] = deis_registry
        return True
    return False

def _change_yaml(name, filename):
    if not os.path.exists(filename): return
    with open(filename) as f:
        data = yaml.round_trip_load(f)
        if "version" in data:
            data["version"] = workflow_util.get_version(name)
        if "docker_tag" in data:
            data["docker_tag"] = workflow_util.get_version(name)
        if "docker_registry" in data:
            data["docker_registry"] = deis_registry
    with open(filename, "w") as f:
        yaml.round_trip_dump(
            data,
            f,
            allow_unicode=True,
        )

def _get_workflow_util():
    github_org = os.getenv("GETHUB_ORG", "deiscc")
    github_auth = os.getenv("GETHUB_AUTH", ":").split(":")
    version = os.getenv("VERSION", "v0.0.0")
    pre_version = os.getenv("PRE_VERSION", "v0.0.0")
    return WorkflowUtils(org=github_org, user=github_auth,
        version=version, pre_version=pre_version)

def build_workflow(*args):
    name_list = build_settings.keys() if len(args) == 0 else args
    for name in name_list:
        export_script = "export VERSION={version}".format(
            version=workflow_util.get_version(name)
        )
        script = "{script} {repo_path} {build_name}".format(
            script=os.path.join(SCRIPTS_PATH, "build_workflow.sh"),
            repo_path=build_repo_path,
            build_name=name
        )
        os.system("%s && %s" % (export_script, script))

def git(*args):
    name_list = build_settings.keys()
    for name in name_list:
        cmd_args = list(args)
        if cmd_args[0] in ("push", "clone", "pull", "push", "fetch"):
            repo_url = build_settings[name]['repo']
            cmd_args.append(repo_url)
            if cmd_args[0] == "clone":
                cmd_args.append(".")
        repo_path = os.path.join(build_repo_path, name)
        if not os.path.exists(repo_path): os.makedirs(repo_path)
        git_script = "cd %s && git %s" % (repo_path, " ".join(cmd_args))
        print(git_script)
        os.system(git_script)

def build_charts(*args):
    tar_version_script_tpl = "tar zcvf {name}-{version}.tgz {name}"
    name_list = build_settings.keys() if len(args) == 0 else args
    for key in name_list:
        chart_path = os.path.join(build_charts_path, key)
        repo_charts_path = os.path.join(build_repo_path, key, "charts", key)
        if not os.path.exists(repo_charts_path): continue
        copy_script = "cp -rf %s %s" % (repo_charts_path, chart_path)
        os.system(copy_script)
        chart_yaml = os.path.join(chart_path, "Chart.yaml")
        values_yaml = os.path.join(chart_path, "values.yaml")
        requirements_yaml = os.path.join(chart_path, "requirements.yaml")
        _change_yaml(key, chart_yaml)
        _change_yaml(key, values_yaml)
        _change_yaml(key, requirements_yaml)
        os.system("%s && %s" % (
            "cd %s" % build_charts_path,
            tar_version_script_tpl.format(
                    name=key,
                    version=workflow_util.get_version(key)
                )
            )
        )
        os.system("rm -rf %s" % chart_path)

def upload_charts(*args):
    script = "curl -u {user} -F 'chart=@{name}' {url}"
    name_list = build_settings.keys() if len(args) == 0 else args
    for name in name_list:
        tar_file = os.path.join(
            build_charts_path,
            "{name}-{version}.tgz".format(
                name=name, version=workflow_util.get_version(name))
        )
        if not os.path.exists(tar_file): continue
        upload_script = "%s && %s" % (
            "cd %s" % build_charts_path,
            script.format(
                user=chartmuseum_user,
                name=tar_file,
                url=chartmuseum_api,
            ),
        )
        os.system(upload_script)

def main():
    if not _init_env(): return
    command = sys.argv[1]
    command_args = sys.argv[2:]
    if command == 'workflow':
        build_workflow(*command_args)
    elif command == 'charts':
        sub_command = command_args[0]
        if sub_command == "build":
            build_charts(*command_args[1:])
        elif sub_command == "upload":
            upload_charts(*command_args[1:])
    elif command == "git":
        git(*command_args)
    else:
        print("Unsupported operation types")
