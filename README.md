<p align="center">
    <h1 align="center"><b>datagusto</b></h1>
    <h3 align="center">Trace, Diagnose and Prevent AI Agents Unpredictability</h3>
</p>


<p align="center">
| <a href="#"><b>Quickstart</b></a> | <a href="#"><b>Documentation</b></a> | <a href="https://www.datagusto.ai"><b>Web Site</b></a> | <a href="https://datagusto.featurebase.app/"><b>Send Feedback</b></a> | 
</p>

datagusto provides step-by-step visibility into why AI agents fail — not just when they fail — with automated guardrails that prevent issues in real-time.

## Limitations
This product is designed to run analysis based on log data from LangFuse, so it requires an AI Agent managed by LangFuse and a properly configured LangFuse setup as prerequisites.
Prerequisites:

- An AI Agent that is actively managed and monitored through LangFuse
- A complete LangFuse setup with proper configuration and integration
- Active logging of agent interactions and performance data in LangFuse

The analysis functionality depends entirely on the availability and quality of the log data that LangFuse collects from your AI Agent operations.

## News
- <b>June 18, 2025</b>: Major update to support guardrails. Now you can control your AI agents based on data quality!

## Get Started

### STEP 1: Setup Langfuse project for your AI agents
Datagusto integrates with your LLM/agent observability platforms, such as Langfuse, to trace, diagnose and prevent AI agents unpredictability.
Currently, we are only supporting Langfuse. If you use other observability platforms, please share it with us via <a href="https://datagusto.featurebase.app/"><b>Feedback Portal</b></a>!

Before starting to set up datagusto, you need to set up a Langfuse project for your AI agents.

<b>(1) Create Langfuse project</b>  
According to [the Langfuse's guide](https://langfuse.com/docs/get-started), create a Langfuse project.

<b>(2) Connect your AI agent</b>
Issue API credentials in the project settings and connect with your AI agents to Langfuse.

There are Langfuse guides for some AI agent frameworks:
- [LangChain](https://langfuse.com/docs/integrations/langchain/tracing)
- [LangGraph](https://langfuse.com/docs/integrations/langchain/example-python-langgraph)
- [Mastra](https://langfuse.com/docs/integrations/mastra)

Now you are ready to set up datagusto!


### STEP 2: Set up datagusto
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

2. Start the application
   ```bash
   docker compose up
   ```

3. Open http://localhost:3000 in your browser to access the datagusto UI.


### STEP 3: Integrating AI agents with datagusto
This guide helps you to integrate your AI agent's trace information with datagusto.

<b>(1) Register your AI agent information</b>
1. Create your account via http://localhost:3000/sign-up

    <img src=docs/assets/sc1.png width="500">

2. Register your AI agent via <b>"Click to create" button</b>    

    <img src=docs/assets/sc2.png width="500">

3. Input your AI agent infomation including Langfuse project credentials (`public_key`, `secret_key`, and `server`)

    <img src=docs/assets/sc3.png width="300">
    

<b>(2) Sync your AI agent's traces</b>
1. Go to your AI agent's project trace page via <b>[Trace] menu</b>. Then, click <b>[Sync Trace] button</b> to sync traces stored in Langfuse

    <img src=docs/assets/sc4.png width="500">


2. After syncing, you can see recent traces as below

    <img src=docs/assets/sc5.png width="500">

<b>Now you are ready for managing AI agent unpredictability!</b>  
Once datagusto synced with Langfuse, you can see the status of all AI agent's traces.

### STEP 4: Root cause analysis for your AI agent's traces

If your agent has any suspected incident, you can quickly review it by checking whether "Status" field indicates "INCIDENT" or not.

If a trace has suspected incident logs, you can see what, where, and why the suspected incident happened.

<img src=docs/assets/sc6.png width="500">


### STEP 5: Guardrail to control your AI agent's behavior based on data quality

You can configure guradrails for your AI agents via <b>"Guardrail"</b> > <b>"Add Guardrail" button</b> 

<img src=docs/assets/sc7.png width="500">

Then, let's integrate your AI agent and datagusto!

<b>(1) Install the datagusto SDK</b>
```bash
pip install datagusto-sdk
```

<b>(2) Set up environment variables</b>
```bash
export DATAGUSTO_API_KEY="your_api_key_here"
export DATAGUSTO_API_URL="http://localhost:8000"
```

You can find your API key in the <b>"Project Settings"</b> menu.


<b>(3) Basic integration with LangGraph</b>

Simply add `datagusto_guardrail` to your existing tool set - no complex integration required!
The below is an example to add `datagusto_guardrail` to a LangGraph-based AI agent.

```python
from datagusto_sdk.langgraph.toolset import datagusto_guardrail
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

For detailed usage examples and advanced configuration, please refer to [the SDK's PyPI page](https://pypi.org/project/datagusto-sdk/).

## Feedback and Issue Reporting
If you have any feedback or discover any issues, please contact us through the board at the following link:
https://datagusto.featurebase.app/
