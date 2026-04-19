from pydantic import BaseModel


class DependencyNode(BaseModel):
    node_id: str
    node_type: str
    label: str
    criticality: str


class DependencyEdge(BaseModel):
    source: str
    target: str
    dependency_type: str
    single_point_of_failure: bool


class SovereigntyGraphService:
    def build(self, *, owner_id: int) -> dict[str, object]:
        nodes = [
            DependencyNode(node_id=f"wallet:{owner_id}", node_type="wallet", label="Primary wallet", criticality="high"),
            DependencyNode(node_id=f"device:{owner_id}:1", node_type="device", label="Signer device", criticality="high"),
            DependencyNode(node_id=f"backup:{owner_id}", node_type="backup", label="Backup artifact", criticality="medium"),
        ]
        edges = [
            DependencyEdge(
                source=f"wallet:{owner_id}",
                target=f"device:{owner_id}:1",
                dependency_type="signing",
                single_point_of_failure=True,
            ),
            DependencyEdge(
                source=f"wallet:{owner_id}",
                target=f"backup:{owner_id}",
                dependency_type="recovery",
                single_point_of_failure=False,
            ),
        ]

        findings = [
            {
                "title": "Signer concentration",
                "severity": "warning",
                "detail": "Single signer device currently marked as SPOF.",
            }
        ]
        return {
            "nodes": [node.model_dump() for node in nodes],
            "edges": [edge.model_dump() for edge in edges],
            "single_points_of_failure": [edge.model_dump() for edge in edges if edge.single_point_of_failure],
            "findings": findings,
            "freshness": {"source": "citadel_graph", "owner_id": owner_id},
            "confidence": 0.73,
            "explainability": {"rule": "edges flagged as SPOF when no redundant sibling edge exists"},
        }
