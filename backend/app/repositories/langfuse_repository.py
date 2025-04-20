from datetime import datetime, timezone, timedelta
import requests
from requests.auth import HTTPBasicAuth


def convert_to_utc_timestamp(timestamp: datetime):
    return timestamp.astimezone(timezone.utc).isoformat()


class LangfuseRepository:
    def __init__(self, public_key: str, secret_key: str, server: str):
        self.server = server        
        self.basic = HTTPBasicAuth(public_key, secret_key)

    def get_traces(self, from_timestamp: datetime = None):
        from_timestamp = from_timestamp or datetime.now() - timedelta(days=1)
        from_timestamp_utc = convert_to_utc_timestamp(from_timestamp)

        try:
            response = requests.get(
                f"{self.server}/api/public/traces",
                params={"fromTimestamp": from_timestamp_utc},
                auth=self.basic,
            )
            response_json = response.json()
            traces = response_json["data"]
        except Exception as e:
            raise e
        
        return traces

    def get_trace(self, trace_id: str):
        try:
            response = requests.get(
                f"{self.server}/api/public/traces/{trace_id}",
                auth=self.basic,
            )
            trace = response.json()
        except Exception as e:
            raise e
        
        return trace
