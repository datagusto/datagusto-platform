<p align="center">
    <h1 align="center"><b>datagusto</b></h1>
    <h3 align="center">Trace, Diagnose and Prevent AI Agents Unpredictability</h3>
</p>


<p align="center">
| <a href="#"><b>Quickstart</b></a> | <a href="#"><b>Documentation</b></a> | <a href="https://www.datagusto.ai"><b>Web Site</b></a> | <a href="https://datagusto.featurebase.app/"><b>Send Feedback</b></a> | 
</p>

datagusto provides step-by-step visibility into why AI agents fail — not just when they fail — with automated guardrails that prevent issues in real-time.

## News
- <b>April 20, 2025</b>: Released a major update for root cause analysis
- <b>April 4, 2025</b>: We launch the datagusto platform as open-source software

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

2. Create environment configuration
   ```bash
   cp .env.example .env
   ```
3. Provide `OPENAI_API_KEY` for the root cause analysis function
    ```
    $ vi .env

    OPENAI_API_KEY=sk-xxxxxxxxxx
    ```
3. Start the application
   ```bash
   docker compose up
   ```

4. Open http://localhost:3000 in your browser to access the datagusto UI.


### STEP 3: Integrating AI agents with datagusto
This guide helps you to integrate your AI agent's trace information with datagusto.

<b>(1) Add your AI agent information</b>
1. Create your account via http://localhost:3000/sign-up

    <img src=docs/assets/sc1.png width="500">

2. Add your AI agent via <b>[AI Agents] menu</b> > <b>[Add New Agent] button</b>    

    <img src=docs/assets/sc2.png width="500">

3. Input your AI agent infomation including Langfuse project credentials (`public_key`, `secret_key`, and `server`)

    <img src=docs/assets/sc3.png width="500">
    

<b>(2) Sync your AI agent's traces</b>
1. Go to your AI agent's detail page via <b>[AI Agents] menu</b> > <b>Choose your AI agent in the list</b>

    <img src=docs/assets/sc4.png width="500">

2. Click <b>[Sync data] button</b> to sync traces stored in Langfuse

    <img src=docs/assets/sc5.png width="500">

3. After syncing, you can see recent traces as below

    <img src=docs/assets/sc6.png width="500">

<b>Now you are ready for managing AI agent Unpredictability!</b>  
Once datagusto synced with Langfuse, you can see the status of all AI agent's traces.

### STEP 4: Root cause analysis for your AI agent’s traces

If your agent has any suspected incident, you can quickly review it by checking whether “Status” field indicates “INCIDENT” or not.

    <img src=docs/assets/sc7.png width="500">

If a trace has suspected incident logs, you can see what, where, and why the suspected incident happened.

    <img src=docs/assets/sc8.png width="500">


**NOTE:** Currently, datagusto check “Hallucination” for every trace with [this system prompt](https://github.com/datagusto/datagusto-platform/blob/b7b70059841c6a4cf04c79013bcfcbc8615984bb/backend/app/services/evaluation_service.py#L31-L44). We plan to support other types of incident checks soon. If you have any requests, please share it with us via our Feedback Portal!



## Feedback and Issue Reporting
If you have any feedback or discover any issues, please contact us through the board at the following link:
https://datagusto.featurebase.app/
