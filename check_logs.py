import boto3
import json
from datetime import datetime, timedelta, timezone
import pytz

def get_lambda_logs():
    logs_client = boto3.client('logs')  # type: ignore
    
    try:
        target_log_group = '/aws/lambda/f1tof12-api-logs'
        print(f"Checking logs from: {target_log_group}")
        
        # Get recent logs (last 1 hour for latest logs)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=1)
        
        all_events = []
        next_token = None
        
        # Handle pagination to get all recent logs
        while True:
            kwargs = {
                'logGroupName': target_log_group,
                'startTime': int(start_time.timestamp() * 1000),
                'endTime': int(end_time.timestamp() * 1000),
                'limit': 1000
            }
            if next_token:
                kwargs['nextToken'] = next_token
                
            logs_response = logs_client.filter_log_events(**kwargs)  # type: ignore
            all_events.extend(logs_response['events'])
            
            next_token = logs_response.get('nextToken')
            if not next_token:
                break
        
        # Sort by timestamp to ensure latest logs are at the end
        all_events.sort(key=lambda x: x['timestamp'])
        
        print(f"Found {len(all_events)} log events in last hour")
        print("\n=== Latest Lambda Logs ===")
        
        # Show last 50 events (most recent)
        ist = pytz.timezone('Asia/Kolkata')
        for event in all_events[-50:]:
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000, tz=timezone.utc).astimezone(ist)
            print(f"[{timestamp}] {event['message']}", end="")
            
    except Exception as e:
        print(f"Error getting logs: {e}")

if __name__ == "__main__":
    get_lambda_logs()