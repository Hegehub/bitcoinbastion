#!/usr/bin/env python3
"""Validate runtime-profile files, Make targets, and dry-run render commands."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "runtime_profile_validation.json"
PROFILES = ["compose", "k8s", "k3s", "kind", "minikube", "single-node", "bare-metal-systemd"]
OVERLAYS = ["dev", "staging", "production", "k3s", "kind", "minikube", "single-node"]
TARGETS = [
    "runtime-profiles", "runtime-detect", "runtime-render-compose", "runtime-render-k8s", "runtime-render-k3s",
    "runtime-render-kind", "runtime-render-minikube", "runtime-render-single-node", "deploy-compose", "deploy-k8s",
    "deploy-k3s", "deploy-kind", "deploy-minikube", "deploy-single-node", "systemd-notes",
]


def run(cmd: list[str]) -> dict[str, object]:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=60)
    display_cmd = list(cmd)
    if display_cmd and Path(display_cmd[0]).resolve() == Path(sys.executable).resolve():
        display_cmd[0] = "python"
    return {
        "command": " ".join(display_cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout[-2000:],
        "stderr": proc.stderr[-2000:],
    }


def main() -> int:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    files = {p: (ROOT / "deploy" / "runtime-profiles" / f"{p}.yaml").exists() for p in PROFILES if p != "bare-metal-systemd"}
    files["bare-metal-systemd"] = (ROOT / "deploy/runtime-profiles/bare-metal-systemd.yaml").exists()
    overlays = {o: (ROOT / "deploy/kubernetes/overlays" / o / "kustomization.yaml").exists() for o in OVERLAYS}
    targets = {t: f"{t}:" in makefile and ("deploy/scripts/" in makefile or "kubectl" in makefile) for t in TARGETS}
    render_profiles = ["compose", "k8s", "k3s", "kind", "minikube", "single-node"]
    render = {p: run([sys.executable, "deploy/scripts/render-runtime-profile.py", "--profile", p, "--dry-run"]) for p in render_profiles}
    kubectl = shutil.which("kubectl")
    kustomize = {}
    for overlay in ["k3s", "kind", "minikube", "single-node"]:
        if kubectl:
            kustomize[overlay] = run([kubectl, "kustomize", f"deploy/kubernetes/overlays/{overlay}"])
        else:
            kustomize[overlay] = {"status": "skipped", "reason": "kubectl unavailable"}
    blockers = []
    blockers += [f"missing profile {k}" for k, v in files.items() if not v]
    blockers += [f"missing overlay {k}" for k, v in overlays.items() if not v]
    blockers += [f"missing or non-scripted target {k}" for k, v in targets.items() if not v]
    blockers += [f"render failed {k}" for k, v in render.items() if v["returncode"] != 0]
    result = {"status": "implemented" if not blockers else "blocked", "files": files, "overlays": overlays, "targets": targets, "render": render, "kustomize": kustomize, "blockers": blockers}
    ARTIFACT.parent.mkdir(exist_ok=True)
    ARTIFACT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if blockers else 0

if __name__ == "__main__":
    raise SystemExit(main())
