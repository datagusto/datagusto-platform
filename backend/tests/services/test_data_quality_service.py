import pytest
import uuid
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.data_quality_service import DataQualityService
from app.models.trace import Trace, Observation


class TestDataQualityService:
    """Test cases for DataQualityService - core business functionality."""

    @pytest.fixture
    def sample_trace(self):
        """Create a sample trace for testing."""
        return Trace(
            id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            external_id="test-trace-123",
            platform_type="langfuse",
            timestamp=datetime.utcnow(),
            raw_data={
                "id": "test-trace-123",
                "name": "test_trace",
                "timestamp": "2024-01-01T10:00:00Z",
                "metadata": {"version": "1.0", "user_id": "user123"},
                "input": {"query": "What is the weather?"},
                "output": {"response": "The weather is sunny."}
            },
            last_synced_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @pytest.fixture
    def complete_observations(self):
        """Create complete, high-quality observations for testing."""
        return [
            Observation(
                id=uuid.uuid4(),
                trace_id=uuid.uuid4(),
                external_id="obs-1",
                platform_type="langfuse",
                start_time=datetime.utcnow(),
                raw_data={
                    "id": "obs-1",
                    "type": "generation",
                    "input": {"prompt": "What is the weather?"},
                    "output": {"text": "The weather is sunny."},
                    "metadata": {"model": "gpt-4", "tokens": 150}
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Observation(
                id=uuid.uuid4(),
                trace_id=uuid.uuid4(),
                external_id="obs-2",
                platform_type="langfuse",
                start_time=datetime.utcnow(),
                raw_data={
                    "id": "obs-2",
                    "type": "span",
                    "input": {"data": {"key": "value"}},
                    "output": {"result": "processed"},
                    "metadata": {"duration": 1500}
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]

    @pytest.fixture
    def incomplete_observations(self):
        """Create observations with various quality issues."""
        return [
            Observation(
                id=uuid.uuid4(),
                trace_id=uuid.uuid4(),
                external_id="obs-incomplete-1",
                platform_type="langfuse",
                start_time=datetime.utcnow(),
                raw_data={
                    "id": "obs-incomplete-1",
                    "type": "generation",
                    "input": None,  # Missing input
                    "output": {"text": ""},  # Empty output
                    "metadata": {}  # Empty metadata
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Observation(
                id=uuid.uuid4(),
                trace_id=uuid.uuid4(),
                external_id="obs-incomplete-2",
                platform_type="langfuse",
                start_time=datetime.utcnow(),
                raw_data={
                    "id": "obs-incomplete-2",
                    "type": "span",
                    # Missing input/output entirely
                    "metadata": {"incomplete": True}
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]

    def test_filter_leaf_observations_no_children(self, complete_observations):
        """Test filtering observations when all are leaf nodes (no children)."""
        # All observations should be considered leaf nodes
        leaf_obs = DataQualityService._filter_leaf_observations(complete_observations)
        
        assert len(leaf_obs) == 2
        assert leaf_obs[0].external_id == "obs-1"
        assert leaf_obs[1].external_id == "obs-2"

    def test_filter_leaf_observations_with_hierarchy(self):
        """Test filtering observations with parent-child relationships."""
        parent_obs = Observation(
            id=uuid.uuid4(),
            trace_id=uuid.uuid4(),
            external_id="parent-obs",
            platform_type="langfuse",
            start_time=datetime.utcnow(),
            raw_data={
                "id": "parent-obs",
                "type": "span",
                "input": {"data": "parent"},
                "output": {"result": "parent_result"}
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        child_obs = Observation(
            id=uuid.uuid4(),
            trace_id=uuid.uuid4(),
            external_id="child-obs",
            platform_type="langfuse",
            start_time=datetime.utcnow(),
            raw_data={
                "id": "child-obs",
                "type": "generation",
                "parentObservationId": "parent-obs",  # Child references parent
                "input": {"prompt": "child"},
                "output": {"text": "child_result"}
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        observations = [parent_obs, child_obs]
        leaf_obs = DataQualityService._filter_leaf_observations(observations)
        
        # Only child should be returned as leaf (parent has children)
        assert len(leaf_obs) == 1
        assert leaf_obs[0].external_id == "child-obs"

    def test_filter_leaf_observations_empty_list(self):
        """Test filtering with empty observation list."""
        leaf_obs = DataQualityService._filter_leaf_observations([])
        assert len(leaf_obs) == 0

    @pytest.mark.asyncio
    async def test_analyze_trace_data_quality_high_quality(self, sample_trace, complete_observations, db_session):
        """Test data quality analysis with high-quality data."""
        quality_score, quality_issues = await DataQualityService.analyze_trace_data_quality(
            sample_trace, complete_observations, db_session
        )
        
        # High quality data should have good score and few issues
        assert quality_score >= 0.7  # Should be high quality
        assert isinstance(quality_issues, list)
        # With complete data, should have minimal issues
        assert len(quality_issues) <= 1

    @pytest.mark.asyncio
    async def test_analyze_trace_data_quality_low_quality(self, sample_trace, incomplete_observations, db_session):
        """Test data quality analysis with low-quality data."""
        quality_score, quality_issues = await DataQualityService.analyze_trace_data_quality(
            sample_trace, incomplete_observations, db_session
        )
        
        # Low quality data should have lower score and more issues
        assert quality_score < 0.7  # Should be lower quality
        assert isinstance(quality_issues, list)
        assert len(quality_issues) > 0  # Should detect issues

    @pytest.mark.asyncio
    async def test_analyze_trace_data_quality_empty_observations(self, sample_trace, db_session):
        """Test data quality analysis with no observations."""
        quality_score, quality_issues = await DataQualityService.analyze_trace_data_quality(
            sample_trace, [], db_session
        )
        
        # No observations should result in very low quality
        assert quality_score == 0.0
        assert isinstance(quality_issues, list)
        assert len(quality_issues) > 0  # Should detect missing observations

    @pytest.mark.asyncio
    async def test_analyze_single_observation_quality_complete(self):
        """Test quality analysis of a single complete observation."""
        observation = Observation(
            id=uuid.uuid4(),
            trace_id=uuid.uuid4(),
            external_id="complete-obs",
            platform_type="langfuse",
            start_time=datetime.utcnow(),
            raw_data={
                "id": "complete-obs",
                "type": "generation",
                "input": {"prompt": "Complete prompt with details"},
                "output": {"text": "Complete response with context"},
                "metadata": {
                    "model": "gpt-4",
                    "tokens": 150,
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        score, issues = await DataQualityService._analyze_single_observation_quality(observation)
        
        # Complete observation should have high score
        assert score >= 0.8
        assert len(issues) == 0  # No issues with complete data

    @pytest.mark.asyncio
    async def test_analyze_single_observation_quality_incomplete(self):
        """Test quality analysis of a single incomplete observation."""
        observation = Observation(
            id=uuid.uuid4(),
            trace_id=uuid.uuid4(),
            external_id="incomplete-obs",
            platform_type="langfuse",
            start_time=datetime.utcnow(),
            raw_data={
                "id": "incomplete-obs",
                "type": "generation",
                "input": None,  # Missing input
                "output": {"text": ""},  # Empty output
                "metadata": {}  # Empty metadata
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        score, issues = await DataQualityService._analyze_single_observation_quality(observation)
        
        # Incomplete observation should have low score
        assert score < 0.5
        assert len(issues) > 0  # Should detect multiple issues

    @pytest.mark.asyncio
    async def test_analyze_single_observation_quality_malformed(self):
        """Test quality analysis with malformed raw_data."""
        observation = Observation(
            id=uuid.uuid4(),
            trace_id=uuid.uuid4(),
            external_id="malformed-obs",
            platform_type="langfuse",
            start_time=datetime.utcnow(),
            raw_data={},  # Empty raw_data
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        score, issues = await DataQualityService._analyze_single_observation_quality(observation)
        
        # Malformed data should have very low score
        assert score < 0.3
        assert len(issues) > 0

    @pytest.mark.asyncio
    async def test_update_trace_quality_metrics_success(self, db_session):
        """Test successful update of trace quality metrics."""
        trace_id = str(uuid.uuid4())
        quality_score = 0.85
        quality_issues = [
            {
                "issue_type": "empty_field", 
                "severity": "low",
                "description": "Empty metadata field",
                "observation_id": "obs-1"
            }
        ]
        
        with patch('app.repositories.trace_repository.TraceRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.update_quality_metrics.return_value = True
            
            success = await DataQualityService.update_trace_quality_metrics(
                trace_id, quality_score, quality_issues, db_session
            )
            
            assert success is True
            mock_repo_class.assert_called_once_with(db_session)
            mock_repo.update_quality_metrics.assert_called_once_with(
                trace_id, quality_score, quality_issues
            )

    @pytest.mark.asyncio
    async def test_update_trace_quality_metrics_failure(self, db_session):
        """Test handling of update failure."""
        trace_id = str(uuid.uuid4())
        quality_score = 0.75
        quality_issues = []
        
        with patch('app.repositories.trace_repository.TraceRepository') as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.update_quality_metrics.side_effect = Exception("Database error")
            
            success = await DataQualityService.update_trace_quality_metrics(
                trace_id, quality_score, quality_issues, db_session
            )
            
            assert success is False

    def test_calculate_completeness_score_perfect(self):
        """Test completeness score calculation with perfect data."""
        complete_data = {
            "id": "obs-1",
            "type": "generation",
            "input": {"prompt": "Complete prompt"},
            "output": {"text": "Complete output"},
            "metadata": {"model": "gpt-4", "tokens": 150}
        }
        
        score = DataQualityService._calculate_completeness_score(complete_data)
        assert score == 1.0

    def test_calculate_completeness_score_partial(self):
        """Test completeness score calculation with partial data."""
        partial_data = {
            "id": "obs-1",
            "type": "generation",
            "input": {"prompt": "Prompt"},
            "output": None,  # Missing output
            "metadata": {}   # Empty metadata
        }
        
        score = DataQualityService._calculate_completeness_score(partial_data)
        assert 0.0 < score < 1.0  # Should be between 0 and 1

    def test_calculate_completeness_score_empty(self):
        """Test completeness score calculation with empty data."""
        empty_data = {}
        
        score = DataQualityService._calculate_completeness_score(empty_data)
        assert score == 0.0

    def test_detect_quality_issues_comprehensive(self):
        """Test comprehensive quality issue detection."""
        problematic_data = {
            "id": "obs-1",
            "type": "generation",
            "input": None,      # Null input
            "output": {"text": ""},  # Empty output
            "metadata": {}      # Empty metadata
        }
        
        issues = DataQualityService._detect_quality_issues(problematic_data, "obs-1")
        
        # Should detect multiple types of issues
        issue_types = [issue["issue_type"] for issue in issues]
        assert "null_field" in issue_types
        assert "empty_field" in issue_types
        assert len(issues) >= 2

    def test_detect_quality_issues_good_data(self):
        """Test quality issue detection with good data."""
        good_data = {
            "id": "obs-1",
            "type": "generation",
            "input": {"prompt": "Good prompt"},
            "output": {"text": "Good output"},
            "metadata": {"model": "gpt-4", "tokens": 150}
        }
        
        issues = DataQualityService._detect_quality_issues(good_data, "obs-1")
        
        # Should detect no issues
        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_quality_scoring_consistency(self, sample_trace, db_session):
        """Test that quality scoring is consistent across multiple runs."""
        observations = [
            Observation(
                id=uuid.uuid4(),
                trace_id=sample_trace.id,
                external_id="consistent-obs",
                platform_type="langfuse",
                start_time=datetime.utcnow(),
                raw_data={
                    "id": "consistent-obs",
                    "type": "generation",
                    "input": {"prompt": "Consistent test"},
                    "output": {"text": "Consistent result"},
                    "metadata": {"model": "gpt-4"}
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        # Run analysis multiple times
        results = []
        for _ in range(3):
            score, issues = await DataQualityService.analyze_trace_data_quality(
                sample_trace, observations, db_session
            )
            results.append((score, len(issues)))
        
        # Results should be consistent
        scores = [r[0] for r in results]
        issue_counts = [r[1] for r in results]
        
        assert all(abs(s - scores[0]) < 0.01 for s in scores)  # Scores within 1%
        assert all(c == issue_counts[0] for c in issue_counts)  # Same issue count

    @pytest.mark.asyncio
    async def test_quality_analysis_edge_cases(self, sample_trace, db_session):
        """Test quality analysis with edge cases."""
        edge_case_observations = [
            # Very large data
            Observation(
                id=uuid.uuid4(),
                trace_id=sample_trace.id,
                external_id="large-obs",
                platform_type="langfuse",
                start_time=datetime.utcnow(),
                raw_data={
                    "id": "large-obs",
                    "input": {"data": "x" * 10000},  # Very large input
                    "output": {"data": "y" * 10000}, # Very large output
                    "metadata": {f"key_{i}": f"value_{i}" for i in range(100)}  # Many metadata fields
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            # Unicode data
            Observation(
                id=uuid.uuid4(),
                trace_id=sample_trace.id,
                external_id="unicode-obs",
                platform_type="langfuse",
                start_time=datetime.utcnow(),
                raw_data={
                    "id": "unicode-obs",
                    "input": {"prompt": "这是中文测试 🚀"},
                    "output": {"text": "Это русский тест ✨"},
                    "metadata": {"language": "mixed", "emoji": "🔥"}
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        # Should handle edge cases without crashing
        quality_score, quality_issues = await DataQualityService.analyze_trace_data_quality(
            sample_trace, edge_case_observations, db_session
        )
        
        assert isinstance(quality_score, float)
        assert 0.0 <= quality_score <= 1.0
        assert isinstance(quality_issues, list)