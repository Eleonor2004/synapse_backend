from fastapi import APIRouter, Depends, HTTPException, Query
from neo4j import Session, time as neo4j_time
from typing import List, Dict, Any

from app.db.graph_db import get_db_session
from app.models.graph import Graph, Node, Edge

router = APIRouter()

# --- Helper Functions (Unchanged) ---
def convert_properties(props: Dict[str, Any]) -> Dict[str, Any]:
    converted = {}
    for key, value in props.items():
        if isinstance(value, neo4j_time.DateTime):
            converted[key] = value.to_native().isoformat()
        else:
            converted[key] = value
    return converted

def format_graph_response(records: List) -> Graph:
    nodes = []
    edges = []
    node_ids = set()
    for record in records:
        path = record.get("p")
        if path is None:
            continue
        for node in path.nodes:
            if node.element_id not in node_ids:
                nodes.append(Node(
                    id=node.element_id,
                    label=list(node.labels)[0],
                    properties=convert_properties(dict(node))
                ))
                node_ids.add(node.element_id)
        for edge in path.relationships:
            edges.append(Edge(
                id=edge.element_id,
                source=edge.start_node.element_id,
                target=edge.end_node.element_id,
                label=edge.type,
                properties=convert_properties(dict(edge))
            ))
    return Graph(nodes=nodes, edges=edges)

# --- API Endpoints ---

@router.get("/full", response_model=Graph)
def get_full_graph(session: Session = Depends(get_db_session)):
    """Retrieves the entire graph from the database."""
    query = "MATCH p = ()-[r]->() RETURN p"
    result = session.run(query)
    records = list(result)
    if not records:
        return Graph(nodes=[], edges=[])
    return format_graph_response(records)

# --- NEW ENDPOINT 1: Search for a Subscriber ---
@router.get("/search", response_model=Graph)
def search_subscriber(
    phone_number: str = Query(..., description="The phone number of the subscriber to search for."),
    session: Session = Depends(get_db_session)
):
    """
    Finds a subscriber by their phone number and returns their immediate network (1-hop neighborhood).
    """
    # This query finds the subscriber and any node connected to them by one relationship.
    query = """
    MATCH p = (s:Subscriber {phoneNumber: $phone_number})-[*0..1]-(neighbor)
    RETURN p
    """
    result = session.run(query, phone_number=phone_number)
    records = list(result)
    if not records:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    return format_graph_response(records)

# --- NEW ENDPOINT 2: Find Shortest Path ---
@router.get("/shortest-path", response_model=Graph)
def get_shortest_path(
    start_phone: str = Query(..., description="Phone number of the starting subscriber."),
    end_phone: str = Query(..., description="Phone number of the ending subscriber."),
    session: Session = Depends(get_db_session)
):
    """
    Calculates the shortest path between two subscribers in the communication network.
    """
    # This query uses a built-in Neo4j algorithm to find the shortest path.
    query = """
    MATCH (a:Subscriber {phoneNumber: $start_phone}), (b:Subscriber {phoneNumber: $end_phone})
    MATCH p = allShortestPaths((a)-[*]-(b))
    RETURN p
    """
    result = session.run(query, start_phone=start_phone, end_phone=end_phone)
    records = list(result)
    if not records:
        raise HTTPException(status_code=404, detail="No path found between the specified subscribers")
    return format_graph_response(records)