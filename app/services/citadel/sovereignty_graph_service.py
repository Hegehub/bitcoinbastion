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
    @staticmethod
    def _signer_count(wallet_type: str) -> int:
        lowered = wallet_type.lower()
        if "multisig" in lowered or "multi" in lowered:
            return 3
        return 1

    def build(
        self,
        *,
        owner_id: int,
        wallet_type: str = "single-sig",
        has_descriptor: bool = False,
        has_recent_health_report: bool = False,
    ) -> dict[str, object]:
        wallet_key = f"wallet:{owner_id}"
        signer_count = self._signer_count(wallet_type)

        nodes = [
            DependencyNode(node_id=wallet_key, node_type="wallet", label="Primary wallet", criticality="high"),
            DependencyNode(node_id=f"policy:{owner_id}", node_type="policy", label="Policy controls", criticality="high"),
            DependencyNode(node_id=f"coordinator:{owner_id}", node_type="coordinator", label="Signing coordinator", criticality="medium"),
            DependencyNode(node_id=f"provider:{owner_id}", node_type="provider", label="Blockchain provider", criticality="medium"),
            DependencyNode(node_id=f"backup:{owner_id}", node_type="backup", label="Recovery backup", criticality="high"),
            DependencyNode(node_id=f"inheritance:{owner_id}", node_type="inheritance", label="Inheritance handoff", criticality="high"),
        ]

        if has_descriptor:
            nodes.append(
                DependencyNode(
                    node_id=f"descriptor:{owner_id}",
                    node_type="descriptor",
                    label="Descriptor reference",
                    criticality="high",
                )
            )

        for signer_idx in range(1, signer_count + 1):
            nodes.append(
                DependencyNode(
                    node_id=f"signer:{owner_id}:{signer_idx}",
                    node_type="signer",
                    label=f"Signer {signer_idx}",
                    criticality="high",
                )
            )
            nodes.append(
                DependencyNode(
                    node_id=f"device:{owner_id}:{signer_idx}",
                    node_type="device",
                    label=f"Signer device {signer_idx}",
                    criticality="high",
                )
            )

        edges: list[DependencyEdge] = [
            DependencyEdge(source=wallet_key, target=f"policy:{owner_id}", dependency_type="policy_assumption", single_point_of_failure=False),
            DependencyEdge(source=wallet_key, target=f"coordinator:{owner_id}", dependency_type="orchestration", single_point_of_failure=False),
            DependencyEdge(source=wallet_key, target=f"provider:{owner_id}", dependency_type="provider_dependency", single_point_of_failure=False),
            DependencyEdge(source=wallet_key, target=f"backup:{owner_id}", dependency_type="recovery", single_point_of_failure=False),
            DependencyEdge(source=f"inheritance:{owner_id}", target=f"backup:{owner_id}", dependency_type="artifact_dependency", single_point_of_failure=False),
            DependencyEdge(source=f"inheritance:{owner_id}", target=f"policy:{owner_id}", dependency_type="inheritance_policy_dependency", single_point_of_failure=False),
        ]

        if has_descriptor:
            edges.append(
                DependencyEdge(source=wallet_key, target=f"descriptor:{owner_id}", dependency_type="descriptor_dependency", single_point_of_failure=False)
            )
            edges.append(
                DependencyEdge(source=f"inheritance:{owner_id}", target=f"descriptor:{owner_id}", dependency_type="inheritance_descriptor_dependency", single_point_of_failure=False)
            )

        for signer_idx in range(1, signer_count + 1):
            signer_key = f"signer:{owner_id}:{signer_idx}"
            device_key = f"device:{owner_id}:{signer_idx}"
            edges.append(
                DependencyEdge(source=wallet_key, target=signer_key, dependency_type="signing", single_point_of_failure=False)
            )
            edges.append(
                DependencyEdge(source=signer_key, target=device_key, dependency_type="device_dependency", single_point_of_failure=False)
            )

        inbound_count: dict[str, int] = {}
        for edge in edges:
            inbound_count[edge.target] = inbound_count.get(edge.target, 0) + 1

        for edge in edges:
            if edge.dependency_type == "signing":
                edge.single_point_of_failure = signer_count <= 1
            elif edge.dependency_type == "device_dependency":
                edge.single_point_of_failure = True
            else:
                edge.single_point_of_failure = inbound_count.get(edge.target, 0) <= 1

        spof_edges = [edge.model_dump() for edge in edges if edge.single_point_of_failure]
        spof_count = len(spof_edges)
        penalized_spof_count = len(
            [edge for edge in spof_edges if edge["dependency_type"] != "device_dependency"]
        )

        findings: list[dict[str, str]] = []
        if signer_count == 1:
            findings.append(
                {
                    "title": "Signer concentration",
                    "severity": "warning",
                    "detail": "Single signer path detected; signing SPOF risk is elevated.",
                }
            )
        if not has_descriptor:
            findings.append(
                {
                    "title": "Descriptor dependency missing",
                    "severity": "warning",
                    "detail": "Descriptor node absent; inheritance and recovery path confidence reduced.",
                }
            )
        if not has_recent_health_report:
            findings.append(
                {
                    "title": "Recovery evidence stale",
                    "severity": "warning",
                    "detail": "Recent wallet health evidence missing; backup/provider assumptions are less reliable.",
                }
            )
        if any(edge["dependency_type"] == "provider_dependency" for edge in spof_edges):
            findings.append(
                {
                    "title": "Provider SPOF",
                    "severity": "warning",
                    "detail": "Single blockchain provider dependency detected.",
                }
            )

        confidence = round(
            max(
                0.45,
                min(
                    0.94,
                    0.64
                    + (0.08 if signer_count >= 3 else 0.0)
                    + (0.06 if has_descriptor else 0.0)
                    + (0.08 if has_recent_health_report else 0.0)
                    - min(0.22, penalized_spof_count * 0.02),
                ),
            ),
            3,
        )

        return {
            "nodes": [node.model_dump() for node in nodes],
            "edges": [edge.model_dump() for edge in edges],
            "single_points_of_failure": spof_edges,
            "findings": findings,
            "freshness": {"source": "citadel_graph", "owner_id": owner_id, "graph_version": "citadel_graph_v2"},
            "confidence": confidence,
            "synthetic_component": True,
            "synthetic_reason": "Deterministic baseline model with partial synthetic assumptions.",
            "production_replacement_path": "Replace with production-grade telemetry, attestations, and provider-linked evidence.",
            "confidence_penalty": 0.15,
            "operator_warning": "Synthetic/baseline Citadel output: validate with real operational evidence before critical action.",
            "evidence_refs": ["citadel:baseline_model"],
            "limitations": ["Output includes synthetic or baseline assumptions and is not full production attestation."],
            "source_quality": {"source_type": "synthetic", "is_fallback": True},
            "explainability": {
                "rule": "SPOF derived from structural inbound dependency analysis with deterministic topology rules",
                "wallet_type": wallet_type,
                "signer_count": signer_count,
                "has_descriptor": has_descriptor,
                "has_recent_health_report": has_recent_health_report,
                "node_counts": {
                    "total": len(nodes),
                    "signer": len([n for n in nodes if n.node_type == "signer"]),
                    "device": len([n for n in nodes if n.node_type == "device"]),
                },
                "edge_counts": {
                    "total": len(edges),
                    "spof": spof_count,
                    "provider_dependencies": len([e for e in edges if e.dependency_type == "provider_dependency"]),
                    "inheritance_dependencies": len([e for e in edges if e.dependency_type.startswith("inheritance_")]),
                },
                "confidence_components": {
                    "base": 0.64,
                    "signer_redundancy_bonus": 0.08 if signer_count >= 3 else 0.0,
                    "descriptor_bonus": 0.06 if has_descriptor else 0.0,
                    "freshness_bonus": 0.08 if has_recent_health_report else 0.0,
                    "spof_penalty": round(min(0.22, penalized_spof_count * 0.02), 3),
                },
            },
        }
