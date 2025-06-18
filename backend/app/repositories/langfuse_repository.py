import requests
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def convert_to_utc_timestamp(dt: datetime) -> str:
    """Convert datetime to UTC timestamp string in ISO 8601 format."""
    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        return dt.isoformat() + "Z"
    else:
        # Convert to UTC and format as ISO 8601
        utc_dt = dt.utctimetuple()
        return datetime(*utc_dt[:6]).isoformat() + "Z"


class LangfuseRepository:
    """Repository for interacting with Langfuse API."""

    def __init__(self, public_key: str, secret_key: str, server: str):
        self.server = server.rstrip("/")
        self.basic = HTTPBasicAuth(public_key, secret_key)

    def get_traces(
        self,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        page: int = 1,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get traces from Langfuse API.

        Args:
            from_timestamp: Filter traces created after this timestamp
            to_timestamp: Filter traces created before this timestamp
            page: Page number (1-based)
            limit: Number of items per page

        Returns:
            List of trace dictionaries
        """
        if from_timestamp is None:
            from_timestamp = datetime.now() - timedelta(days=30)

        params = {
            "page": page,
            "limit": limit,
        }

        if from_timestamp:
            params["fromTimestamp"] = convert_to_utc_timestamp(from_timestamp)
        if to_timestamp:
            params["toTimestamp"] = convert_to_utc_timestamp(to_timestamp)

        try:
            logger.info(
                f"Fetching traces from Langfuse: {self.server}/api/public/traces"
            )
            response = requests.get(
                f"{self.server}/api/public/traces",
                params=params,
                auth=self.basic,
                timeout=30,
            )
            response.raise_for_status()
            response_json = response.json()
            traces = response_json.get("data", [])

            logger.info(f"Successfully fetched {len(traces)} traces from Langfuse")
            return traces

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch traces from Langfuse: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error fetching traces: {e}")
            raise e

    def get_trace(self, trace_id: str) -> Dict[str, Any]:
        """
        Get a single trace by ID from Langfuse API.

        Args:
            trace_id: Langfuse trace ID

        Returns:
            Trace dictionary
        """
        try:
            logger.info(f"Fetching trace {trace_id} from Langfuse")
            response = requests.get(
                f"{self.server}/api/public/traces/{trace_id}",
                auth=self.basic,
                timeout=30,
            )
            response.raise_for_status()
            trace = response.json()

            logger.info(f"Successfully fetched trace {trace_id} from Langfuse")
            return trace

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch trace {trace_id} from Langfuse: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error fetching trace {trace_id}: {e}")
            raise e

    def get_observations(
        self, trace_id: Optional[str] = None, page: int = 1, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get observations from Langfuse API.

        Args:
            trace_id: Filter by trace ID
            page: Page number (1-based)
            limit: Number of items per page

        Returns:
            List of observation dictionaries
        """
        params = {
            "page": page,
            "limit": limit,
        }

        if trace_id:
            params["traceId"] = trace_id

        try:
            logger.info(f"Fetching observations from Langfuse")
            response = requests.get(
                f"{self.server}/api/public/observations",
                params=params,
                auth=self.basic,
                timeout=30,
            )
            response.raise_for_status()
            response_json = response.json()
            observations = response_json.get("data", [])

            logger.info(
                f"Successfully fetched {len(observations)} observations from Langfuse"
            )
            return observations

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch observations from Langfuse: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error fetching observations: {e}")
            raise e
