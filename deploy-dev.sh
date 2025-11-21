#!/bin/bash

REGION="ap-south-1"
STACK_NAME="f1tof12-server-dev"
S3_BUCKET_NAME="f1tof12-server-dev"
export ENVIRONMENT=dev

echo "🚀 Deploying to DEV environment..."

# Create S3 bucket if it doesn't exist
echo "📦 Checking S3 bucket..."
aws s3 mb s3://$S3_BUCKET_NAME --region $REGION 2>/dev/null || echo "Bucket already exists"

echo "🔨 Building..."
sam build -t template-dev.yaml || { echo "❌ Build failed"; exit 1; }

echo "📦 Deploying..."
sam deploy --template-file .aws-sam/build/template.yaml --stack-name $STACK_NAME --region $REGION --capabilities CAPABILITY_IAM --s3-bucket $S3_BUCKET_NAME || { echo "❌ Deploy failed"; exit 1; }

echo "✅ Dev deployment complete!"
echo "🌐 Custom domain: https://dev-api.f1tof12.com"
echo "🚀 Dev API is ready to use!"