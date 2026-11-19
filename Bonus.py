from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    question: str
    query: str
    evidence: str | None
    retries: int
    answer: str


DOCUMENTS = {
    "billing database": "The billing service uses PostgreSQL.",
}


def decide(state: State):
    print("decide")
    return {"query": state["question"].lower().rstrip("?")}


def route_question(state: State):
    # In the full demo, the model decides whether to request a search.
    if "our " in state["query"]:
        return "retrieve"
    return "answer"


def retrieve(state: State):
    print(f"retrieve: {state['query']!r}")
    return {"evidence": DOCUMENTS.get(state["query"])}


def grade(state: State):
    print(f"grade: evidence found = {state['evidence'] is not None}")
    return {}


def route_evidence(state: State):
    if state["evidence"]:
        return "answer"
    if state["retries"] == 0:
        return "rewrite"
    return "review"


def rewrite(state: State):
    query = state["query"].removeprefix("our ")
    print(f"rewrite: {query!r}")
    return {"query": query, "retries": state["retries"] + 1}


def answer(state: State):
    print("answer")
    return {
        "answer": state["evidence"] or "An index helps a database find rows faster."
    }


def review(state: State):
    print("review")
    return {"answer": "Needs human review: no supporting document found."}


builder = StateGraph(State)

builder.add_node("decide", decide)
builder.add_node("retrieve", retrieve)
builder.add_node("grade", grade)
builder.add_node("rewrite", rewrite)
builder.add_node("answer", answer)
builder.add_node("review", review)

builder.add_edge(START, "decide")
builder.add_conditional_edges("decide", route_question)
builder.add_edge("retrieve", "grade")
builder.add_conditional_edges("grade", route_evidence)
builder.add_edge("rewrite", "retrieve")
builder.add_edge("answer", END)
builder.add_edge("review", END)

graph = builder.compile()

for question in [
    "What is a database index?",
    "Our billing database?",
    "Our billing migration approver?",
]:
    print(f"\nQuestion: {question}")
    result = graph.invoke(
        {
            "question": question,
            "query": "",
            "evidence": None,
            "retries": 0,
            "answer": "",
        }
    )
    print(result["answer"])