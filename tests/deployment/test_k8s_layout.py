from pathlib import Path


def test_k8s_overlays_exist() -> None:
    for env in ("dev", "staging", "production"):
        assert Path(f"k8s/overlays/{env}/kustomization.yaml").exists()


def test_production_overlay_disables_debug() -> None:
    content = Path("k8s/overlays/production/kustomization.yaml").read_text()
    assert 'path: /data/DEBUG' in content
    assert 'value: "false"' in content


def test_network_policies_exist() -> None:
    assert Path("k8s/security/networkpolicy-default-deny.yaml").exists()
    assert Path("k8s/security/networkpolicy-frontend-api.yaml").exists()
