from datetime import datetime
import os
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class IncidentHandleHistory(BaseModel):
    name: str = Field(description="The step name of the incident handling")
    description: str = Field(description="The description of the incident handling")
    timestamp: str = Field(description="The timestamp of the incident handling")


class HullcinationScore(BaseModel):
    score: float = Field(
        description="A score from 0.0 to 1.0 indicating the likelihood of hallucination (0 = no hallucination, 1 = definite hallucination)",
    )


class RootCauseAnalysis(BaseModel):
    root_cause: str = Field(description="The root cause of the issue")
    howto_fix: str = Field(description="The how to fix the root cause")


class IncidentDescription(BaseModel):
    description: str = Field(description="The description of the incident")


def check_hullicination(observation):
    llm = ChatOpenAI(model="gpt-4o-mini")
    structured_llm = llm.with_structured_output(HullcinationScore)
    prompt = f"""
    You are a helpful assistant that evaluates the likelihood of hallucination.
    Is the output below based solely on information contained in the input prompt? Please check if the output contains any information that contradicts facts or adds details not present in the prompt.

    Input prompt:
    {observation["input"]}

    Output:
    {observation["output"]}
    Please evaluate the likelihood of hallucination in the text and return a score between 0.0 and 1.0.

    1 = Completely hallucinated (contains many fabricated facts or contradictions)
    0 = No hallucination
    """
    result = structured_llm.invoke(prompt)
    return result.score


def root_cause_analysis(evaluation_results):
    not_good_observations = [
        ob for ob in evaluation_results["details"] if ob["quality"] != "Good"
    ]
    if len(not_good_observations) == 0:
        return {
            "number_of_issues": 0,
            "description": "There is no issue with the trace.",
            "history": None,
        }

    history = []

    history.append(
        IncidentHandleHistory(
            name="Issue Identification",
            description="Hullcination is identified in this trace.",
            timestamp=datetime.now().isoformat(),
        ).model_dump()
    )

    # Do root cause analysis for each not good observation
    llm = ChatOpenAI(model="gpt-4o-mini")
    structured_llm = llm.with_structured_output(RootCauseAnalysis)

    for ob in not_good_observations:
        # Find root cause of the issue
        prompt = f"""
        The following step has been identified as a hullicination.
        {ob["observation"]}

        Please analyze the root cause of the issue and return the root cause.
        """
        result = structured_llm.invoke(prompt)
        history.append(
            IncidentHandleHistory(
                name="Root Cause Identified",
                description=f"""Step {ob["observation"]["parentObservationId"]}
                Root Cause: {result.root_cause}
                How to fix: {result.howto_fix}""",
                timestamp=datetime.now().isoformat(),
            ).model_dump()
        )

    # generate incident description
    structured_llm = llm.with_structured_output(IncidentDescription)
    prompt = f"""
    The following is the root cause of the issue.
    {history}

    Please generate a brief description of the incident.
    """
    result = structured_llm.invoke(prompt)

    return {
        "number_of_issues": len(not_good_observations),
        "description": result.description,
        "history": history,
    }


def evaluate_observation(observation):
    return check_hullicination(observation)


def evaluate_trace(trace):
    has_children = {}
    for ob in trace["observations"]:
        if ob["parentObservationId"] is not None:
            has_children[ob["parentObservationId"]] = True

    evaluation_results = {"details": [], "root_cause": None}
    for ob in sorted(trace["observations"], key=lambda x: x["startTime"]):
        if has_children.get(ob["id"], False):
            continue
        score = evaluate_observation(ob)
        record = {"observationId": ob["id"], "observation": ob, "score": score}

        if score > 0.5:
            record["quality"] = "Hullicination"
        else:
            record["quality"] = "Good"

        evaluation_results["details"].append(record)

    root_cause = root_cause_analysis(evaluation_results)
    evaluation_results["root_cause"] = root_cause
    return evaluation_results
