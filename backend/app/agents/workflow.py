from langgraph.graph import END, START, StateGraph

from backend.app.agents.state import DocumentState
from backend.app.services.analysis import analyze_text


def analyze_document(state: DocumentState) -> DocumentState:
    result = analyze_text(state["text"])

    return {
        **state,
        "summary": result["summary"],
        "word_count": result["word_count"],
        "character_count": result["character_count"],
        "sentence_count": result["sentence_count"],
        "status": "analyzed",
    }


def build_document_workflow():
    workflow = StateGraph(DocumentState)

    workflow.add_node("analyze", analyze_document)

    workflow.add_edge(START, "analyze")
    workflow.add_edge("analyze", END)

    return workflow.compile()


document_workflow = build_document_workflow()