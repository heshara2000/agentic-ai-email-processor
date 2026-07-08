# Since we're using LangGraph, every node shares a state.


from typing import TypedDict

class GraphState(TypedDict):
    file_path: str
    extracted_data: dict
    validation_result: dict
    decision: str