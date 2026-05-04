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
    def build(
        self,
        *,
        owner_id: int,
        wallet_type: str = "single-sig",
        has_descriptor: bool = False,
        has_recent_health_report: bool = False,
    ) -> dict[str, object]:
        wallet_key = f"wallet:{owner_id}"
        is_multisig = "multi" in wallet_type.lower()
        signer_count = 3 if is_multisig else 1
        nodes = [
            DependencyNode(node_id=wallet_key, node_type="wallet", label="Primary wallet", criticality="high"),
            DependencyNode(
                node_id=f"coordinator:{owner_id}",
                node_type="coordinator",
                label="Wallet coordinator",
                criticality="medium",
            ),
            DependencyNode(
                node_id=f"policy:{owner_id}",
                node_type="policy",
                label="Policy assumptions",
                criticality="high",
            ),
            DependencyNode(
                node_id=f"recovery-path:{owner_id}",
                node_type="recovery_path",
                label="Recovery execution path",
                criticality="high",
            ),
            DependencyNode(
                node_id=f"backup:{owner_id}",
                node_type="backup",
                label="Backup artifact",
                criticality="high" if not has_recent_health_report else "medium",
            ),
        ]
        for signer_idx in range(1, signer_count + 1):
            nodes.append(
                DependencyNode(
                    node_id=f"device:{owner_id}:{signer_idx}",
                    node_type="device",
                    label=f"Signer device {signer_idx}",
                    criticality="high",
                )
            )

        edges: list[DependencyEdge] = []
        for signer_idx in range(1, signer_count + 1):
            edges.append(
                DependencyEdge(
                    source=wallet_key,
                    target=f"device:{owner_id}:{signer_idx}",
                    dependency_type="signing",
                    single_point_of_failure=False,
                )
            )
        edges.extend(
            [
                DependencyEdge(
                    source=wallet_key,
                    target=f"backup:{owner_id}",
                    dependency_type="recovery",
                    single_point_of_failure=False,
                ),
                DependencyEdge(
                    source=wallet_key,
                    target=f"coordinator:{owner_id}",
                    dependency_type="orchestration",
                    single_point_of_failure=False,
                ),
                DependencyEdge(
                    source=wallet_key,
                    target=f"policy:{owner_id}",
                    dependency_type="policy_assumption",
                    single_point_of_failure=False,
                ),
                DependencyEdge(
                    source=f"recovery-path:{owner_id}",
                    target=f"backup:{owner_id}",
                    dependency_type="artifact_dependency",
                    single_point_of_failure=not has_recent_health_report,
                ),
            ]
        )
        if has_descriptor:
            nodes.append(
                DependencyNode(
                    node_id=f"descriptor:{owner_id}",
                    node_type="descriptor",
                    label="Descriptor reference",
                    criticality="high",
                )
            )
            edges.append(
                DependencyEdge(
                    source=wallet_key,
                    target=f"descriptor:{owner_id}",
                    dependency_type="descriptor_dependency",
                    single_point_of_failure=False,
                )
            )

        # Structural SPOF detection: a target is SPOF if only one upstream dependency points to it.
        inbound_count: dict[str, int] = {}
        for edge in edges:
            inbound_count[edge.target] = inbound_count.get(edge.target, 0) + 1
        for edge in edges:
            if edge.dependency_type == "signing":
                edge.single_point_of_failure = signer_count <= 1
            elif edge.dependency_type in {"recovery", "artifact_dependency"}:
                edge.single_point_of_failure = inbound_count.get(edge.target, 0) <= 1

        findings: list[dict[str, str]] = []
        if signer_count == 1:
            findings.append(
                {
                    "title": "Signer concentration",
                    "severity": "warning",
                    "detail": "Single signer dependency detected in topology graph.",
                }
            )
        if not has_descriptor:
            findings.append(
                {
                    "title": "Descriptor linkage missing",
                    "severity": "warning",
                    "detail": "Recovery path lacks descriptor dependency evidence.",
                }
            )
        if not has_recent_health_report:
            findings.append(
                {
                    "title": "Recovery freshness uncertainty",
                    "severity": "warning",
                    "detail": "Recent wallet health evidence is missing; recovery confidence reduced.",
                }
            )
        return {
            "nodes": [node.model_dump() for node in nodes],
            "edges": [edge.model_dump() for edge in edges],
            "single_points_of_failure": [edge.model_dump() for edge in edges if edge.single_point_of_failure],
            "findings": findings,
            "freshness": {"source": "citadel_graph", "owner_id": owner_id},
            "confidence": 0.84 if has_recent_health_report else 0.68,
            "explainability": {
                "rule": "SPOF derived from dependency topology and inbound redundancy count",
                "wallet_type": wallet_type,
                "signer_count": signer_count,
                "has_descriptor": has_descriptor,
                "has_recent_health_report": has_recent_health_report,
            },
        }
