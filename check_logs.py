import boto3
import json
from datetime import datetime, timedelta, timezone

def get_lambda_logs():
    logs_client = boto3.client('logs')  # type: ignore
    
    try:
        target_log_group = '/aws/lambda/f1tof12-api-logs'
        print(f"Checking logs from: {target_log_group}")
        
        # Get recent logs
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=7)
        
        logs_response = logs_client.filter_log_events(  # type: ignore
            logGroupName=target_log_group,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000)
        )
        
        print(f"Found {len(logs_response['events'])} log events")
        print("\n=== Recent Lambda Logs ===")
        for event in logs_response['events'][-50:]:
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000, tz=timezone.utc)
            print(f"[{timestamp}] {event['message']}", end="")
            
    except Exception as e:
        print(f"Error getting logs: {e}")

if __name__ == "__main__":
    get_lambda_logs()