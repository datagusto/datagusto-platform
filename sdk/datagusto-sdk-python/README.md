# Datagusto SDK for Python

A data quality guardrail SDK for LangGraph agents that provides tools for ensuring data quality and governance in AI agent workflows.

## Features

- **Data Quality Guardrails**: Automatically filter out incomplete records with null/None values
- **LangGraph Integration**: Seamlessly integrates with LangGraph agents as a tool
- **API-Based Configuration**: Fetches guardrail rules from your Datagusto backend
- **Easy to Use**: Simple function calls that can be added to any LangGraph workflow

## Installation

```bash
pip install datagusto-sdk
```

## Quick Start

### 1. Set Environment Variables

```bash
export DATAGUSTO_API_KEY="your_api_key_here"
export DATAGUSTO_API_URL="http://localhost:8000"  # Optional, defaults to localhost:8000
```

### 2. Basic Usage with LangGraph

Simply add `datagusto_guardrail` to your existing tool set - no complex integration required!

```python
from datagusto_sdk import datagusto_guardrail
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model

# Initialize your tools including the datagusto guardrail
tool = TavilySearch(max_results=2)
tools = [tool, datagusto_guardrail]  # Just add datagusto_guardrail to your existing tools

# Set up your LLM with tools
llm = init_chat_model("anthropic:claude-3-5-sonnet-latest")
llm_with_tools = llm.bind_tools(tools)

# The guardrail will automatically be called after other tools to ensure data quality
```

## Complete Example

Here's a complete example of a LangGraph agent with Datagusto guardrails, based on the [LangGraph Add Tools tutorial](https://langchain-ai.github.io/langgraph/tutorials/get-started/2-add-tools/):

```python
import json
from typing import Annotated
from typing_extensions import TypedDict

from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_tavily import TavilySearch

from datagusto_sdk.langgraph.toolset import datagusto_guardrail

# Initialize tools
tool = TavilySearch(max_results=2)
tools = [tool, datagusto_guardrail]

# Set up LLM
llm = init_chat_model("anthropic:claude-3-5-sonnet-latest")
llm_with_tools = llm.bind_tools(tools)

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

class BasicToolNode:
    """A node that runs the tools requested in the last AIMessage."""
    
    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}
    
    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

tool_node = BasicToolNode(tools=[tool])

def route_tools(state: State):
    """Route to the ToolNode if the last message has tool calls."""
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END

# Build the graph
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)
graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    {"tools": "tools", END: END},
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile()

# Run the agent
def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)

if __name__ == "__main__":
    stream_graph_updates("What do you know about LangGraph?")
```

## Configuration

The SDK uses environment variables for configuration:

- `DATAGUSTO_API_KEY`: Your API key for authentication (required)
- `DATAGUSTO_API_URL`: The base URL of your Datagusto API (optional, defaults to `http://localhost:8000`)

## Requirements

- Python 3.8+
- langchain-core >= 0.1.0
- requests >= 2.25.0

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

