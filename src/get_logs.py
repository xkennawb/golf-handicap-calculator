import boto3
import time
from datetime import datetime, timedelta

logs = boto3.client('logs', region_name='ap-southeast-2', verify=False)

log_group = '/aws/lambda/golf-handicap-tracker'

# Get recent log streams
start_time = int((datetime.now() - timedelta(minutes=5)).timestamp() * 1000)

try:
    streams = logs.describe_log_streams(
        logGroupName=log_group,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )
    
    if streams['logStreams']:
        stream_name = streams['logStreams'][0]['logStreamName']
        print(f"Getting logs from: {stream_name}\n")
        
        events = logs.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            startTime=start_time,
            limit=100
        )
        
        # Print last 30 log lines
        for event in events['events'][-30:]:
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
            print(f"{timestamp.strftime('%H:%M:%S')} {event['message']}")
            
except Exception as e:
    print(f"Error: {e}")
