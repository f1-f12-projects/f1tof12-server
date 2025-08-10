#!/bin/bash

# Install Serverless Framework
sudo npm install -g serverless
npm install serverless-python-requirements

# Deploy to AWS
serverless deploy

echo "Deployment complete! Your API is available at the endpoint shown above."