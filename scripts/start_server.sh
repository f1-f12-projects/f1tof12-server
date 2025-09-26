#!/bin/bash
cd /home/ec2-user/f1tof12-server
# Source environment variables from .env file if it exists
if [ -f .env ]; then
    export $(cat .env | xargs)
fi
export S3_BUCKET=f1tof12-db-backup
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &