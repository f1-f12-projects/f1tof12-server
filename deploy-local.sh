#!/bin/bash

# Install Serverless Framework locally (no sudo needed)
npm install serverless serverless-python-requirements || { echo "❌ npm install failed"; exit 1; }

# Deploy using local installation
npx serverless deploy || { echo "❌ Serverless deploy failed"; exit 1; }

echo "Deployment complete! Your API is available at the endpoint shown above."