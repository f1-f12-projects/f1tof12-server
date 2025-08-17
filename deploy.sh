#!/bin/bash
set -e

# Install Serverless Framework
sudo npm install -g serverless || { echo "❌ Global serverless install failed"; exit 1; }
npm install serverless-python-requirements || { echo "❌ npm install failed"; exit 1; }

# Deploy to AWS
serverless deploy || { echo "❌ Serverless deploy failed"; exit 1; }

echo "Deployment complete! Your API is available at the endpoint shown above."