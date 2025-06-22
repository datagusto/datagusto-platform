import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import status
from fastapi.testclient import TestClient

from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


class TestTracesEndpoints:
    """Test cases for traces API endpoints."""

    @pytest.fixture
    async def authenticated_user_and_project(self, db_session):
        """Create authenticated user with project for testing."""
        # Create user
        user_data = UserCreate(
            name="Test User",
            email="test@example.com",
            password="testpassword123"
        )
        user = await AuthService.register_user(user_data, db_session)
        
        # Create project (would normally be done through API)
        from app.repositories.project_repository import ProjectRepository
        project_repo = ProjectRepository(db_session)
        
        project_data = {
            "id": uuid.uuid4(),
            "name": "Test Project",
            "organization_id": user.id,  # Use user ID as org ID for simplicity
            "platform_type": "langfuse",
            "platform_config": {
                "public_key": "pk_test_123",
                "secret_key": "sk_test_456", 
                "url": "https://cloud.langfuse.com"
            }
        }
        project = await project_repo.create_project(project_data)
        db_session.commit()
        
        return user, project

    @pytest.fixture
    def auth_headers(self, client: TestClient):
        """Get authentication headers for API requests."""
        # Login to get token
        login_data = {
            "username": "test@example.com",
            "password": "testpassword123"
        }
        response = client.post("/api/v1/auth/token", data=login_data)
        token_data = response.json()
        
        return {"Authorization": f"Bearer {token_data['access_token']}"}

    @pytest.mark.asyncio
    async def test_sync_traces_success(self, client: TestClient, authenticated_user_and_project, auth_headers):
        """Test successful trace synchronization."""
        user, project = await authenticated_user_and_project
        
        with patch('app.services.trace_service.TraceService.sync_traces') as mock_sync:
            mock_sync.return_value = {
                "project_id": project.id,
                "total_traces": 5,
                "new_traces": 3,
                "updated_traces": 2,
                "sync_started_at": datetime.utcnow(),
                "sync_completed_at": datetime.utcnow(),
                "error": None
            }
            
            response = client.post(
                f"/api/v1/traces/sync/{project.id}",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total_traces"] == 5
            assert data["new_traces"] == 3
            assert data["updated_traces"] == 2
            assert data["error"] is None

    @pytest.mark.asyncio
    async def test_sync_traces_unauthorized(self, client: TestClient):
        """Test trace sync without authentication."""
        project_id = uuid.uuid4()
        
        response = client.post(f"/api/v1/traces/sync/{project_id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_sync_traces_project_not_found(self, client: TestClient, auth_headers):
        """Test trace sync with non-existent project."""
        project_id = uuid.uuid4()
        
        with patch('app.services.trace_service.TraceService.sync_traces') as mock_sync:
            mock_sync.return_value = {
                "project_id": project_id,
                "total_traces": 0,
                "new_traces": 0,
                "updated_traces": 0,
                "sync_started_at": datetime.utcnow(),
                "error": "Project not found"
            }
            
            response = client.post(
                f"/api/v1/traces/sync/{project_id}",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["error"] == "Project not found"

    @pytest.mark.asyncio
    async def test_get_traces_success(self, client: TestClient, authenticated_user_and_project, auth_headers):
        """Test successful retrieval of traces."""
        user, project = await authenticated_user_and_project
        
        mock_traces = [
            {
                "id": str(uuid.uuid4()),
                "external_id": "trace-123",
                "platform_type": "langfuse",
                "timestamp": datetime.utcnow().isoformat(),
                "quality_score": 0.85,
                "raw_data": {"test": "data"}
            },
            {
                "id": str(uuid.uuid4()),
                "external_id": "trace-456", 
                "platform_type": "langfuse",
                "timestamp": datetime.utcnow().isoformat(),
                "quality_score": 0.92,
                "raw_data": {"test": "data2"}
            }
        ]
        
        with patch('app.services.trace_service.TraceService.get_traces_by_project') as mock_get:
            mock_get.return_value = mock_traces
            
            response = client.get(
                f"/api/v1/traces/project/{project.id}",
                headers=auth_headers,
                params={"limit": 50, "offset": 0}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2
            assert data[0]["external_id"] == "trace-123"
            assert data[1]["quality_score"] == 0.92

    @pytest.mark.asyncio
    async def test_get_traces_with_pagination(self, client: TestClient, authenticated_user_and_project, auth_headers):
        """Test trace retrieval with pagination parameters."""
        user, project = await authenticated_user_and_project
        
        with patch('app.services.trace_service.TraceService.get_traces_by_project') as mock_get:
            mock_get.return_value = []
            
            response = client.get(
                f"/api/v1/traces/project/{project.id}",
                headers=auth_headers,
                params={"limit": 10, "offset": 20}
            )
            
            assert response.status_code == status.HTTP_200_OK
            
            # Verify pagination parameters were passed correctly
            mock_get.assert_called_once_with(
                str(project.id), str(user.id), db_session=mock_get.call_args[0][2], limit=10, offset=20
            )

    @pytest.mark.asyncio
    async def test_get_trace_detail_success(self, client: TestClient, authenticated_user_and_project, auth_headers):
        """Test successful retrieval of trace details."""
        user, project = await authenticated_user_and_project
        trace_id = uuid.uuid4()
        
        mock_trace = {
            "id": str(trace_id),
            "external_id": "trace-123",
            "platform_type": "langfuse",
            "timestamp": datetime.utcnow().isoformat(),
            "quality_score": 0.88,
            "quality_issues": [],
            "raw_data": {"input": "test", "output": "result"},
            "observations": [
                {
                    "id": str(uuid.uuid4()),
                    "external_id": "obs-1",
                    "type": "generation",
                    "start_time": datetime.utcnow().isoformat(),
                    "raw_data": {"model": "gpt-4"}
                }
            ]
        }
        
        with patch('app.services.trace_service.TraceService.get_trace_with_observations') as mock_get:
            mock_get.return_value = mock_trace
            
            response = client.get(
                f"/api/v1/traces/{trace_id}",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == str(trace_id)
            assert data["quality_score"] == 0.88
            assert len(data["observations"]) == 1

    @pytest.mark.asyncio
    async def test_get_trace_detail_not_found(self, client: TestClient, auth_headers):
        """Test trace detail retrieval for non-existent trace."""
        trace_id = uuid.uuid4()
        
        with patch('app.services.trace_service.TraceService.get_trace_with_observations') as mock_get:
            mock_get.return_value = None
            
            response = client.get(
                f"/api/v1/traces/{trace_id}",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_quality_metrics_success(self, client: TestClient, authenticated_user_and_project, auth_headers):
        """Test successful retrieval of quality metrics."""
        user, project = await authenticated_user_and_project
        
        mock_metrics = {
            "average_quality_score": 0.85,
            "total_traces": 150,
            "traces_by_quality": {
                "excellent": 60,
                "good": 45,
                "fair": 30,
                "poor": 15
            },
            "quality_trend": [
                {"date": "2024-01-01", "score": 0.82},
                {"date": "2024-01-02", "score": 0.85},
                {"date": "2024-01-03", "score": 0.87}
            ]
        }
        
        with patch('app.services.data_quality_service.DataQualityService') as mock_service:
            mock_service.get_project_quality_metrics.return_value = mock_metrics
            
            response = client.get(
                f"/api/v1/traces/project/{project.id}/quality-metrics",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["average_quality_score"] == 0.85
            assert data["total_traces"] == 150
            assert len(data["quality_trend"]) == 3

    @pytest.mark.asyncio
    async def test_analyze_trace_quality_success(self, client: TestClient, authenticated_user_and_project, auth_headers):
        """Test manual trace quality analysis."""
        user, project = await authenticated_user_and_project
        trace_id = uuid.uuid4()
        
        with patch('app.services.trace_service.TraceService.analyze_traces_data_quality') as mock_analyze:
            mock_analyze.return_value = None
            
            response = client.post(
                f"/api/v1/traces/{trace_id}/analyze-quality",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "message" in data
            
            # Verify analysis was triggered
            mock_analyze.assert_called_once_with([str(trace_id)], mock_analyze.call_args[0][1])

    @pytest.mark.asyncio
    async def test_bulk_analyze_quality_success(self, client: TestClient, authenticated_user_and_project, auth_headers):
        """Test bulk quality analysis for project traces."""
        user, project = await authenticated_user_and_project
        
        request_data = {
            "trace_ids": [str(uuid.uuid4()), str(uuid.uuid4())]
        }
        
        with patch('app.services.trace_service.TraceService.analyze_traces_data_quality') as mock_analyze:
            mock_analyze.return_value = None
            
            response = client.post(
                f"/api/v1/traces/project/{project.id}/analyze-quality",
                headers=auth_headers,
                json=request_data
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "analyzed" in data["message"]
            
            # Verify bulk analysis was triggered
            mock_analyze.assert_called_once_with(request_data["trace_ids"], mock_analyze.call_args[0][1])

    @pytest.mark.asyncio
    async def test_invalid_project_id_format(self, client: TestClient, auth_headers):
        """Test API endpoints with invalid UUID format."""
        invalid_id = "not-a-uuid"
        
        response = client.get(
            f"/api/v1/traces/project/{invalid_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_access_denied_to_project(self, client: TestClient, auth_headers):
        """Test access denial to project user doesn't have access to."""
        project_id = uuid.uuid4()
        
        with patch('app.services.trace_service.TraceService.get_traces_by_project') as mock_get:
            mock_get.side_effect = ValueError("Project not found")
            
            response = client.get(
                f"/api/v1/traces/project/{project_id}",
                headers=auth_headers
            )
            
            # This should be handled appropriately by the endpoint
            assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]