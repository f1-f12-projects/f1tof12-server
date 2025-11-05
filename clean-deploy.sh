#!/bin/bash

# Get environment parameter
ENV=${1:-prod}

REGION="ap-south-1"
STACK_NAME="f1tof12-server"
S3_BUCKET_NAME="f1tof12-server"
export ENVIRONMENT=prod

echo "🌍 Deploying to $ENV environment (Region: $REGION)"

echo "🔍 Checking if S3 bucket exists..."
if ! aws s3 ls "s3://$S3_BUCKET_NAME" >/dev/null 2>&1; then
    echo "❌ S3 bucket '$S3_BUCKET_NAME' does not exist!"
    echo "Create it with: aws s3 mb s3://$S3_BUCKET_NAME --region $REGION"
    exit 1
fi

echo "🧹 Cleaning previous builds..."
chmod -R 755 .aws-sam 2>/dev/null || true
rm -rf .aws-sam

echo "🔨 Building SAM application..."
sam build || { echo "❌ Build failed"; exit 1; }

echo "🚀 Deploying to AWS..."
sam deploy --stack-name $STACK_NAME --region $REGION --capabilities CAPABILITY_IAM --s3-bucket $S3_BUCKET_NAME || { echo "❌ Deploy failed"; exit 1; }

echo "📊 Setting up DynamoDB tables..."
python3 setup_environment.py $ENV || echo "⚠️  DynamoDB setup skipped (tables may already exist)"

echo "✅ Clean build and deploy complete!"