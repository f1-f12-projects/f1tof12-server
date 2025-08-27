#!/bin/bash

echo "📦 Getting S3 bucket name..."
S3_BUCKET_NAME="f1tof12-server"
if [ -z "$S3_BUCKET_NAME" ]; then
    echo "❌ S3_BUCKET_NAME environment variable is not set!"
    exit 1
fi

echo "🌍 Using S3 bucket: $S3_BUCKET_NAME"

echo "🔍 Checking if S3 bucket exists..."
if ! aws s3 ls "s3://$S3_BUCKET_NAME" >/dev/null 2>&1; then
    echo "❌ S3 bucket '$S3_BUCKET_NAME' does not exist!"
    echo "Create it with: aws s3 mb s3://$S3_BUCKET_NAME --region ap-south-1"
    exit 1
fi

echo "🧹 Cleaning previous builds..."
chmod -R 755 .aws-sam 2>/dev/null || true
rm -rf .aws-sam

echo "🔨 Building SAM application..."
sam build || { echo "❌ Build failed"; exit 1; }


echo "🚀 Deploying to AWS..."
sam deploy --stack-name f1tof12-server --region ap-south-1 --capabilities CAPABILITY_IAM --s3-bucket $S3_BUCKET_NAME || { echo "❌ Deploy failed"; exit 1; }

echo "✅ Clean build and deploy complete!"