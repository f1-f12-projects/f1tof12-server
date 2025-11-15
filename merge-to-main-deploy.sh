#!/bin/bash

# Merge dev to main and deploy
git checkout main
git merge dev
./clean-deploy.sh
git checkout dev