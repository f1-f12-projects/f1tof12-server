#!/bin/bash

REGION="ap-south-1"
STACK_NAME="f1tof12-server"
S3_BUCKET_NAME="f1tof12-server"
export ENVIRONMENT=prod

echo "🚀 Fast deploying code changes to PROD..."
echo "🔨 Building..."
sam build || { echo "❌ Build failed"; exit 1; }

echo "📦 Deploying..."
sam deploy --stack-name $STACK_NAME --region $REGION --capabilities CAPABILITY_IAM --s3-bucket $S3_BUCKET_NAME || { echo "❌ Deploy failed"; exit 1; }

echo "✅ Code deployment complete!"