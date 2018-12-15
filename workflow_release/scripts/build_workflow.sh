#!/usr/bin/env bash
set -eo pipefail

export DEIS_REGISTY=""

deis_repo_path="$1"

builder(){
    cd $deis_repo_path/builder
    make bootstrap docker-build docker-immutable-push
}

redis(){
    cd $deis_repo_path/redis
    make docker-build docker-immutable-push
}

workflow-manager(){
    cd $deis_repo_path/workflow-manager
    make bootstrap build docker-build docker-immutable-push
}

controller(){
    cd $deis_repo_path/controller
    make build docker-immutable-push
}

dockerbuilder(){
    cd $deis_repo_path/dockerbuilder
    make docker-build docker-immutable-push
}

fluentd(){
    cd $deis_repo_path/fluentd
    make build docker-immutable-push
}

logger(){
    cd $deis_repo_path/logger
    make bootstrap build docker-immutable-push
}

minio(){
    cd $deis_repo_path/minio
    make docker-build docker-immutable-push
}

monitor(){
    cd $deis_repo_path/monitor/grafana
    make build docker-immutable-push
    cd $deis_repo_path/monitor/influxdb
    make build docker-immutable-push
    cd $deis_repo_path/monitor/telegraf
    make build docker-immutable-push
}

nsq(){
    cd $deis_repo_path/nsq
    make build docker-immutable-push
}

database(){
    cd $deis_repo_path/database
    make docker-build docker-immutable-push
}

registry(){
    cd $deis_repo_path/registry
    make docker-build docker-immutable-push
}

registry-proxy(){
    cd $deis_repo_path/registry-proxy
    make build docker-immutable-push
}

registry-token-refresher(){
    cd $deis_repo_path/registry-token-refresher
    make bootstrap docker-build docker-immutable-push
}

router(){
    cd $deis_repo_path/router
    make bootstrap docker-build docker-immutable-push
}

slugbuilder(){
    cd $deis_repo_path/slugbuilder
    make build docker-build docker-immutable-push
}

slugrunner(){
    cd $deis_repo_path/slugrunner
    make build docker-build docker-immutable-push
}

"$2"