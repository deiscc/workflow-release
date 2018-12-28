# Requirements

* python>=3.5.0
* docker>=1.13

# Install

```
git clone https://github.com/deiscc/workflow-release
cd workflow-release & python3 -m venv .venv
source .venv/bin/active && python3 setup.py develop
```

# Environment

* `GETHUB_ORG` Organization of GitHub, default `deiscc`
* `GETHUB_AUTH` Github's account, like `username:password`
* `VERSION` Workflow version to be released, like `v2.8.0`
* `PRE_VERSION` Workflow version number of the last release, like `v2.7.0`
* `IMAGE_PREFIX` Image prefix of docker registry, default `deiscc`
* `DEIS_REGISTRY` The address of docker registry, use docker official registry by default