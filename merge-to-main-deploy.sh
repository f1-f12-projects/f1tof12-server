#!/bin/bash

# Merge dev to main and deploy
git checkout main
git merge dev
git push origin main
# ./clean-deploy.sh # Deployment will happen using GitHub actions. Hence commented this.
git checkout dev
