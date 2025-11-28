import json
import logging
import time
from datetime import datetime
from typing import Any
from uuid import UUID

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm import create_llm_client, get_llm_config
from app.repositories.session_alignment_history_repository import (
    SessionAlignmentHistoryRepository,
)
from app.repositories.session_validation_log_repository import (
    SessionValidationLogRepository,
)
from app.schemas.guardrail import GuardrailDefinition
from app.schemas.guardrail_evaluation import ActionResult, TriggeredGuardrail
from app.schemas.safety import KeyTermsOutput
from app.services.guardrail_evaluation.action_executor import (
    execute_block_action,
    execute_modify_action,
    execute_warn_action,
)
from app.services.guardrail_evaluation.condition_evaluator import evaluate_conditions
from app.services.guardrail_evaluation.exceptions import (
    ConditionEvaluationError,
    FieldPathResolutionError,
)
from app.services.guardrail_evaluation.should_proceed_calculator import (
    calculate_should_proceed_with_configs,
)
from app.services.session_service import SessionService
from app.services.tool_definition_service import ToolDefinitionService

logger = logging.getLogger(__name__)

KEYTERM_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Extract all key terms from the user's instruction history that could affect an AI agent's planning and actions.

## INPUTS:
1. Latest User Instruction (required): The most recent instruction from the user
2. Past Instructions History (optional): Record of previous user instructions in the same session
3. Previous Extraction Output (optional): JSON output from the previous execution of this process

## WHAT TO EXTRACT:
Identify terms from all instructions that are ambiguous or context-dependent, particularly:
- Time expressions without concrete dates
- Location references without specific paths or addresses
- Object references using pronouns or generic terms
- Actions without clear specifications
- Degree/scope expressions with subjective interpretation
- Conditions or constraints affecting execution
- References to previous context

## CRITICAL RULE for user_provided_context:

This field captures information that clarifies a term through:
1. **Explicit user statements**: The user directly provides specific details
2. **System information inference**: ONLY when user uses relative expressions that reference the system date
3. **Contextual inference**: Deduce clarification from other explicitly mentioned terms in the same instruction

user_provided_context must remain NULL when:
- The term appears without any clarification
- No explicit user details are provided
- The term is ambiguous and requires future clarification

## INFERENCE RULES:

**From System Information (ONLY for explicit relative references):**
Apply system date inference ONLY when user explicitly uses relative time expressions:
- "today", "今日" → resolve to actual date
- "this year", "今年", "今年度" → resolve to actual year/fiscal year
- "next week", "来週" → calculate specific date range
- "yesterday", "昨日" → resolve to actual date

DO NOT apply system date inference when:
- User mentions time periods without relative markers (e.g., "春学期", "Q3", "summer")
- User mentions past or future without specifying when

**From Contextual Clues:**
When user specifies details about one term, apply it to directly related terms in the same instruction:
- If user says "Project X report", then "report" → user_provided_context: "Project X report"
- Only apply when the relationship is explicit and immediate

**Strict Guidelines:**
- Do NOT add general meanings, translations, or explanations to user_provided_context
- Do NOT infer information beyond what user explicitly stated or directly implied
- Preserve ambiguity when clarification hasn't been provided
- Keep user_provided_context as null until actual clarification occurs

## ITERATIVE PROCESSING:

This extraction runs each time the user provides input. On subsequent runs:
1. Load all previously extracted terms as the base
2. Scan the latest instruction for clarifications of existing ambiguous terms
3. Apply explicit clarifications and only clear inferences
4. Update user_provided_context when new information becomes available
5. Add any new ambiguous terms found in the latest instruction
6. Preserve all existing terms (do not remove any)

## OUTPUT REQUIREMENTS:
- Extract comprehensively without filtering
- Maintain all terms from previous iterations
- Update user_provided_context only with explicit user information or clear relative time resolution
- Preserve ambiguity when appropriate
- Output valid JSON matching the schema

Today's date is {date}.""",
        ),
        (
            "human",
            """Latest User Instruction: {latest_user_instruction}

Past Instructions History: {past_instructions_history}

Previous Extraction Output: {previous_extraction_output}""",
        ),
    ]
)


class GeneratedGuardrail(BaseModel):
    """Generated guardrail from user instruction and key terms"""

    tool_name: str = Field(description="Name of the tool to invoke")
    condition: str = Field(
        description="Condition under which this tool should be invoked (natural language)"
    )
    parameters: dict[str, Any] = Field(
        description="Expected parameter values based on key terms"
    )
    reasoning: str = Field(description="Reasoning for why this tool should be invoked")
    guardrail_definition: GuardrailDefinition = Field(
        description="Guardrail definition with trigger conditions and actions"
    )


class GeneratedGuardrails(BaseModel):
    """Output containing generated guardrails"""

    guardrails: list[GeneratedGuardrail] = Field(
        description="List of generated guardrails"
    )
    disallowed_tools: list[str] = Field(
        description="List of tool names that should NOT be called for this instruction"
    )


GUARDRAIL_GENERATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Generate guardrails for AI agent tool invocations based on user instruction and context.

## INPUTS:
1. User Instruction: What the user wants to accomplish
2. Key Terms: Extracted terms with user-provided context
3. Available Tools: List of tools that can be invoked

## YOUR TASK:
Analyze the user instruction and generate guardrails that:
1. Determine which tools are needed and when they should be invoked
2. Define expected parameter values using information from key terms
3. Create runtime enforcement rules to validate tool invocations
4. Provide clear reasoning for each guardrail

## ANTI-PATTERNS (Do NOT generate these guardrails):
The following types of guardrails are NOT useful and should NOT be generated:
- UUID format validation (already validated by API layer)
- Data type checks (already validated by schema)
- Required field existence checks (already validated by API layer)
- Basic input format validation (already handled by the system)

These technical validations are redundant because the API layer already enforces them before guardrails are evaluated.

## MEANINGFUL GUARDRAILS (Generate these instead):

### Intent Alignment Verification
Verify that tool invocation parameters match the user's specified conditions:
- Time period constraints (e.g., "spring semester" should not access fall semester data)
- Target scope constraints (e.g., "my grades" should not access other users' data)
- Action type constraints (e.g., "retrieve" should not trigger update operations)

### Resource Relevance Verification
Verify that the resources being accessed are relevant to the user's instruction:
- Resources obtained from previous tool calls should be validated against user intent
- Accessed resource IDs should correspond to what the user explicitly requested
- Cross-reference with prior agent actions in the same session

### Operation Scope Limitation
Detect operations that exceed the user's explicitly permitted scope:
- Read-only requests should not trigger write operations
- Single-target requests should not trigger bulk operations
- Specific resource requests should not access unrelated resources

## LLM_JUDGE OPERATOR USAGE:

The evaluation context has the following structure:
- **context.input**: Tool input parameters (always available in both on_start and on_end)
- **context.output**: Tool output data (only available in on_end)

When validating requires semantic understanding or cross-referencing with previous agent actions, use the "llm_judge" operator.

**For on_start (validate input parameters):**
Use "field": "input" to validate the entire input object:
```json
{{
  "trigger": {{
    "type": "on_start",
    "conditions": [{{
      "field": "input",
      "operator": "llm_judge",
      "value": "Verify that input.file_id was obtained from a previous get_user_files call and corresponds to spring semester grade files"
    }}]
  }}
}}
```

**For on_end (validate output data):**
Use "field": "output" to validate the entire output object:
```json
{{
  "trigger": {{
    "type": "on_end",
    "conditions": [{{
      "field": "output",
      "operator": "llm_judge",
      "value": "Verify that output.content contains spring semester grade data, not other semesters"
    }}]
  }}
}}
```

Use llm_judge for:
- Validating semantic alignment between user intent and tool parameters
- Cross-referencing current tool call with previous tool outputs in the session
- Complex conditional logic that cannot be expressed with simple operators
- Verifying that accessed resources match user's specified criteria

## TRIGGER TIMING (on_start vs on_end):

Choose the appropriate trigger timing based on what can be validated:

**on_start (before tool execution)**:
- Use ONLY for conditions that can be verified from INPUT PARAMETERS
- Check the tool's input_schema to confirm the parameter exists before using it in conditions
- If a condition requires data not present in input_schema, do NOT use on_start

**on_end (after tool execution)**:
- Use for conditions that require examining the tool's OUTPUT
- Validate that returned data matches user's intent (e.g., correct semester, correct user's data)
- Verify that the retrieved resources are relevant to the user's instruction

**Example - "Get spring semester grades"**:
- on_start: Limited validation (input has no semester parameter)
- on_end: Verify returned data contains spring semester grades (output validation)

## GUARDRAIL COMPONENTS:

**Tool invocation metadata**:
- tool_name: Name of the tool to invoke
- condition: Natural language description of when to invoke
- parameters: Expected parameter values derived from key terms
- reasoning: Why this tool is appropriate for the user's instruction

**Guardrail definition** (for runtime enforcement):
- trigger.type: "on_start" (input validation) or "on_end" (output validation)
- trigger.conditions: Conditions based on available data at the chosen timing
- actions: What to do when conditions are met (block, warn, or modify)
- metadata.severity: Risk level ("low", "medium", "high", "critical")

## TOOL CATEGORIZATION:

For each available tool, categorize it as one of:
1. **Required with guardrails**: Tools needed for the instruction with specific validation rules
2. **Allowed without guardrails**: Tools that may be called with no validation needed
3. **Disallowed**: Tools that should NOT be called for this instruction

Output:
- `guardrails`: Guardrails for category 1 tools (Required with guardrails)
- `disallowed_tools`: List of tool names in category 3 (Disallowed)

Category 2 tools (Allowed without guardrails) are implicitly all tools not in either list.

## GUIDELINES:
- Generate guardrails for tools that need validation (category 1)
- List tools that should NOT be called in `disallowed_tools` (category 3)
- **CRITICAL**: Check the tool's input_schema before creating on_start conditions
- If the condition requires data not in input_schema, use on_end instead
- Focus on SEMANTIC validation, not technical format validation
- Use llm_judge when validation requires understanding context or previous actions
- Create guardrails that verify user INTENT alignment, not just data format
- Set higher severity for operations that could access or modify wrong resources
- Consider the entire user instruction context when defining validation criteria

Today's date is {date}.""",
        ),
        (
            "human",
            """User Instruction: {user_instruction}

Key Terms with Context:
{key_terms}

Available Tools:
{available_tools}""",
        ),
    ]
)


class SafetyService:
    """Service for handling safety operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the safety service.

        Args:
            db: Async database session
        """
        self.db = db
        self.session_service = SessionService(db)
        self.alignment_history_repo = SessionAlignmentHistoryRepository(db)
        self.validation_log_repo = SessionValidationLogRepository(db)

    async def alignment_session(
        self,
        agent_id: str,
        session_id: str | None,
        user_instruction: str,
    ):
        """
        Perform alignment session for a user instruction.

        Args:
            agent_id: Agent UUID as string
            session_id: Optional session UUID as string (creates new if None)
            user_instruction: Latest user instruction

        Returns:
            Tuple of (session_id, key_terms_output, generated_guardrails)
        """
        # Convert agent_id to UUID
        agent_uuid = UUID(agent_id)

        # Get or create session
        session = None
        try:
            if session_id:
                session = await self.session_service.get_session(UUID(session_id))
        except Exception:
            pass

        if not session:
            session = await self.session_service.create_session(agent_id=agent_uuid)
            session_id = session["id"]

        # Read the latest alignment history from the database
        latest_alignment_history = await self.session_service.get_latest_alignment(
            UUID(session_id)
        )

        # Extract past instructions and previous extraction output
        past_instructions_history = None
        previous_extraction_output = None

        if latest_alignment_history:
            past_instructions_history = latest_alignment_history.get(
                "past_instructions_history"
            )
            previous_extraction_output = latest_alignment_history.get(
                "previous_extraction_output"
            )

        # Extract key terms in the user instruction
        key_terms_output = await self.extract_key_terms_in_user_instruction(
            latest_user_instruction=user_instruction,
            past_instructions_history=past_instructions_history,
            previous_extraction_output=previous_extraction_output,
        )

        # Read the latest tool definitions from the database
        tool_service = ToolDefinitionService(self.db)
        tools_data, revision_id = await tool_service.get_latest_revision(agent_uuid)

        # Generate guardrails (tool invocation rules)
        if tools_data:
            generated_guardrails_result = await self.generate_guardrails(
                user_instruction=user_instruction,
                key_terms=key_terms_output,
                tools_data=tools_data,
            )
        else:
            generated_guardrails_result = None

        # Store the result in the database
        # Build alignment result with key_terms, tool_invocation_rules, and disallowed_tools
        alignment_result = {
            "key_terms": [term.model_dump() for term in key_terms_output.key_terms]
            if hasattr(key_terms_output, "key_terms")
            else [],
            "tool_invocation_rules": [
                rule.model_dump()
                for rule in (
                    generated_guardrails_result.guardrails
                    if generated_guardrails_result
                    else []
                )
            ],
            "disallowed_tools": (
                generated_guardrails_result.disallowed_tools
                if generated_guardrails_result
                else []
            ),
        }

        # Save alignment history
        await self.session_service.add_alignment_history(
            session_id=UUID(session_id),
            user_instruction=user_instruction,
            past_instructions_history=past_instructions_history,
            previous_extraction_output=previous_extraction_output,
            alignment_result=alignment_result,
        )

        return session_id, key_terms_output, generated_guardrails_result

    async def extract_key_terms_in_user_instruction(
        self,
        latest_user_instruction: str,
        past_instructions_history: str | None = None,
        previous_extraction_output: str | None = None,
    ) -> KeyTermsOutput:
        config = get_llm_config()
        llm = create_llm_client(config)

        structured_llm = llm.with_structured_output(KeyTermsOutput)
        chain = KEYTERM_EXTRACTION_PROMPT | structured_llm
        result = await chain.ainvoke(
            {
                "latest_user_instruction": latest_user_instruction,
                "past_instructions_history": past_instructions_history,
                "previous_extraction_output": previous_extraction_output,
                "date": datetime.now().strftime("%Y-%m-%d"),
            }
        )
        return result

    async def generate_guardrails(
        self,
        user_instruction: str,
        key_terms: KeyTermsOutput,
        tools_data: dict[str, Any],
    ) -> GeneratedGuardrails:
        """
        Generate guardrails based on user instruction.

        Args:
            user_instruction: User's instruction text
            key_terms: Extracted key terms with context
            tools_data: Tool definitions data from database

        Returns:
            GeneratedGuardrails containing guardrails and disallowed_tools
        """
        config = get_llm_config()
        llm = create_llm_client(config)

        structured_llm = llm.with_structured_output(GeneratedGuardrails)
        chain = GUARDRAIL_GENERATION_PROMPT | structured_llm

        result = await chain.ainvoke(
            {
                "user_instruction": user_instruction,
                "key_terms": json.dumps(
                    key_terms.model_dump()
                    if hasattr(key_terms, "model_dump")
                    else key_terms,
                    ensure_ascii=False,
                ),
                "available_tools": json.dumps(tools_data, ensure_ascii=False),
                "date": datetime.now().strftime("%Y-%m-%d"),
            }
        )

        return result

    async def validate_session_guardrails(
        self,
        session_id: UUID,
        agent_id: UUID,
        project_id: UUID,
        organization_id: UUID,
        trace_id: str | None,
        process_name: str,
        process_type: str,
        timing: str,
        context: dict[str, Any],
    ) -> tuple[bool, list[TriggeredGuardrail], dict[str, Any]]:
        """
        Validate tool/LLM invocation against session-generated guardrails.

        Args:
            session_id: Session UUID containing guardrails
            agent_id: Agent making the request
            project_id: Project the agent belongs to
            organization_id: Organization (for logging)
            trace_id: Optional external trace ID
            process_name: Name of the process being evaluated
            process_type: Type of process (llm, tool, retrieval, agent)
            timing: When to evaluate (on_start or on_end)
            context: Evaluation context data

        Returns:
            Tuple of (should_proceed, triggered_guardrails, metadata)

        Example:
            >>> should_proceed, triggered, metadata = await service.validate_session_guardrails(
            ...     session_id, agent_id, project_id, org_id, None,
            ...     "get_exam_results", "tool", "on_start",
            ...     {"input": {"semester": "spring"}}
            ... )
        """
        start_time = time.time()

        logger.info(
            f"Starting session validation for session {session_id}, "
            f"process={process_name}, timing={timing}"
        )

        # Get guardrails and disallowed_tools from session
        guardrails, disallowed_tools = await self._get_guardrails_from_session(
            session_id, timing
        )

        # Check disallowed_tools first
        if process_name in disallowed_tools:
            logger.warning(
                f"Tool '{process_name}' is in disallowed_tools for session {session_id}"
            )
            evaluation_time_ms = int((time.time() - start_time) * 1000)

            blocked_guardrail = TriggeredGuardrail(
                guardrail_id="disallowed_tool",
                guardrail_name=f"disallowed_{process_name}",
                triggered=True,
                error=False,
                matched_conditions=[],
                actions=[
                    ActionResult(
                        action_type="block",
                        priority=0,
                        result={
                            "should_block": True,
                            "message": f"Tool '{process_name}' is not allowed for this instruction",
                        },
                    )
                ],
            )

            metadata = {
                "evaluation_time_ms": evaluation_time_ms,
                "blocked_by": "disallowed_tools",
                "evaluated_guardrails_count": 0,
            }

            await self._save_validation_log(
                session_id=session_id,
                agent_id=agent_id,
                project_id=project_id,
                organization_id=organization_id,
                trace_id=trace_id,
                process_name=process_name,
                process_type=process_type,
                timing=timing,
                context=context,
                should_proceed=False,
                triggered_guardrails=[blocked_guardrail],
                metadata=metadata,
            )

            return False, [blocked_guardrail], metadata

        if not guardrails:
            logger.info(
                f"No guardrails found for session {session_id} with timing={timing}"
            )
            # No guardrails to evaluate - proceed
            return True, [], {"evaluated_guardrails_count": 0}

        triggered_guardrails_list: list[TriggeredGuardrail] = []
        guardrail_definitions: dict[str, dict[str, Any]] = {}

        # Evaluate each guardrail
        for idx, guardrail_data in enumerate(guardrails):
            guardrail_definition = guardrail_data.get("guardrail_definition", {})
            guardrail_name = guardrail_data.get("tool_name", f"guardrail_{idx}")
            guardrail_id = f"session_guardrail_{idx}"

            guardrail_definitions[guardrail_id] = guardrail_definition

            triggered_result = await self._evaluate_single_guardrail(
                guardrail_id=guardrail_id,
                guardrail_name=guardrail_name,
                guardrail_definition=guardrail_definition,
                context=context,
            )

            triggered_guardrails_list.append(triggered_result)

        # Calculate should_proceed
        should_proceed = calculate_should_proceed_with_configs(
            [tg.model_dump() for tg in triggered_guardrails_list], guardrail_definitions
        )

        # Calculate evaluation time
        evaluation_time_ms = int((time.time() - start_time) * 1000)

        # Count triggered guardrails
        triggered_count = sum(
            1 for tg in triggered_guardrails_list if tg.triggered and not tg.error
        )

        metadata = {
            "evaluation_time_ms": evaluation_time_ms,
            "evaluated_guardrails_count": len(guardrails),
            "triggered_guardrails_count": triggered_count,
        }

        # Save validation log
        await self._save_validation_log(
            session_id=session_id,
            agent_id=agent_id,
            project_id=project_id,
            organization_id=organization_id,
            trace_id=trace_id,
            process_name=process_name,
            process_type=process_type,
            timing=timing,
            context=context,
            should_proceed=should_proceed,
            triggered_guardrails=triggered_guardrails_list,
            metadata=metadata,
        )

        logger.info(
            f"Session validation completed for {session_id}: should_proceed={should_proceed}, "
            f"triggered={triggered_count}/{len(guardrails)}, time={evaluation_time_ms}ms"
        )

        return should_proceed, triggered_guardrails_list, metadata

    async def _get_guardrails_from_session(
        self, session_id: UUID, timing: str
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """
        Get guardrails and disallowed_tools from session alignment history.

        Args:
            session_id: Session UUID
            timing: Evaluation timing (on_start or on_end)

        Returns:
            Tuple of (filtered_guardrails, disallowed_tools)

        Example:
            >>> guardrails, disallowed = await service._get_guardrails_from_session(
            ...     session_id, "on_start"
            ... )
        """
        # Get latest alignment history for this session
        alignment_history = await self.alignment_history_repo.get_latest_by_session(
            session_id
        )

        if not alignment_history:
            logger.warning(f"No alignment history found for session {session_id}")
            return [], []

        # Extract guardrails and disallowed_tools from alignment_result
        alignment_result = alignment_history.alignment_result or {}
        tool_invocation_rules = alignment_result.get("tool_invocation_rules", [])
        disallowed_tools = alignment_result.get("disallowed_tools", [])

        # Filter by timing
        filtered_guardrails = []
        for rule in tool_invocation_rules:
            guardrail_def = rule.get("guardrail_definition", {})
            trigger = guardrail_def.get("trigger", {})
            trigger_type = trigger.get("type")

            if trigger_type == timing:
                filtered_guardrails.append(rule)

        logger.debug(
            f"Found {len(filtered_guardrails)} guardrails for session {session_id} "
            f"with timing={timing}, disallowed_tools={disallowed_tools}"
        )

        return filtered_guardrails, disallowed_tools

    async def _evaluate_single_guardrail(
        self,
        guardrail_id: str,
        guardrail_name: str,
        guardrail_definition: dict[str, Any],
        context: dict[str, Any],
    ) -> TriggeredGuardrail:
        """
        Evaluate a single guardrail.

        Args:
            guardrail_id: Guardrail identifier
            guardrail_name: Guardrail name
            guardrail_definition: Guardrail definition with trigger and actions
            context: Evaluation context

        Returns:
            TriggeredGuardrail result

        Example:
            >>> result = await service._evaluate_single_guardrail(
            ...     "gr_1", "check_semester", definition, context
            ... )
        """
        try:
            trigger = guardrail_definition.get("trigger", {})
            conditions = trigger.get("conditions", [])
            logic = trigger.get("logic", "and")

            # Evaluate conditions
            triggered, matched_indices = evaluate_conditions(context, conditions, logic)

            if not triggered:
                # Not triggered
                return TriggeredGuardrail(
                    guardrail_id=guardrail_id,
                    guardrail_name=guardrail_name,
                    triggered=False,
                    error=False,
                    matched_conditions=[],
                    actions=[],
                )

            # Execute actions
            actions_config = guardrail_definition.get("actions", [])
            action_results: list[ActionResult] = []

            for action_config in actions_config:
                action_type = action_config.get("type")

                try:
                    if action_type == "block":
                        result = execute_block_action(
                            action_config, context, matched_indices, conditions
                        )
                    elif action_type == "warn":
                        result = execute_warn_action(action_config)
                    elif action_type == "modify":
                        result = execute_modify_action(action_config, context)
                    else:
                        logger.warning(f"Unknown action type: {action_type}")
                        continue

                    action_results.append(ActionResult(**result))

                except Exception as e:
                    logger.error(f"Action execution error: {str(e)}")
                    # Continue with other actions

            return TriggeredGuardrail(
                guardrail_id=guardrail_id,
                guardrail_name=guardrail_name,
                triggered=True,
                error=False,
                matched_conditions=matched_indices,
                actions=action_results,
            )

        except (FieldPathResolutionError, ConditionEvaluationError) as e:
            # Known evaluation errors
            logger.error(f"Guardrail evaluation error for {guardrail_name}: {str(e)}")
            return TriggeredGuardrail(
                guardrail_id=guardrail_id,
                guardrail_name=guardrail_name,
                triggered=False,
                error=True,
                error_message=str(e),
                matched_conditions=[],
                actions=[],
            )

        except Exception as e:
            # Unexpected errors
            logger.error(
                f"Unexpected error evaluating guardrail {guardrail_name}: {str(e)}"
            )
            return TriggeredGuardrail(
                guardrail_id=guardrail_id,
                guardrail_name=guardrail_name,
                triggered=False,
                error=True,
                error_message=f"Unexpected error: {str(e)}",
                matched_conditions=[],
                actions=[],
            )

    async def _save_validation_log(
        self,
        session_id: UUID,
        agent_id: UUID,
        project_id: UUID,
        organization_id: UUID,
        trace_id: str | None,
        process_name: str,
        process_type: str,
        timing: str,
        context: dict[str, Any],
        should_proceed: bool,
        triggered_guardrails: list[TriggeredGuardrail],
        metadata: dict[str, Any],
    ) -> None:
        """
        Save session validation log to database.

        Args:
            session_id: Session UUID
            agent_id: Agent UUID
            project_id: Project UUID
            organization_id: Organization UUID
            trace_id: Optional external trace ID
            process_name: Process name
            process_type: Process type
            timing: Evaluation timing
            context: Evaluation context
            should_proceed: Final decision
            triggered_guardrails: List of triggered guardrails
            metadata: Evaluation metadata
        """
        log_data = {
            "process_name": process_name,
            "process_type": process_type,
            "timing": timing,
            "should_proceed": should_proceed,
            "request_context": context,
            "evaluation_result": {
                "triggered_guardrails": [
                    tg.model_dump(mode="json") for tg in triggered_guardrails
                ],
                "metadata": metadata,
            },
        }

        try:
            await self.validation_log_repo.create(
                {
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "project_id": project_id,
                    "organization_id": organization_id,
                    "trace_id": trace_id,
                    "log_data": log_data,
                }
            )
            await self.db.commit()
            logger.debug(f"Saved validation log for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save validation log: {str(e)}", exc_info=True)
            # Don't fail the request if logging fails
            await self.db.rollback()
