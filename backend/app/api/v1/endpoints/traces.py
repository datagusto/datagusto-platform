from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.trace import Trace, TraceSyncStatus, TraceWithObservations
from app.services.trace_service import TraceService
from app.services.data_quality_service import DataQualityService

router = APIRouter()


@router.post("/{project_id}/sync", response_model=TraceSyncStatus)
async def manual_sync_traces(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Manually trigger trace sync from Langfuse for a project.
    
    This endpoint triggers an immediate sync of traces from the configured
    Langfuse instance for the specified project. It performs differential
    sync, only fetching new or updated traces since the last sync.
    
    Args:
        project_id: UUID of the project to sync traces for
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        TraceSyncStatus: Results of the sync operation including counts
        of new and updated traces, timing information, and any errors
        
    Raises:
        HTTPException: If project not found, user lacks access, or
        project is not configured for Langfuse
    """
    try:
        sync_result = await TraceService.sync_traces(str(project_id), str(current_user.id), db)
        
        if sync_result.error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sync failed: {sync_result.error}"
            )
        
        return sync_result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during sync"
        )


@router.get("/{project_id}", response_model=List[Trace])
async def get_project_traces(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
) -> Any:
    """
    Get traces for a project with pagination.
    
    Args:
        project_id: UUID of the project
        current_user: Currently authenticated user
        db: Database session
        limit: Maximum number of traces to return (default: 50)
        offset: Number of traces to skip (default: 0)
        
    Returns:
        List of traces ordered by timestamp (newest first)
        
    Raises:
        HTTPException: If project not found or user lacks access
    """
    try:
        traces = await TraceService.get_traces_by_project(
            str(project_id), str(current_user.id), db, limit, offset
        )
        return traces
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{project_id}/{trace_id}", response_model=TraceWithObservations)
async def get_trace_detail(
    project_id: UUID,
    trace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get detailed trace information including observations.
    
    Args:
        project_id: UUID of the project (for access control)
        trace_id: UUID of the trace to retrieve
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Trace with all its observations
        
    Raises:
        HTTPException: If trace not found or user lacks access
    """
    try:
        trace = await TraceService.get_trace_with_observations(
            str(trace_id), str(current_user.id), db
        )
        
        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trace not found"
            )
        
        return trace
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{project_id}/{trace_id}/observations", response_model=List[dict])
async def get_trace_observations(
    project_id: UUID,
    trace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get leaf observations (observations without children) for a specific trace.
    
    Args:
        project_id: UUID of the project (for access control)
        trace_id: UUID of the trace
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        List of leaf observations for the trace
        
    Raises:
        HTTPException: If trace not found or user lacks access
    """
    try:
        # Get trace with observations
        trace = await TraceService.get_trace_with_observations(
            str(trace_id), str(current_user.id), db
        )
        
        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trace not found"
            )
        
        # Filter to get only leaf observations (observations without children)
        leaf_observations = []
        if trace.observations:
            # First, collect all parent observation IDs
            parent_ids = set()
            for obs in trace.observations:
                raw_data = obs.raw_data
                if isinstance(raw_data, dict) and raw_data.get("parentObservationId"):
                    parent_ids.add(raw_data["parentObservationId"])
            
            # Then, filter observations that are not parents (leaf nodes)
            for obs in trace.observations:
                raw_data = obs.raw_data
                if isinstance(raw_data, dict) and raw_data.get("id"):
                    # If this observation's ID is not in parent_ids, it's a leaf
                    if raw_data["id"] not in parent_ids:
                        leaf_observations.append({
                            "id": str(obs.id),
                            "trace_id": str(obs.trace_id),
                            "parent_observation_id": str(obs.parent_observation_id) if obs.parent_observation_id else None,
                            "external_id": obs.external_id,
                            "platform_type": obs.platform_type,
                            "start_time": obs.start_time.isoformat() if obs.start_time else None,
                            "raw_data": obs.raw_data,
                            "created_at": obs.created_at.isoformat() if obs.created_at else None,
                            "updated_at": obs.updated_at.isoformat() if obs.updated_at else None,
                        })
                else:
                    # If raw_data doesn't have id field, include it as a potential leaf
                    leaf_observations.append({
                        "id": str(obs.id),
                        "trace_id": str(obs.trace_id),
                        "parent_observation_id": str(obs.parent_observation_id) if obs.parent_observation_id else None,
                        "external_id": obs.external_id,
                        "platform_type": obs.platform_type,
                        "start_time": obs.start_time.isoformat() if obs.start_time else None,
                        "raw_data": obs.raw_data,
                        "created_at": obs.created_at.isoformat() if obs.created_at else None,
                        "updated_at": obs.updated_at.isoformat() if obs.updated_at else None,
                    })
        
        return leaf_observations
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/{project_id}/{trace_id}/analyze-quality", response_model=dict)
async def reanalyze_trace_quality(
    project_id: UUID,
    trace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Re-analyze data quality for a specific trace.
    
    This endpoint triggers a fresh data quality analysis for the specified trace,
    recalculating quality scores and identifying any data quality issues in the
    trace's observations.
    
    Args:
        project_id: UUID of the project (for access control)
        trace_id: UUID of the trace to analyze
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Dictionary containing quality_score and quality_issues
        
    Raises:
        HTTPException: If trace not found or user lacks access
    """
    try:
        # Get trace with observations
        trace = await TraceService.get_trace_with_observations(
            str(trace_id), str(current_user.id), db
        )
        
        if not trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trace not found"
            )
        
        # Perform data quality analysis
        quality_score, quality_issues = await DataQualityService.analyze_trace_data_quality(
            trace, trace.observations, db
        )
        
        # Update trace with new quality metrics
        success = await DataQualityService.update_trace_quality_metrics(
            str(trace_id), quality_score, quality_issues, db
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update quality metrics"
            )
        
        return {
            "trace_id": str(trace_id),
            "quality_score": quality_score,
            "quality_issues": quality_issues,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during quality analysis"
        )


@router.get("/{project_id}/quality-summary", response_model=dict)
async def get_project_quality_summary(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get data quality summary for a project.
    
    Returns aggregated data quality metrics for all traces in the project,
    including average quality score, total number of issues, and breakdown
    by issue type.
    
    Args:
        project_id: UUID of the project
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Dictionary with quality summary statistics
        
    Raises:
        HTTPException: If project not found or user lacks access
    """
    try:
        # Get all traces for the project
        traces = await TraceService.get_traces_by_project(
            str(project_id), str(current_user.id), db, limit=1000, offset=0
        )
        
        # Calculate quality summary
        total_traces = len(traces)
        traces_with_quality = [t for t in traces if t.quality_score is not None]
        
        if not traces_with_quality:
            return {
                "project_id": str(project_id),
                "total_traces": total_traces,
                "analyzed_traces": 0,
                "average_quality_score": None,
                "total_issues": 0,
                "issue_breakdown": {},
                "quality_distribution": {}
            }
        
        # Calculate average quality score
        avg_quality = sum(t.quality_score for t in traces_with_quality) / len(traces_with_quality)
        
        # Count total issues and breakdown by type
        total_issues = 0
        issue_breakdown = {}
        
        for trace in traces_with_quality:
            if trace.quality_issues:
                total_issues += len(trace.quality_issues)
                for issue in trace.quality_issues:
                    issue_type = issue.get("issue_type", "unknown")
                    issue_breakdown[issue_type] = issue_breakdown.get(issue_type, 0) + 1
        
        # Calculate quality score distribution
        quality_distribution = {
            "excellent": len([t for t in traces_with_quality if t.quality_score >= 0.9]),
            "good": len([t for t in traces_with_quality if 0.7 <= t.quality_score < 0.9]),
            "fair": len([t for t in traces_with_quality if 0.5 <= t.quality_score < 0.7]),
            "poor": len([t for t in traces_with_quality if t.quality_score < 0.5])
        }
        
        return {
            "project_id": str(project_id),
            "total_traces": total_traces,
            "analyzed_traces": len(traces_with_quality),
            "average_quality_score": round(avg_quality, 3),
            "total_issues": total_issues,
            "issue_breakdown": issue_breakdown,
            "quality_distribution": quality_distribution,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )