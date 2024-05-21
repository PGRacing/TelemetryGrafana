import requests
import datetime
import time

# Simplified URL and channel name
grafana_live_url = "http://localhost:3000/api/live/push/test-channel"
grafana_api_key = "glsa_NH9iUavnzkCFX8xgAKAnwmr6Zptku68i_d584408f"

def push_to_grafana_live(metric_line):
    headers = {
        "Authorization": f"Bearer {grafana_api_key}",
        "Content-Type": "text/plain"
    }
    print(f"Payload: {metric_line}")
    response = requests.post(grafana_live_url, data=metric_line, headers=headers)
    print(f"Response status code: {response.status_code}")
    if response.status_code != 200:
        print(f"Failed to push data to Grafana Live: {response.text}")
    else:
        print(f"Successfully pushed data to Grafana Live: {metric_line}")

def generate_sample_data():
    timestamp = (datetime.datetime.now()-datetime.timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
    metric_line = f'test_channel,source=sample value=42 timestamp={timestamp}'
    return metric_line

if __name__ == "__main__":
    data = generate_sample_data()
    push_to_grafana_live(data)