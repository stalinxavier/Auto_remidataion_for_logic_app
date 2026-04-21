"""
graph.py
--------
Builds and returns the compiled LangGraph pipeline.

Pipeline
--------
  observer → classifier → rca → fixer

Each node reads from and writes back to the shared state dict.
"""

from langgraph.graph import StateGraph

from _nodes.observer_node import observer_node
from _nodes.classifier_node import classifier_node
from _nodes.root_cause_analysis import rca_node
from _nodes.fixer_node import fixer_node


def build_graph():
    """
    Construct the LangGraph StateGraph for the auto-remediation pipeline.

    Returns a compiled graph ready to be invoked with graph.invoke({}).
    """
    builder = StateGraph(dict)

    # Register nodes
    builder.add_node("observer", observer_node)
    builder.add_node("classifier", classifier_node)
    builder.add_node("rca", rca_node)
    builder.add_node("fixer", fixer_node)

    # Entry point
    builder.set_entry_point("observer")

    # Linear pipeline edges
    builder.add_edge("observer", "classifier")
    builder.add_edge("classifier", "rca")
    builder.add_edge("rca", "fixer")

    # Mark fixer as terminal
    builder.set_finish_point("fixer")

    return builder.compile()
