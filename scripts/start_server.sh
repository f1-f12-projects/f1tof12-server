#!/bin/bash
cd /home/ec2-user/f1tof12-server
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export S3_BUCKET=f1tof12-db-backup
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &