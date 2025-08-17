#!/bin/bash
set -e

yum update -y || { echo "❌ System update failed"; exit 1; }
yum install -y python3 python3-pip || { echo "❌ Python installation failed"; exit 1; }
pip3 install -r /home/ec2-user/f1tof12-server/requirements.txt || { echo "❌ Requirements installation failed"; exit 1; }