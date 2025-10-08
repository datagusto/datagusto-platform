"""LangGraph single-node graph template.

Returns a predefined response. Replace logic and configuration as needed.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, TypedDict, cast

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from psycopg_pool import AsyncConnectionPool

from app.agent.prompts import (
    SYSTEM_PROMPT_AMBIGUITY_EXTRACTION,
    SYSTEM_PROMPT_DISAMBIGUATION,
    SYSTEM_PROMPT_SYSTEM_TIME,
)
from app.agent.state import State

session_store = {}
with open("session_store.json") as f:
    session_store = json.load(f)


def _extract_from_markdown_block(text: str) -> dict | None:
    """Extract from markdown block."""
    pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

    if matches:
        json_str = matches[-1].strip()
        return json_str

    return text


class Context(TypedDict):
    """Context parameters for the agent.

    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    my_configurable_param: str


async def extract(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    """Process input and returns output.

    Can use runtime context to alter behavior.
    """
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", max_tokens=20000)

    system_message = {
        "role": "system",
        "content": [
            {
                "type": "text",
                "text": SYSTEM_PROMPT_SYSTEM_TIME.format(
                    system_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
            },
            {
                "type": "text",
                "text": SYSTEM_PROMPT_AMBIGUITY_EXTRACTION,
                # "cache_control": {"type": "ephemeral"},
            },
        ],
    }

    user_prompt = f"""
    Instruction: {state.user_instruction}
    """

    user_message = {"role": "user", "content": user_prompt}

    response = cast(AIMessage, await llm.ainvoke([system_message, user_message]))
    result_raw = _extract_from_markdown_block(response.content)
    result = json.loads(result_raw)

    return {"all_ambiguities": result.get("all_ambiguities", [])}


async def lookup(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    """Lookup the ambiguity."""
    global session_store
    all_ambiguities = state.all_ambiguities
    result = []
    for ambiguity in all_ambiguities:
        if ambiguity["element"] in session_store:
            result.append(
                {
                    "element": ambiguity["element"],
                    "resolved_value": session_store[ambiguity["element"]],
                }
            )
    return {
        "historical_resolutions": result,
    }


async def resolve(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    """Process input and returns output.

    Can use runtime context to alter behavior.
    """
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", max_tokens=20000)

    system_message = {
        "role": "system",
        "content": [
            # {
            #     "type": "text",
            #     "text": SYSTEM_PROMPT_SYSTEM_TIME.format(
            #         system_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            #     ),
            # },
            {
                "type": "text",
                "text": SYSTEM_PROMPT_DISAMBIGUATION,
                # "cache_control": {"type": "ephemeral"},
            },
        ],
    }

    user_prompt = f"""
    Original Instruction: {state.user_instruction}
    All Ambiguities: {json.dumps(state.all_ambiguities, indent=2)}
    Historical Resolutions: {json.dumps(state.historical_resolutions, indent=2)}
    User Clarifications: {json.dumps(state.user_clarifications, indent=2)}
    """

    user_message = {"role": "user", "content": user_prompt}

    response = cast(AIMessage, await llm.ainvoke([system_message, user_message]))

    result_raw = _extract_from_markdown_block(response.content)

    result = json.loads(result_raw)

    return {
        "resolved_ambiguities": result.get("resolved_ambiguities", []),
        "unresolved_ambiguities": result.get("unresolved_ambiguities", []),
        "disambiguation_complete": result.get("disambiguation_complete", False),
    }


async def should_clarify(state: State) -> bool:
    """Check if the disambiguation is complete."""
    if len(state.unresolved_ambiguities) == 0:
        return "save"

    return "clarify"


async def clarify(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    """Clarify the ambiguity."""
    message = AIMessage(content="Please clarify the ambiguity.")
    return {"messages": [message]}


async def save(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    """Save the ambiguity."""
    global session_store
    for r in state.resolved_ambiguities:
        session_store[r["element"]] = r["resolved_value"]
    with open("session_store.json", "w") as f:
        json.dump(session_store, f, indent=2)
    with open("session_store.json") as f:
        session_store = json.load(f)
    return {"messages": [AIMessage(content="Saving the ambiguity.")]}


async def interrupt(state: State) -> dict:
    """中断ポイント：質問を準備."""
    return {
        "clarification_questions": [
            {
                "id": amb["id"],
                # "question": amb["question"],
                # "options": amb.get("options", []),
            }
            for amb in state.unresolved_ambiguities
        ]
    }


def should_interrupt(state: State) -> str:
    """中断すべきか判定"""
    if not state.disambiguation_complete:
        return "interrupt"
    return "continue"


graph_initial = (
    StateGraph(State, context_schema=Context)
    .add_node(extract)
    .add_node(lookup)
    .add_node(resolve)
    .add_node(should_interrupt)
    .add_node(interrupt)
    .add_node(save)
    .add_edge("__start__", "extract")
    .add_edge("extract", "lookup")
    .add_edge("lookup", "resolve")
    .add_conditional_edges(
        "resolve", should_interrupt, {"continue": "save", "interrupt": "interrupt"}
    )
    .add_edge("interrupt", "__end__")
    .add_edge("save", "__end__")
)

graph_resume = (
    StateGraph(State, context_schema=Context)
    .add_node(resolve)
    .add_node(interrupt)
    .add_node(save)
    .add_edge("__start__", "resolve")
    .add_conditional_edges(
        "resolve", should_interrupt, {"continue": "save", "interrupt": "interrupt"}
    )
    .add_edge("interrupt", "__end__")
    .add_edge("save", "__end__")
)


async def compile_graph(graph):
    DB_URI = "postgresql://postgres:postgres@localhost:5432/langgraph_checkpoint"
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
    }
    pool = AsyncConnectionPool(
        conninfo=DB_URI,
        max_size=5,
        kwargs=connection_kwargs,
    )
    checkpointer = AsyncPostgresSaver(pool)
    # checkpointer = PostgresSaver(pool)
    await checkpointer.setup()

    return graph.compile(name="New Graph", checkpointer=checkpointer)
