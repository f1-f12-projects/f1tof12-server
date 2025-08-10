#!/bin/bash

# Install Serverless Framework locally (no sudo needed)
npm install serverless serverless-python-requirements

# Deploy using local installation
npx serverless deploy

echo "Deployment complete! Your API is available at the endpoint shown above."