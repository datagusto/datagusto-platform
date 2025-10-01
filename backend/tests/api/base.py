"""
Base test class for controller layer tests.

This module provides a base class with helper methods for API testing.
"""

from typing import Any, Dict, Optional
from httpx import AsyncClient, Response
from unittest.mock import AsyncMock

from tests.utils import assert_response_success, assert_response_error


class BaseControllerTest:
    """Base class for controller tests with common helper methods."""

    def setup_method(self):
        """Setup method called before each test."""
        pass

    def teardown_method(self):
        """Teardown method called after each test."""
        pass

    async def _make_request(
        self,
        client: AsyncClient,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """
        Make HTTP request to API endpoint.

        Args:
            client: AsyncClient instance
            method: HTTP method (GET, POST, PATCH, DELETE)
            url: Request URL
            headers: Optional request headers
            json: Optional JSON request body
            data: Optional form data
            params: Optional query parameters

        Returns:
            HTTP response object
        """
        method = method.upper()

        if method == "GET":
            return await client.get(url, headers=headers, params=params)
        elif method == "POST":
            return await client.post(url, headers=headers, json=json, data=data)
        elif method == "PATCH":
            return await client.patch(url, headers=headers, json=json)
        elif method == "PUT":
            return await client.put(url, headers=headers, json=json)
        elif method == "DELETE":
            return await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    def _assert_success(
        self,
        response: Response,
        expected_status: int = 200,
        expected_keys: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """
        Assert successful response and validate structure.

        Args:
            response: HTTP response object
            expected_status: Expected HTTP status code
            expected_keys: Optional list of required response keys

        Returns:
            Response JSON data

        Raises:
            AssertionError: If response doesn't match expected structure
        """
        assert_response_success(response, expected_status)
        data = response.json()

        if expected_keys:
            for key in expected_keys:
                assert key in data, f"Response missing required key: {key}"

        return data

    def _assert_error(
        self,
        response: Response,
        expected_status: int,
        expected_detail: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Assert error response and validate structure.

        Args:
            response: HTTP response object
            expected_status: Expected HTTP status code
            expected_detail: Expected error detail message

        Returns:
            Response JSON data

        Raises:
            AssertionError: If response doesn't match expected error structure
        """
        assert_response_error(response, expected_status, expected_detail)
        return response.json()

    def _mock_service_method(
        self,
        service: AsyncMock,
        method_name: str,
        return_value: Any = None,
        side_effect: Optional[Exception] = None,
    ) -> AsyncMock:
        """
        Configure mock service method.

        Args:
            service: Mock service instance
            method_name: Name of method to mock
            return_value: Value to return (optional)
            side_effect: Exception to raise (optional)

        Returns:
            Configured AsyncMock for the method
        """
        method = getattr(service, method_name)

        if side_effect:
            method.side_effect = side_effect
        else:
            method.return_value = return_value

        return method
