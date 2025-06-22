import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

from app.services.trace_service import TraceService
from app.schemas.trace import TraceSyncStatus
from app.models.project import Project


class TestTraceService:
    """Test cases for TraceService - main feature functionality."""

    @pytest.fixture
    def sample_project(self):
        """Create a sample project for testing."""
        return Project(
            id=uuid.uuid4(),
            name="Test Project",
            organization_id=uuid.uuid4(),
            platform_type="langfuse",
            platform_config={
                "public_key": "pk_test_123",
                "secret_key": "sk_test_456",
                "url": "https://cloud.langfuse.com"
            },
            api_key="test_api_key",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_langfuse_traces(self):
        """Create sample Langfuse trace data."""
        return [
            {
                "id": "trace-123",
                "name": "test_trace",
                "timestamp": "2024-01-01T10:00:00Z",
                "metadata": {"version": "1.0"},
                "input": {"query": "What is AI?"},
                "output": {"response": "AI is artificial intelligence."}
            },
            {
                "id": "trace-456", 
                "name": "another_trace",
                "timestamp": "2024-01-01T11:00:00Z",
                "metadata": {"version": "1.0"},
                "input": {"query": "Explain machine learning"},
                "output": {"response": "Machine learning is a subset of AI."}
            }
        ]

    @pytest.mark.asyncio
    async def test_sync_traces_success(self, sample_project, sample_langfuse_traces):
        """Test successful trace synchronization from Langfuse."""
        project_id = str(sample_project.id)
        user_id = str(uuid.uuid4())
        
        with patch('app.repositories.trace_repository.TraceRepository') as mock_trace_repo, \
             patch('app.repositories.project_repository.ProjectRepository') as mock_project_repo, \
             patch('app.repositories.observation_repository.ObservationRepository') as mock_obs_repo, \
             patch('app.repositories.langfuse_repository.LangfuseRepository') as mock_langfuse_repo:
            
            # Setup mocks
            mock_db = AsyncMock()
            mock_project_repo_instance = mock_project_repo.return_value
            mock_project_repo_instance.get_project_by_id_str.return_value = sample_project
            
            mock_trace_repo_instance = mock_trace_repo.return_value
            mock_trace_repo_instance.get_last_sync_timestamp.return_value = None
            mock_trace_repo_instance.get_existing_trace.return_value = None
            mock_trace_repo_instance.create_trace.return_value = MagicMock(id=uuid.uuid4())
            
            mock_langfuse_repo_instance = mock_langfuse_repo.return_value
            mock_langfuse_repo_instance.get_traces.side_effect = [
                sample_langfuse_traces,  # First page
                []  # No more pages
            ]
            mock_langfuse_repo_instance.get_trace.return_value = {
                "observations": []
            }
            
            # Execute sync
            result = await TraceService.sync_traces(project_id, user_id, mock_db)
            
            # Verify results
            assert isinstance(result, TraceSyncStatus)
            assert result.project_id == uuid.UUID(project_id)
            assert result.new_traces == 2
            assert result.updated_traces == 0
            assert result.total_traces == 2
            assert result.error is None
            assert result.sync_completed_at is not None

    @pytest.mark.asyncio
    async def test_sync_traces_project_not_found(self):
        """Test sync traces when project is not found."""
        project_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        with patch('app.repositories.project_repository.ProjectRepository') as mock_project_repo:
            mock_db = AsyncMock()
            mock_project_repo_instance = mock_project_repo.return_value
            mock_project_repo_instance.get_project_by_id_str.return_value = None
            
            result = await TraceService.sync_traces(project_id, user_id, mock_db)
            
            # Should return error status
            assert result.error is not None
            assert "Project not found" in result.error
            assert result.new_traces == 0
            assert result.updated_traces == 0

    @pytest.mark.asyncio
    async def test_sync_traces_invalid_langfuse_config(self, sample_project):
        """Test sync traces with invalid Langfuse configuration."""
        project_id = str(sample_project.id)
        user_id = str(uuid.uuid4())
        
        # Set invalid config
        sample_project.platform_config = {"public_key": "pk_test"}  # Missing secret_key and url
        
        with patch('app.repositories.project_repository.ProjectRepository') as mock_project_repo:
            mock_db = AsyncMock()
            mock_project_repo_instance = mock_project_repo.return_value
            mock_project_repo_instance.get_project_by_id_str.return_value = sample_project
            
            result = await TraceService.sync_traces(project_id, user_id, mock_db)
            
            # Should return error status
            assert result.error is not None
            assert "Incomplete Langfuse configuration" in result.error

    @pytest.mark.asyncio
    async def test_sync_traces_update_existing(self, sample_project, sample_langfuse_traces):
        """Test updating existing traces during sync."""
        project_id = str(sample_project.id)
        user_id = str(uuid.uuid4())
        
        with patch('app.repositories.trace_repository.TraceRepository') as mock_trace_repo, \
             patch('app.repositories.project_repository.ProjectRepository') as mock_project_repo, \
             patch('app.repositories.observation_repository.ObservationRepository') as mock_obs_repo, \
             patch('app.repositories.langfuse_repository.LangfuseRepository') as mock_langfuse_repo:
            
            # Setup mocks
            mock_db = AsyncMock()
            mock_project_repo_instance = mock_project_repo.return_value
            mock_project_repo_instance.get_project_by_id_str.return_value = sample_project
            
            existing_trace = MagicMock(id=uuid.uuid4())
            mock_trace_repo_instance = mock_trace_repo.return_value
            mock_trace_repo_instance.get_last_sync_timestamp.return_value = None
            mock_trace_repo_instance.get_existing_trace.return_value = existing_trace
            mock_trace_repo_instance.update_trace.return_value = existing_trace
            
            mock_langfuse_repo_instance = mock_langfuse_repo.return_value
            mock_langfuse_repo_instance.get_traces.side_effect = [
                sample_langfuse_traces,
                []
            ]
            
            result = await TraceService.sync_traces(project_id, user_id, mock_db)
            
            # Should have updated existing traces
            assert result.new_traces == 0
            assert result.updated_traces == 2
            assert result.total_traces == 2

    @pytest.mark.asyncio
    async def test_get_traces_by_project(self, sample_project):
        """Test retrieving traces for a project."""
        project_id = str(sample_project.id)
        user_id = str(uuid.uuid4())
        
        with patch('app.repositories.trace_repository.TraceRepository') as mock_trace_repo, \
             patch('app.repositories.project_repository.ProjectRepository') as mock_project_repo:
            
            mock_db = AsyncMock()
            mock_project_repo_instance = mock_project_repo.return_value
            mock_project_repo_instance.get_project_by_id_str.return_value = sample_project
            
            mock_traces = [
                MagicMock(id=uuid.uuid4(), external_id="trace-1"),
                MagicMock(id=uuid.uuid4(), external_id="trace-2")
            ]
            mock_trace_repo_instance = mock_trace_repo.return_value
            mock_trace_repo_instance.get_traces_by_project.return_value = mock_traces
            
            traces = await TraceService.get_traces_by_project(
                project_id, user_id, mock_db, limit=50, offset=0
            )
            
            assert len(traces) == 2
            mock_trace_repo_instance.get_traces_by_project.assert_called_once_with(
                project_id, 50, 0
            )

    @pytest.mark.asyncio
    async def test_get_trace_with_observations(self):
        """Test retrieving a single trace with observations."""
        trace_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        with patch('app.repositories.trace_repository.TraceRepository') as mock_trace_repo, \
             patch('app.repositories.project_repository.ProjectRepository') as mock_project_repo:
            
            mock_db = AsyncMock()
            mock_trace = MagicMock(
                id=uuid.UUID(trace_id),
                project_id=uuid.uuid4(),
                observations=[]
            )
            mock_trace_repo_instance = mock_trace_repo.return_value
            mock_trace_repo_instance.get_trace_by_id.return_value = mock_trace
            
            mock_project = MagicMock()
            mock_project_repo_instance = mock_project_repo.return_value
            mock_project_repo_instance.get_project_by_id_str.return_value = mock_project
            
            trace = await TraceService.get_trace_with_observations(
                trace_id, user_id, mock_db
            )
            
            assert trace is not None
            assert str(trace.id) == trace_id

    @pytest.mark.asyncio
    async def test_get_trace_with_observations_not_found(self):
        """Test retrieving non-existent trace."""
        trace_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        with patch('app.repositories.trace_repository.TraceRepository') as mock_trace_repo:
            mock_db = AsyncMock()
            mock_trace_repo_instance = mock_trace_repo.return_value
            mock_trace_repo_instance.get_trace_by_id.return_value = None
            
            trace = await TraceService.get_trace_with_observations(
                trace_id, user_id, mock_db
            )
            
            assert trace is None

    @pytest.mark.asyncio
    async def test_analyze_traces_data_quality(self):
        """Test data quality analysis for multiple traces."""
        trace_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        
        with patch('app.repositories.trace_repository.TraceRepository') as mock_trace_repo, \
             patch('app.services.data_quality_service.DataQualityService') as mock_quality_service:
            
            mock_db = AsyncMock()
            mock_trace_repo_instance = mock_trace_repo.return_value
            mock_trace_repo_instance.get_trace_by_id.side_effect = [
                MagicMock(id=uuid.UUID(trace_ids[0]), observations=[]),
                MagicMock(id=uuid.UUID(trace_ids[1]), observations=[])
            ]
            
            mock_quality_service.analyze_trace_data_quality.return_value = (0.85, [])
            mock_quality_service.update_trace_quality_metrics.return_value = None
            
            await TraceService.analyze_traces_data_quality(trace_ids, mock_db)
            
            # Verify quality analysis was called for each trace
            assert mock_quality_service.analyze_trace_data_quality.call_count == 2
            assert mock_quality_service.update_trace_quality_metrics.call_count == 2

    @pytest.mark.asyncio
    async def test_create_trace_from_langfuse(self, sample_langfuse_traces):
        """Test creating trace from Langfuse data."""
        project_id = str(uuid.uuid4())
        langfuse_data = sample_langfuse_traces[0]
        
        with patch('app.repositories.trace_repository.TraceRepository') as mock_trace_repo, \
             patch('app.repositories.langfuse_repository.LangfuseRepository') as mock_langfuse_repo, \
             patch('app.repositories.observation_repository.ObservationRepository') as mock_obs_repo:
            
            mock_trace = MagicMock(id=uuid.uuid4())
            mock_trace_repo_instance = mock_trace_repo.return_value
            mock_trace_repo_instance.create_trace.return_value = mock_trace
            
            mock_langfuse_repo_instance = mock_langfuse_repo.return_value
            mock_langfuse_repo_instance.get_trace.return_value = {
                "observations": []
            }
            
            result = await TraceService._create_trace_from_langfuse(
                project_id, langfuse_data, mock_langfuse_repo_instance,
                mock_trace_repo_instance, mock_obs_repo.return_value
            )
            
            assert result == mock_trace
            mock_trace_repo_instance.create_trace.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_trace_from_langfuse(self, sample_langfuse_traces):
        """Test updating existing trace with Langfuse data."""
        existing_trace = MagicMock(id=uuid.uuid4())
        langfuse_data = sample_langfuse_traces[0]
        
        with patch('app.repositories.trace_repository.TraceRepository') as mock_trace_repo:
            mock_trace_repo_instance = mock_trace_repo.return_value
            mock_trace_repo_instance.update_trace.return_value = existing_trace
            
            result = await TraceService._update_trace_from_langfuse(
                existing_trace, langfuse_data, mock_trace_repo_instance
            )
            
            assert result == existing_trace
            mock_trace_repo_instance.update_trace.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_project_with_access_valid(self, sample_project):
        """Test project access verification with valid project."""
        project_id = str(sample_project.id)
        user_id = str(uuid.uuid4())
        
        with patch('app.repositories.project_repository.ProjectRepository') as mock_project_repo:
            mock_project_repo_instance = mock_project_repo.return_value
            mock_project_repo_instance.get_project_by_id_str.return_value = sample_project
            
            result = await TraceService._get_project_with_access(
                project_id, user_id, mock_project_repo_instance
            )
            
            assert result == sample_project

    @pytest.mark.asyncio
    async def test_get_project_with_access_invalid(self):
        """Test project access verification with invalid project."""
        project_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        with patch('app.repositories.project_repository.ProjectRepository') as mock_project_repo:
            mock_project_repo_instance = mock_project_repo.return_value
            mock_project_repo_instance.get_project_by_id_str.return_value = None
            
            with pytest.raises(ValueError, match="Project not found"):
                await TraceService._get_project_with_access(
                    project_id, user_id, mock_project_repo_instance
                )