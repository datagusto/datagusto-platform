import json
import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.trace import Trace, Observation
from app.repositories.trace_repository import TraceRepository

logger = logging.getLogger(__name__)


class DataQualityService:
    """Service for calculating data quality metrics for AI agent traces."""

    @staticmethod
    async def analyze_trace_data_quality(
        trace: Trace, observations: List[Observation], db: Session
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Analyze data quality for a complete trace and its observations.

        Args:
            trace: The trace to analyze
            observations: List of observations for the trace
            db: Database session

        Returns:
            Tuple of (quality_score, quality_issues)
        """
        logger.info(f"Starting data quality analysis for trace {trace.id}")

        # Filter observations to only include those without child observations
        leaf_observations = DataQualityService._filter_leaf_observations(observations)
        logger.info(
            f"Filtered {len(observations)} observations to {len(leaf_observations)} leaf observations"
        )

        all_issues = []
        total_quality_score = 0.0
        analyzed_observations = 0

        # Analyze each leaf observation for tool calling data quality
        for observation in leaf_observations:
            try:
                logger.info(
                    f"Analyzing observation: id={observation.id}, external_id={observation.external_id}"
                )
                (
                    observation_issues,
                    observation_score,
                ) = await DataQualityService._analyze_observation_data_quality(
                    observation
                )

                if observation_issues or observation_score is not None:
                    all_issues.extend(observation_issues)
                    if observation_score is not None:
                        total_quality_score += observation_score
                        analyzed_observations += 1

            except Exception as e:
                logger.warning(f"Failed to analyze observation {observation.id}: {e}")
                # Add error as quality issue
                # all_issues.append(
                #     {
                #         "observation_id": str(observation.id),
                #         "issue_type": "analysis_error",
                #         "severity": "medium",
                #         "description": f"Failed to analyze observation data: {str(e)}",
                #         "timestamp": datetime.utcnow().isoformat(),
                #     }
                # )

        # Calculate overall trace quality score
        if analyzed_observations > 0:
            overall_quality_score = total_quality_score / analyzed_observations
        else:
            overall_quality_score = 0.0
            # all_issues.append(
            #     {
            #         "trace_id": str(trace.id),
            #         "issue_type": "no_analyzable_data",
            #         "severity": "low",
            #         "description": "No tool calling observations found to analyze",
            #         "timestamp": datetime.utcnow().isoformat(),
            #     }
            # )

        logger.info(
            f"Data quality analysis completed for trace {trace.id}: "
            f"score={overall_quality_score:.2f}, issues={len(all_issues)}"
        )

        return overall_quality_score, all_issues

    @staticmethod
    def _filter_leaf_observations(observations: List[Observation]) -> List[Observation]:
        """
        Filter observations to only include those without child observations.

        Args:
            observations: List of all observations

        Returns:
            List of observations that don't have child observations
        """
        # Create a set of all observation IDs that are parents
        parent_ids = set()
        for observation in observations:
            parent_observation_id = observation.raw_data["parentObservationId"]
            if parent_observation_id is not None:
                parent_ids.add(parent_observation_id)
        # Filter observations to only include those that are not parents
        leaf_observations = []
        for observation in observations:
            if observation.raw_data["id"] in parent_ids:
                continue
            leaf_observations.append(observation)

        return leaf_observations

    @staticmethod
    async def _analyze_observation_data_quality(
        observation: Observation,
    ) -> Tuple[List[Dict[str, Any]], Optional[float]]:
        """
        Analyze data quality for a single observation.

        Args:
            observation: The observation to analyze

        Returns:
            Tuple of (quality_issues, quality_score)
        """
        quality_issues = []

        # Check if this is a tool calling observation
        if not DataQualityService._is_tool_calling_observation(observation):
            return quality_issues, None

        print(observation.id, observation.raw_data["name"])

        try:
            # Extract output data from observation
            # output_data = DataQualityService._extract_output_data(observation)
            output_data = observation.raw_data["output"]

            if not output_data:
                return quality_issues, 1.0

            if isinstance(output_data, list):
                if "messages" in output_data[0]:
                    output_data = output_data[0]["messages"][0]["content"]

            # Convert to DataFrame for analysis
            df = pd.DataFrame(output_data)

            # Analyze each column for data quality issues
            column_scores = []

            for column in df.columns:
                column_issues, column_score = (
                    DataQualityService._analyze_column_quality(
                        df, column, observation.id
                    )
                )
                quality_issues.extend(column_issues)
                column_scores.append(column_score)

            # Calculate overall observation quality score
            observation_score = (
                sum(column_scores) / len(column_scores) if column_scores else 0.0
            )

            return quality_issues, observation_score

        except Exception as e:
            logger.error(f"Error analyzing observation {observation.id}: {e}")
            # quality_issues.append(
            #     {
            #         "observation_id": str(observation.id),
            #         "issue_type": "analysis_error",
            #         "severity": "medium",
            #         "description": f"Failed to analyze observation: {str(e)}",
            #         "timestamp": datetime.utcnow().isoformat(),
            #     }
            # )
            return quality_issues, 1.0

    @staticmethod
    def _is_tool_calling_observation(observation: Observation) -> bool:
        """Check if observation represents a tool calling action."""
        raw_data = observation.raw_data

        # Check for Langfuse tool calling patterns
        if observation.platform_type == "langfuse":
            # Check if observation_metadata contains tool node information
            if "metadata" in raw_data:
                metadata = raw_data["metadata"]
                if isinstance(metadata, dict) and "langgraph_node" in metadata:
                    return "tool" in metadata["langgraph_node"]

        return False

    @staticmethod
    def _extract_output_data(
        observation: Observation,
    ) -> Optional[List[Dict[str, Any]]]:
        """Extract structured output data from observation."""
        raw_data = observation.raw_data

        if observation.platform_type == "langfuse":
            output = raw_data.get("output")

            if not output:
                return None

            try:
                # Handle different output formats
                if isinstance(output, str):
                    output_data = json.loads(output)
                elif isinstance(output, dict):
                    output_data = output
                else:
                    return None

                # Extract content if wrapped
                if isinstance(output_data, dict) and "content" in output_data:
                    content = output_data["content"]
                    if isinstance(content, str):
                        content = json.loads(content)
                    output_data = content

                # Ensure we have a list of dictionaries for DataFrame creation
                if isinstance(output_data, list):
                    return output_data
                elif isinstance(output_data, dict):
                    return [output_data]
                else:
                    return None

            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse output data: {e}")
                return None

        return None

    @staticmethod
    def _analyze_column_quality(
        df: pd.DataFrame, column: str, observation_id: str
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Analyze data quality for a specific column.

        Args:
            df: DataFrame containing the data
            column: Column name to analyze
            observation_id: ID of the observation being analyzed

        Returns:
            Tuple of (quality_issues, quality_score)
        """
        quality_issues = []

        # Skip list columns for now (complex nested data)
        if df[column].apply(lambda x: isinstance(x, list)).any():
            return quality_issues, 1.0

        # Calculate basic quality metrics
        total_rows = len(df)
        null_count = df[column].isna().sum()
        non_null_values = df[column].dropna().tolist()
        unique_count = df[column].nunique()
        completeness = df[column].notna().mean()

        # Analyze value types
        value_types = set(type(val).__name__ for val in non_null_values)

        # Create field statistics
        field_stats = {
            "column": column,
            "types": list(value_types),
            "null_count": int(null_count),
            "unique_count": int(unique_count),
            "completeness": float(completeness),
            "total_rows": total_rows,
        }

        logger.info(f"Column {column} stats: {field_stats}")

        # Quality issue detection
        quality_score = 1.0

        # Check for high null percentage
        if completeness < 0.5:
            issue = {
                "observation_id": str(observation_id),
                "column": column,
                "quality_metrics": "completeness",
                "issue_type": "high_null_rate",
                "severity": "high",
                "description": f"Column has {completeness:.1%} completeness (>{null_count} nulls out of {total_rows} rows)",
                "metadata": field_stats,
                "timestamp": datetime.utcnow().isoformat(),
            }
            logger.info(f"Created quality issue: {issue}")
            quality_issues.append(issue)
            quality_score -= 0.5
        elif completeness < 0.8:
            issue = {
                "observation_id": str(observation_id),
                "column": column,
                "quality_metrics": "completeness",
                "issue_type": "moderate_null_rate",
                "severity": "medium",
                "description": f"Column has {completeness:.1%} completeness ({null_count} nulls out of {total_rows} rows)",
                "metadata": field_stats,
                "timestamp": datetime.utcnow().isoformat(),
            }
            logger.info(f"Created quality issue: {issue}")
            quality_issues.append(issue)
            quality_score -= 0.3

        # # Check for type inconsistency
        # if len(value_types) > 1:
        #     quality_issues.append(
        #         {
        #             "observation_id": str(observation_id),
        #             "column": column,
        #             "issue_type": "mixed_data_types",
        #             "severity": "medium",
        #             "description": f"Column contains mixed data types: {', '.join(value_types)}",
        #             "metrics": field_stats,
        #             "timestamp": datetime.utcnow().isoformat(),
        #         }
        #     )
        #     quality_score -= 0.2

        # # Check for low cardinality (potential data quality issue)
        # if total_rows > 10 and unique_count == 1 and completeness > 0:
        #     quality_issues.append(
        #         {
        #             "observation_id": str(observation_id),
        #             "column": column,
        #             "issue_type": "constant_value",
        #             "severity": "low",
        #             "description": f"Column has only one unique value across {total_rows} rows",
        #             "metrics": field_stats,
        #             "timestamp": datetime.utcnow().isoformat(),
        #         }
        #     )
        #     quality_score -= 0.1

        # Ensure quality score doesn't go below 0
        quality_score = max(0.0, quality_score)

        return quality_issues, quality_score

    @staticmethod
    async def update_trace_quality_metrics(
        trace_id: str,
        quality_score: float,
        quality_issues: List[Dict[str, Any]],
        db: Session,
    ) -> bool:
        """
        Update trace with calculated quality metrics.

        Args:
            trace_id: ID of the trace to update
            quality_score: Calculated quality score
            quality_issues: List of identified quality issues
            db: Database session

        Returns:
            True if update was successful
        """
        try:
            trace_repo = TraceRepository(db)

            update_data = {
                "quality_score": quality_score,
                "quality_issues": quality_issues,
            }

            trace = await trace_repo.get_trace_by_id(trace_id)
            if trace:
                await trace_repo.update_trace(trace, update_data)
                db.commit()
                logger.info(f"Updated quality metrics for trace {trace_id}")
                return True
            else:
                logger.warning(f"Trace {trace_id} not found for quality update")
                return False

        except Exception as e:
            logger.error(f"Failed to update quality metrics for trace {trace_id}: {e}")
            db.rollback()
            return False
