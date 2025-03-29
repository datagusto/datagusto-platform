<p align="center">
    <h1 align="center"><b>datagusto</b></h1>
    <h3 align="center">Trace, Diagnose and Prevent AI Agents Unpredictability</h3>
</p>


<p align="center">
| <a href="#"><b>Quickstart</b></a> | <a href="#"><b>Documentation</b></a> | <a href="https://www.datagusto.ai"><b>Web Site</b></a> | <a href="https://datagusto.featurebase.app/"><b>Send Feedback</b></a> | 
</p>

datagusto provides step-by-step visibility into why AI agents fail — not just when they fail — with automated guardrails that prevent issues in real-time.

## News

- <b>April 4, 2025</b>: We launch the datagusto platform as open-source software

## Get Started

### Self Hosting
This guide walk you through the steps to run datagusto platform locally using docker compose.

<b>Requirements</b>:  
- git
- docker & docker compose (use Docker Desktop on Windows or MacOS)

<b>Deployment</b>:  
1. Get a copy of the latest datagusto repository:
    ```bash
    git clone https://github.com/datagusto/datagusto-platform.git
    cd datagusto-platform
    ```

2. Create environment configuration
   ```bash
   cp .env.example .env
   ```

3. Start the application
   ```bash
   docker compose up
   ```

4. Open http://localhost:3000 in your browser to access the datagusto UI.


### Integrating AI agents with datagusto SDK
This guide helps you to integrate your AI agent with our SDK.
It will trace the example AI agent's logs to get you started.

<b>Issue new API key in datagusto platform</b>:  
1. Create your account via http://localhost:3000/sign-up
2. Add your agent via <b>[AI Agents] menu</b> > <b>[Add New Agent] button</b>
3. Go to the agent page and note down the API key starts with `sk-dg-`.

<b>Trace your first agent logs to datagusto</b>:  
This step will give a step-by-step guide with a LangGraph-based AI agent.

1. Install datagusto's SDK
    ```bash
    pip install datagusto-sdk
    ```

2. Integrate your agent code with SDK
    ```python
    # This agent is based on LangGraph's Routing Agent: https://langchain-ai.github.io/langgraph/tutorials/workflows/#routing
    import os

    from typing import Annotated
    from typing_extensions import TypedDict
    
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    
    from langgraph.graph import StateGraph
    from langgraph.graph.message import add_messages
    
    from datagusto.callback import LangchainCallbackHandler

    # datagusto setting
    os.environ["DATAGUSTO_SECRET_KEY"] = "sk-dg-xxx"
    os.environ["DATAGUSTO_HOST"] = "http://localhost:8000"
    handler = LangchainCallbackHandler()

    # your openai key
    os.environ["OPENAI_API_KEY"] = "sk-xxx"
    llm = ChatOpenAI(model = "gpt-4o-mini", temperature = 0.2)
    
    class State(TypedDict):
        messages: Annotated[list, add_messages]
    
    graph_builder = StateGraph(State)

    def chatbot(state: State):
        return {"messages": [llm.invoke(state["messages"])]}
    
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.set_entry_point("chatbot")
    graph_builder.set_finish_point("chatbot")

    graph = graph_builder.compile().with_config({"callbacks": [handler]})
    
    for s in graph.stream({"messages": [HumanMessage(content = "What is autonomous AI agent?")]}):
        print(s)
    ```

    - To integrate with the datagusto SDK, you'll need to set up environment variables:
        - Set `DATAGUSTO_SECRET_KEY` with your secret key
        - Set `DATAGUSTO_HOST` to `http://localhost:8000` to override the default value


## Feedback and Issue Reporting
If you have any feedback or discover any issues, please contact us through the board at the following link:
https://datagusto.featurebase.app/