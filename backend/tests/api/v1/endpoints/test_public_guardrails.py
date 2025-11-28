"""
Guardrail evaluation endpoint tests.

Tests for POST /api/v1/public/guardrails/evaluate endpoint.
Comprehensive tests covering multiple guardrail types, actions, and conditions.
"""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.core.security import extract_key_prefix, generate_api_key, hash_api_key
from app.models.agent import AgentAPIKey
from app.models.guardrail import GuardrailActiveStatus, GuardrailAgentAssignment
from app.models.guardrail_evaluation_log import GuardrailEvaluationLog
from tests.repositories.conftest import (
    seed_test_agent,
    seed_test_guardrail,
    seed_test_membership,
    seed_test_organization,
    seed_test_project,
    seed_test_user,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
async def guardrail_test_setup(integration_client, test_db_engine):
    """
    Create complete test setup for guardrail evaluation tests.

    Uses the same session pool as integration_client to ensure data visibility.
    Data is committed to the database and will be cleaned up by integration_client fixture.

    Returns:
        dict: Contains org, user, project, agent, and auth headers
    """
    # Import session factory from conftest
    from tests.conftest import TestAsyncSessionLocal

    # Create a new session from the same pool as integration_client
    async with TestAsyncSessionLocal() as session:
        # Create organization, user, and membership
        org = await seed_test_organization(session)
        user = await seed_test_user(session)
        await seed_test_membership(
            session, user.id, org.id, is_owner=True, is_admin=True
        )

        # Create project and assign user as member/owner
        from app.models.project import ProjectMember, ProjectOwner

        project = await seed_test_project(
            session, organization_id=org.id, created_by=user.id
        )
        project_member = ProjectMember(project_id=project.id, user_id=user.id)
        session.add(project_member)
        project_owner = ProjectOwner(project_id=project.id, user_id=user.id)
        session.add(project_owner)

        # Create agent
        agent = await seed_test_agent(
            session,
            project_id=project.id,
            organization_id=org.id,
            created_by=user.id,
        )

        # Generate Agent API Key
        api_key = generate_api_key()
        key_prefix = extract_key_prefix(api_key, prefix_length=16)
        key_hash = hash_api_key(api_key)

        agent_api_key = AgentAPIKey(
            agent_id=agent.id,
            key_prefix=key_prefix,
            key_hash=key_hash,
            name="Test API Key",
            expires_at=None,
            created_by=user.id,
        )
        session.add(agent_api_key)

        # Commit all data so integration_client can see it
        await session.commit()

        # Refresh objects to get committed state
        await session.refresh(org)
        await session.refresh(user)
        await session.refresh(project)
        await session.refresh(agent)

        # Create auth headers with Agent API Key
        auth_headers = {"Authorization": f"Bearer {api_key}"}

        return {
            "org": org,
            "user": user,
            "project": project,
            "agent": agent,
            "auth_headers": auth_headers,
            "api_key": api_key,
        }


async def create_and_assign_guardrail(
    project_id, org_id, user_id, agent_id, name, definition
):
    """
    Helper to create a guardrail and assign it to an agent.

    Creates a new session from TestAsyncSessionLocal to ensure data is committed
    and visible to integration_client.

    Args:
        project_id: Project UUID
        org_id: Organization UUID
        user_id: User UUID (creator)
        agent_id: Agent UUID
        name: Guardrail name
        definition: Guardrail definition (JSONB)

    Returns:
        Guardrail: Created and assigned guardrail
    """
    # Import session factory
    from tests.conftest import TestAsyncSessionLocal

    # Create new session from same pool as integration_client
    async with TestAsyncSessionLocal() as session:
        # seed_test_guardrail already creates GuardrailActiveStatus by default
        guardrail = await seed_test_guardrail(
            session,
            project_id=project_id,
            organization_id=org_id,
            created_by=user_id,
            name=name,
            with_active_status=True,
        )

        # Update definition
        guardrail.definition = definition
        session.add(guardrail)

        # Assign to agent
        assignment = GuardrailAgentAssignment(
            guardrail_id=guardrail.id,
            agent_id=agent_id,
            project_id=project_id,
            assigned_by=user_id,
        )
        session.add(assignment)

        # Commit so integration_client can see it
        await session.commit()
        await session.refresh(guardrail)
        return guardrail


async def verify_evaluation_log(
    request_id: str,
    agent_id: UUID,
    project_id: UUID,
    organization_id: UUID,
    timing: str,
    process_type: str,
    process_name: str,
    should_proceed: bool,
    trace_id: str | None = None,
):
    """
    Verify that evaluation log was saved to database with correct data.

    Args:
        request_id: Expected request ID
        agent_id: Expected agent ID
        project_id: Expected project ID
        organization_id: Expected organization ID
        timing: Expected timing (on_start/on_end)
        process_type: Expected process type
        process_name: Expected process name
        should_proceed: Expected should_proceed value
        trace_id: Optional trace ID
    """
    from tests.conftest import TestAsyncSessionLocal

    async with TestAsyncSessionLocal() as session:
        # Query log by request_id
        stmt = select(GuardrailEvaluationLog).where(
            GuardrailEvaluationLog.request_id == request_id
        )
        result = await session.execute(stmt)
        log = result.scalar_one_or_none()

        # Verify log exists
        assert log is not None, f"Evaluation log not found for request_id: {request_id}"

        # Verify basic fields
        assert log.request_id == request_id
        assert log.agent_id == agent_id
        assert log.project_id == project_id
        assert log.organization_id == organization_id
        assert log.timing == timing
        assert log.process_type == process_type
        assert log.should_proceed == should_proceed

        # Verify trace_id if provided
        if trace_id:
            assert log.trace_id == trace_id

        # Verify log_data structure
        assert log.log_data is not None
        assert "process_name" in log.log_data
        assert log.log_data["process_name"] == process_name
        assert "request_context" in log.log_data
        assert "evaluated_guardrail_ids" in log.log_data
        assert "triggered_guardrail_ids" in log.log_data
        assert "evaluation_result" in log.log_data
        assert "evaluation_time_ms" in log.log_data

        # Verify evaluation_result structure
        eval_result = log.log_data["evaluation_result"]
        assert "triggered_guardrails" in eval_result
        assert "metadata" in eval_result

        # Verify metadata
        metadata = eval_result["metadata"]
        assert "evaluation_time_ms" in metadata
        assert "evaluated_guardrails_count" in metadata
        assert "triggered_guardrails_count" in metadata

        return log


# ============================================================================
# Test Cases
# ============================================================================


@pytest.mark.asyncio
async def test_block_action_contains_on_start(integration_client, guardrail_test_setup):
    """
    Test block action with contains operator on on_start timing.

    Scenario: Block requests containing prohibited keywords in input.

    Expected:
        - Guardrail triggers on prohibited keyword
        - Block action returns should_block=true
        - should_proceed=false (processing blocked)
    """
    setup = guardrail_test_setup

    # Create guardrail: Block if input contains "prohibited"
    definition = {
        "trigger": {
            "type": "on_start",
            "logic": "or",
            "conditions": [
                {
                    "field": "input.query",
                    "operator": "contains",
                    "value": "prohibited",
                }
            ],
        },
        "actions": [
            {
                "type": "block",
                "priority": 1,
                "config": {"message": "Prohibited keyword detected"},
            }
        ],
        "metadata": {
            "description": "Block prohibited keywords",
            "tags": ["security"],
            "severity": "high",
        },
    }

    await create_and_assign_guardrail(
        setup["project"].id,
        setup["org"].id,
        setup["user"].id,
        setup["agent"].id,
        "Block Prohibited Keywords",
        definition,
    )

    # Test request with prohibited keyword
    payload = {
        "trace_id": "trace_001",
        "process_name": "user_query",
        "process_type": "llm",
        "timing": "on_start",
        "context": {"input": {"query": "This contains prohibited content"}},
    }

    response = await integration_client.post(
        "/api/v1/public/guardrails/evaluate",
        json=payload,
        headers=setup["auth_headers"],
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()

    assert "request_id" in data
    assert "triggered_guardrails" in data
    assert "should_proceed" in data
    assert "metadata" in data

    # Should not proceed (blocked)
    assert data["should_proceed"] is False

    # Check triggered guardrail
    assert len(data["triggered_guardrails"]) == 1
    triggered = data["triggered_guardrails"][0]
    assert triggered["triggered"] is True
    assert triggered["error"] is False
    assert len(triggered["matched_conditions"]) == 1
    assert triggered["matched_conditions"][0] == 0

    # Check block action
    assert len(triggered["actions"]) == 1
    action = triggered["actions"][0]
    assert action["action_type"] == "block"
    assert action["priority"] == 1
    assert action["result"]["should_block"] is True
    assert "Prohibited keyword detected" in action["result"]["message"]

    # Verify evaluation log was saved to database
    await verify_evaluation_log(
        request_id=data["request_id"],
        agent_id=setup["agent"].id,
        project_id=setup["project"].id,
        organization_id=setup["org"].id,
        timing="on_start",
        process_type="llm",
        process_name="user_query",
        should_proceed=False,
        trace_id="trace_001",
    )


@pytest.mark.asyncio
async def test_warn_action_allow_proceed_true(integration_client, guardrail_test_setup):
    """
    Test warn action with allow_proceed=true on on_end timing.

    Scenario: Warn when output is too long but allow processing to continue.

    Expected:
        - Guardrail triggers on long output
        - Warn action issued
        - should_proceed=true (processing continues)
    """
    setup = guardrail_test_setup

    # Create guardrail: Warn if output is too long
    definition = {
        "trigger": {
            "type": "on_end",
            "logic": "and",
            "conditions": [
                {
                    "field": "output.content",
                    "operator": "size_gt",
                    "value": 100,
                }
            ],
        },
        "actions": [
            {
                "type": "warn",
                "priority": 1,
                "config": {
                    "message": "Output is very long (>100 chars)",
                    "severity": "medium",
                    "allow_proceed": True,
                },
            }
        ],
    }

    await create_and_assign_guardrail(
        setup["project"].id,
        setup["org"].id,
        setup["user"].id,
        setup["agent"].id,
        "Warn Long Output",
        definition,
    )

    # Test request with long output
    long_content = "x" * 150  # 150 characters
    payload = {
        "process_name": "llm_response",
        "process_type": "llm",
        "timing": "on_end",
        "context": {
            "input": {"query": "test"},
            "output": {"content": long_content},
        },
    }

    response = await integration_client.post(
        "/api/v1/public/guardrails/evaluate",
        json=payload,
        headers=setup["auth_headers"],
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()

    # Should proceed (warning only)
    assert data["should_proceed"] is True

    # Check triggered guardrail
    assert len(data["triggered_guardrails"]) == 1
    triggered = data["triggered_guardrails"][0]
    assert triggered["triggered"] is True

    # Check warn action
    assert len(triggered["actions"]) == 1
    action = triggered["actions"][0]
    assert action["action_type"] == "warn"
    assert action["result"]["severity"] == "medium"
    assert "long" in action["result"]["warning_message"].lower()

    # Verify evaluation log was saved to database
    await verify_evaluation_log(
        request_id=data["request_id"],
        agent_id=setup["agent"].id,
        project_id=setup["project"].id,
        organization_id=setup["org"].id,
        timing="on_end",
        process_type="llm",
        process_name="llm_response",
        should_proceed=True,
    )


@pytest.mark.asyncio
async def test_warn_action_allow_proceed_false(
    integration_client, guardrail_test_setup
):
    """
    Test warn action with allow_proceed=false (blocking warn).

    Scenario: Warn and block when output exceeds critical threshold.

    Expected:
        - Guardrail triggers on very long output
        - Warn action with allow_proceed=false
        - should_proceed=false (processing blocked by warn)
    """
    setup = guardrail_test_setup

    # Create guardrail: Block with warning if output too long
    definition = {
        "trigger": {
            "type": "on_end",
            "logic": "and",
            "conditions": [
                {
                    "field": "output.content",
                    "operator": "size_gt",
                    "value": 1000,
                }
            ],
        },
        "actions": [
            {
                "type": "warn",
                "priority": 1,
                "config": {
                    "message": "Output exceeds critical length (>1000 chars)",
                    "severity": "critical",
                    "allow_proceed": False,
                },
            }
        ],
    }

    await create_and_assign_guardrail(
        setup["project"].id,
        setup["org"].id,
        setup["user"].id,
        setup["agent"].id,
        "Critical Length Check",
        definition,
    )

    # Test request with very long output
    very_long_content = "x" * 1500
    payload = {
        "process_name": "llm_response",
        "process_type": "llm",
        "timing": "on_end",
        "context": {
            "input": {"query": "test"},
            "output": {"content": very_long_content},
        },
    }

    response = await integration_client.post(
        "/api/v1/public/guardrails/evaluate",
        json=payload,
        headers=setup["auth_headers"],
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()

    # Should NOT proceed (blocked by warn action)
    assert data["should_proceed"] is False

    # Check triggered guardrail
    triggered = data["triggered_guardrails"][0]
    assert triggered["triggered"] is True

    # Check warn action with blocking
    action = triggered["actions"][0]
    assert action["action_type"] == "warn"
    assert action["result"]["severity"] == "critical"

    # Verify evaluation log was saved to database
    await verify_evaluation_log(
        request_id=data["request_id"],
        agent_id=setup["agent"].id,
        project_id=setup["project"].id,
        organization_id=setup["org"].id,
        timing="on_end",
        process_type="llm",
        process_name="llm_response",
        should_proceed=False,
    )


@pytest.mark.asyncio
async def test_modify_action_drop_field(integration_client, guardrail_test_setup):
    """
    Test modify action with drop_field modification type.

    Scenario: Remove email field from output when it contains email address.

    Expected:
        - Guardrail triggers on email pattern
        - Modify action drops sensitive field
        - should_proceed=true (processing continues with modified data)
        - Modified data returned in action result
    """
    setup = guardrail_test_setup

    # Create guardrail: Drop email field if present
    definition = {
        "trigger": {
            "type": "on_end",
            "logic": "and",
            "conditions": [
                {
                    "field": "output.user_info.email",
                    "operator": "regex",
                    "value": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                }
            ],
        },
        "actions": [
            {
                "type": "modify",
                "priority": 1,
                "config": {
                    "modification_type": "drop_field",
                    "target": "output.user_info",
                    "condition": {
                        "fields": ["email"],
                        "operator": "is_null",
                        "value": None,
                    },
                },
            }
        ],
    }

    await create_and_assign_guardrail(
        setup["project"].id,
        setup["org"].id,
        setup["user"].id,
        setup["agent"].id,
        "Remove Email Field",
        definition,
    )

    # Test request with email in output
    payload = {
        "process_name": "user_data_fetch",
        "process_type": "tool",
        "timing": "on_end",
        "context": {
            "input": {"user_id": "123"},
            "output": {
                "user_info": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "123-456-7890",
                }
            },
        },
    }

    response = await integration_client.post(
        "/api/v1/public/guardrails/evaluate",
        json=payload,
        headers=setup["auth_headers"],
    )

    # Assertions
    assert response.status_code == 200
    data = response.json()

    # Should proceed (modify allows continuation)
    assert data["should_proceed"] is True

    # Check triggered guardrail
    triggered = data["triggered_guardrails"][0]
    assert triggered["triggered"] is True

    # Check modify action
    action = triggered["actions"][0]
    assert action["action_type"] == "modify"
    assert action["result"]["modification_type"] == "drop_field"
    assert "modified_data" in action["result"]

    # Verify evaluation log was saved to database
    await verify_evaluation_log(
        request_id=data["request_id"],
        agent_id=setup["agent"].id,
        project_id=setup["project"].id,
        organization_id=setup["org"].id,
        timing="on_end",
        process_type="tool",
        process_name="user_data_fetch",
        should_proceed=True,
    )


@pytest.mark.asyncio
async def test_multiple_conditions_and_logic(integration_client, guardrail_test_setup):
    """
    Test multiple conditions with AND logic.

    Scenario: Block only when ALL conditions are met.

    Expected:
        - Guardrail triggers only when both conditions match
        - Should NOT trigger when only one condition matches
    """
    setup = guardrail_test_setup

    # Create guardrail: Block if query contains "sensitive" AND token_count > 50
    definition = {
        "trigger": {
            "type": "on_start",
            "logic": "and",
            "conditions": [
                {
                    "field": "input.query",
                    "operator": "contains",
                    "value": "sensitive",
                },
                {
                    "field": "input.token_count",
                    "operator": "gt",
                    "value": 50,
                },
            ],
        },
        "actions": [
            {
                "type": "block",
                "priority": 1,
                "config": {"message": "Sensitive data with high token count"},
            }
        ],
    }

    await create_and_assign_guardrail(
        setup["project"].id,
        setup["org"].id,
        setup["user"].id,
        setup["agent"].id,
        "AND Condition Test",
        definition,
    )

    # Test 1: Both conditions match - should trigger
    payload_both = {
        "process_name": "test",
        "process_type": "llm",
        "timing": "on_start",
        "context": {"input": {"query": "This is sensitive data", "token_count": 100}},
    }

    response = await integration_client.post(
        "/api/v1/public/guardrails/evaluate",
        json=payload_both,
        headers=setup["auth_headers"],
    )

    data = response.json()
    assert data["should_proceed"] is False  # Blocked
    assert data["triggered_guardrails"][0]["triggered"] is True
    assert len(data["triggered_guardrails"][0]["matched_conditions"]) == 2

    # Verify evaluation log for first request
    await verify_evaluation_log(
        request_id=data["request_id"],
        agent_id=setup["agent"].id,
        project_id=setup["project"].id,
        organization_id=setup["org"].id,
        timing="on_start",
        process_type="llm",
        process_name="test",
        should_proceed=False,
    )

    # Test 2: Only first condition matches - should NOT trigger
    payload_partial = {
        "process_name": "test",
        "process_type": "llm",
        "timing": "on_start",
        "context": {"input": {"query": "This is sensitive data", "token_count": 30}},
    }

    response = await integration_client.post(
        "/api/v1/public/guardrails/evaluate",
        json=payload_partial,
        headers=setup["auth_headers"],
    )

    data = response.json()
    assert data["should_proceed"] is True  # Not blocked
    assert data["triggered_guardrails"][0]["triggered"] is False

    # Verify evaluation log for second request
    await verify_evaluation_log(
        request_id=data["request_id"],
        agent_id=setup["agent"].id,
        project_id=setup["project"].id,
        organization_id=setup["org"].id,
        timing="on_start",
        process_type="llm",
        process_name="test",
        should_proceed=True,
    )


@pytest.mark.asyncio
async def test_multiple_conditions_or_logic(integration_client, guardrail_test_setup):
    """
    Test multiple conditions with OR logic.

    Scenario: Block when ANY condition is met.

    Expected:
        - Guardrail triggers when at least one condition matches
        - Should trigger even if only one condition matches
    """
    setup = guardrail_test_setup

    # Create guardrail: Block if query contains "word1" OR "word2"
    definition = {
        "trigger": {
            "type": "on_start",
            "logic": "or",
            "conditions": [
                {
                    "field": "input.query",
                    "operator": "contains",
                    "value": "forbidden1",
                },
                {
                    "field": "input.query",
                    "operator": "contains",
                    "value": "forbidden2",
                },
                {
                    "field": "input.query",
                    "operator": "contains",
                    "value": "forbidden3",
                },
            ],
        },
        "actions": [
            {
                "type": "block",
                "priority": 1,
                "config": {"message": "Forbidden keyword detected"},
            }
        ],
    }

    await create_and_assign_guardrail(
        setup["project"].id,
        setup["org"].id,
        setup["user"].id,
        setup["agent"].id,
        "OR Condition Test",
        definition,
    )

    # Test 1: First condition matches
    payload_first = {
        "process_name": "test",
        "process_type": "llm",
        "timing": "on_start",
        "context": {"input": {"query": "This contains forbidden1 keyword"}},
    }

    response = await integration_client.post(
        "/api/v1/public/guardrails/evaluate",
        json=payload_first,
        headers=setup["auth_headers"],
    )

    data = response.json()
    assert data["should_proceed"] is False  # Blocked
    assert data["triggered_guardrails"][0]["triggered"] is True
    assert 0 in data["triggered_guardrails"][0]["matched_conditions"]

    # Verify evaluation log for first request
    await verify_evaluation_log(
        request_id=data["request_id"],
        agent_id=setup["agent"].id,
        project_id=setup["project"].id,
        organization_id=setup["org"].id,
        timing="on_start",
        process_type="llm",
        process_name="test",
        should_proceed=False,
    )

    # Test 2: Second condition matches
    payload_second = {
        "process_name": "test",
        "process_type": "llm",
        "timing": "on_start",
        "context": {"input": {"query": "This contains forbidden2 keyword"}},
    }

    response = await integration_client.post(
        "/api/v1/public/guardrails/evaluate",
        json=payload_second,
        headers=setup["auth_headers"],
    )

    data = response.json()
    assert data["should_proceed"] is False  # Blocked
    assert data["triggered_guardrails"][0]["triggered"] is True
    assert 1 in data["triggered_guardrails"][0]["matched_conditions"]

    # Verify evaluation log for second request
    await verify_evaluation_log(
        request_id=data["request_id"],
        agent_id=setup["agent"].id,
        project_id=setup["project"].id,
        organization_id=setup["org"].id,
        timing="on_start",
        process_type="llm",
        process_name="test",
        should_proceed=False,
    )

    # Test 3: No conditions match
    payload_none = {
        "process_name": "test",
        "process_type": "llm",
        "timing": "on_start",
        "context": {"input": {"query": "This is safe content"}},
    }

    response = await integration_client.post(
        "/api/v1/public/guardrails/evaluate",
        json=payload_none,
        headers=setup["auth_headers"],
    )

    data = response.json()
    assert data["should_proceed"] is True  # Not blocked
    assert data["triggered_guardrails"][0]["triggered"] is False

    # Verify evaluation log for third request
    await verify_evaluation_log(
        request_id=data["request_id"],
        agent_id=setup["agent"].id,
        project_id=setup["project"].id,
        organization_id=setup["org"].id,
        timing="on_start",
        process_type="llm",
        process_name="test",
        should_proceed=True,
    )


@pytest.mark.asyncio
async def test_invalid_api_key_returns_401(integration_client):
    """
    Test that invalid API key returns 401 Unauthorized.

    Expected:
        - 401 status code
        - Authentication error message
    """
    invalid_headers = {"Authorization": "Bearer agt_live_invalid_key_12345"}

    payload = {
        "process_name": "test",
        "process_type": "llm",
        "timing": "on_start",
        "context": {"input": {"query": "test"}},
    }

    response = await integration_client.post(
        "/api/v1/public/guardrails/evaluate",
        json=payload,
        headers=invalid_headers,
    )

    assert response.status_code == 401
    assert "Invalid or expired API key" in response.json()["detail"]


@pytest.mark.asyncio
async def test_missing_input_context_returns_422(
    integration_client, guardrail_test_setup
):
    """
    Test that request without 'input' in context returns 422.

    Expected:
        - 422 status code (Pydantic validation error)
        - Error message about missing input
    """
    setup = guardrail_test_setup

    # Invalid payload: missing 'input' in context
    payload = {
        "process_name": "test",
        "process_type": "llm",
        "timing": "on_start",
        "context": {},  # Missing 'input' key
    }

    response = await integration_client.post(
        "/api/v1/public/guardrails/evaluate",
        json=payload,
        headers=setup["auth_headers"],
    )

    assert response.status_code == 422
    # 422 responses have different structure (Pydantic validation error)
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_no_guardrails_assigned(integration_client, guardrail_test_setup):
    """
    Test evaluation when no guardrails are assigned to agent.

    Expected:
        - 200 status code
        - Empty triggered_guardrails list
        - should_proceed=true (no restrictions)
    """
    setup = guardrail_test_setup

    # Don't create any guardrails - just make request
    payload = {
        "process_name": "test",
        "process_type": "llm",
        "timing": "on_start",
        "context": {"input": {"query": "test query"}},
    }

    response = await integration_client.post(
        "/api/v1/public/guardrails/evaluate",
        json=payload,
        headers=setup["auth_headers"],
    )

    assert response.status_code == 200
    data = response.json()

    # Should proceed (no guardrails to block)
    assert data["should_proceed"] is True
    assert len(data["triggered_guardrails"]) == 0
    assert data["metadata"]["evaluated_guardrails_count"] == 0
    assert data["metadata"]["triggered_guardrails_count"] == 0

    # Verify evaluation log was saved to database (even with no guardrails)
    await verify_evaluation_log(
        request_id=data["request_id"],
        agent_id=setup["agent"].id,
        project_id=setup["project"].id,
        organization_id=setup["org"].id,
        timing="on_start",
        process_type="llm",
        process_name="test",
        should_proceed=True,
    )
