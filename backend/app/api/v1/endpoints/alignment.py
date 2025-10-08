import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.agent.graph import compile_graph, graph_initial, graph_resume

router = APIRouter()


class AlignmentRequest(BaseModel):
    """Request body for the alignment endpoint (dummy)."""

    session_id: str | None = None
    user_instruction: str


class AlignmentResponse(BaseModel):
    """Response body for the alignment endpoint (dummy)."""

    session_id: str
    all_ambiguities: list[dict[str, Any]]
    unresolved_ambiguities: list[dict[str, Any]]
    resolved_ambiguities: list[dict[str, Any]]
    next_instruction: str


@router.post("", response_model=AlignmentResponse)
async def create_alignment(request: AlignmentRequest) -> AlignmentResponse:
    """Dummy POST / endpoint that returns a static response."""

    session_id = request.session_id
    user_instruction = request.user_instruction

    if session_id is None:
        session_id = str(uuid.uuid4())
        graph = await compile_graph(graph_initial)
        initial_state = {
            "session_id": session_id,
            "user_instruction": user_instruction,
            "user_clarifications": [],
        }
        config = {"configurable": {"thread_id": session_id}}
        final_state = await graph.ainvoke(initial_state, config=config)

    else:
        graph = await compile_graph(graph_resume)
        config = {"configurable": {"thread_id": session_id}}
        saved_state = await graph.aget_state(config)
        current_state = saved_state.values.copy()
        current_state["user_clarifications"].append(user_instruction)
        final_state = await graph.ainvoke(current_state, config=config)

    if len(final_state["unresolved_ambiguities"]) > 0:
        unresolved_words = ", ".join(
            [
                ambiguity["element"]
                for ambiguity in final_state["unresolved_ambiguities"]
            ]
        )
        next_instruction = f"Continue to ask questions to resolve the ambiguities found in the user's instruction. Following words are still unresolved: {unresolved_words}"
    else:
        next_instruction = (
            "All ambiguities have been resolved. Please proceed to the next task."
        )

    result = AlignmentResponse(
        session_id=session_id,
        all_ambiguities=final_state.get("all_ambiguities", []),
        unresolved_ambiguities=final_state.get("unresolved_ambiguities", []),
        resolved_ambiguities=final_state.get("resolved_ambiguities", []),
        next_instruction=next_instruction,
    )

    return result
