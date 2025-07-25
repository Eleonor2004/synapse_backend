from pydantic import BaseModel
from typing import List, Dict, Any

# Pydantic model for a graph node
class Node(BaseModel):
    id: str             # Unique identifier for the node (from Neo4j's element_id)
    label: str          # The node's label (e.g., "Subscriber", "Device")
    properties: Dict[str, Any] # A dictionary of the node's properties

# Pydantic model for a graph edge (relationship)
class Edge(BaseModel):
    id: str             # Unique identifier for the edge
    source: str         # The ID of the source node
    target: str         # The ID of the target node
    label: str          # The type of the relationship (e.g., "INITIATED")
    properties: Dict[str, Any] # A dictionary of the edge's properties

# Pydantic model for the entire graph structure
class Graph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]