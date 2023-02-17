#!/bin/bash

docker build -t cdk-build .
docker run -it cdk-build > videomoderation.template.yaml