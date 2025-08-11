#!/bin/bash

echo "🧹 Cleaning previous builds..."
chmod -R 755 .aws-sam 2>/dev/null || true
rm -rf .aws-sam

echo "🔨 Building SAM application..."
sam build

echo "🚀 Deploying to AWS..."
sam deploy --stack-name f1tof12-server --region ap-south-1 --capabilities CAPABILITY_IAM --resolve-s3

echo "✅ Clean build and deploy complete!"