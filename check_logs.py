import boto3
import json
from datetime import datetime, timedelta

def get_lambda_logs():
    logs_client = boto3.client('logs', region_name='ap-south-1')
    
    # Get log group for the Lambda function
    log_group = '/aws/lambda/f1tof12-server-F1toF12API-*'
    
    try:
        # List log groups to find the exact name
        response = logs_client.describe_log_groups(logGroupNamePrefix='/aws/lambda/f1tof12-server')
        
        if response['logGroups']:
            log_group_name = response['logGroups'][0]['logGroupName']
            print(f"Found log group: {log_group_name}")
            
            # Get recent logs
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            logs_response = logs_client.filter_log_events(
                logGroupName=log_group_name,
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000)
            )
            
            print("\n=== Recent Lambda Logs ===")
            for event in logs_response['events'][-50:]:  # Last 10 events
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                print(f"[{timestamp}] {event['message']}", end="")
        else:
            print("No log groups found")
            
    except Exception as e:
        print(f"Error getting logs: {e}")

if __name__ == "__main__":
    get_lambda_logs()