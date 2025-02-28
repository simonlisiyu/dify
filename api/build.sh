#!/bin/bash
set -e

git log -1 > commit_info.txt

VERSION=$(git rev-parse --abbrev-ref HEAD)

# 构建的cpu架构类型，默认是x86-64，可选的有：amd64, arm64
if [ -n "$1" ]; then
    TYPE="$1" #arm64
else
    TYPE="amd64"
fi

DOCKER_BUILDKIT=1 docker build . -t docker.art.haizhi.com/starry-api-$TYPE:$VERSION --platform linux/$TYPE
