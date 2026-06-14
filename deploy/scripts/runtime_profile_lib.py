from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIR = ROOT / "deploy" / "runtime-profiles"
KUBE_OVERLAYS = ROOT / "deploy" / "kubernetes" / "overlays"
SUPPORTED_PROFILES = {
    "compose",
    "k8s",
    "k3s",
    "kind",
    "minikube",
    "single-node",
    "bare-metal-systemd",
}
SUPPORTED_ENVS = {"local", "dev", "staging", "production"}
EXIT_INVALID_USAGE = 1
EXIT_MISSING_FILE = 2
EXIT_MISSING_TOOL = 3
EXIT_COMMAND_FAILED = 4


@dataclass(frozen=True)
class CommandPlan:
    profile: str
    env: str
    commands: list[list[str]]
    display_commands: list[str]
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    overlay_path: str | None = None
    mode: str = "dry-run"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def run_checked(command: list[str], *, timeout: int = 5) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def detect_docker_compose() -> bool:
    docker = shutil.which("docker")
    if docker:
        try:
            result = run_checked([docker, "compose", "version"], timeout=4)
            if result.returncode == 0:
                return True
        except (OSError, subprocess.TimeoutExpired):
            pass
    legacy = shutil.which("docker-compose")
    if legacy:
        try:
            result = run_checked([legacy, "version"], timeout=4)
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False
    return False


def get_kubectl_context() -> str | None:
    kubectl = shutil.which("kubectl")
    if not kubectl:
        return None
    try:
        result = run_checked([kubectl, "config", "current-context"], timeout=4)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    context = result.stdout.strip()
    return context or None


def detect_ram_gb() -> float | None:
    meminfo = Path("/proc/meminfo")
    try:
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                parts = line.split()
                if len(parts) >= 2:
                    return round(int(parts[1]) / 1024 / 1024, 2)
    except (OSError, ValueError):
        return None
    return None


def is_ci() -> bool:
    return os.environ.get("CI", "").lower() in {"1", "true", "yes", "on"}


def is_systemd_available() -> bool:
    if not command_exists("systemctl"):
        return False
    if platform.system().lower() != "linux":
        return False
    return Path("/run/systemd/system").exists() or Path("/bin/systemctl").exists() or Path("/usr/bin/systemctl").exists()


def detect_environment() -> dict[str, Any]:
    tools = {
        "docker": command_exists("docker"),
        "docker_compose": detect_docker_compose(),
        "kubectl": command_exists("kubectl"),
        "k3s": command_exists("k3s"),
        "kind": command_exists("kind"),
        "minikube": command_exists("minikube"),
        "systemd": is_systemd_available(),
    }
    kubectl_context = get_kubectl_context() if tools["kubectl"] else None
    system = {
        "cpu_count": os.cpu_count(),
        "ram_gb": detect_ram_gb(),
        "ci": is_ci(),
        "platform": platform.system().lower(),
        "kubectl_context": kubectl_context,
    }
    recommendation = recommend_profile(tools, system)
    return {"tools": tools, "system": system, "recommendation": recommendation}


def resource_warnings(system: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    ram_gb = system.get("ram_gb")
    if ram_gb is None:
        warnings.append("RAM size unknown; verify resources before deployment.")
    elif ram_gb < 2:
        warnings.append("Very constrained environment: less than 2 GB RAM detected.")
    elif ram_gb < 4:
        warnings.append("Constrained environment: prefer compose or bare-metal-systemd unless you intentionally tuned services.")
    elif ram_gb < 8:
        warnings.append("Moderate resources: compose, k3s single-node, Kind, or Minikube may be possible with limits.")
    return warnings


def recommend_profile(tools: dict[str, bool], system: dict[str, Any]) -> dict[str, Any]:
    warnings = resource_warnings(system)
    if system.get("ci"):
        if tools.get("kind"):
            return {"profile": "kind", "reason": "CI environment detected and kind is available for local Kubernetes validation.", "warnings": warnings}
        if tools.get("docker_compose"):
            return {"profile": "compose", "reason": "CI environment detected and docker compose is available.", "warnings": warnings}
        return {"profile": "no-safe-profile", "reason": "CI environment detected but no supported local runtime tools were found.", "warnings": warnings}
    if tools.get("k3s"):
        return {"profile": "k3s", "reason": "k3s detected; suitable for sovereign VPS/home server deployment when hardened.", "warnings": warnings}
    if tools.get("kubectl") and system.get("kubectl_context"):
        return {"profile": "k8s", "reason": "kubectl context detected; use the canonical Kubernetes overlays intentionally.", "warnings": warnings}
    if tools.get("kind"):
        return {"profile": "kind", "reason": "kind detected; suitable for local manifest validation only.", "warnings": warnings}
    if tools.get("minikube"):
        return {"profile": "minikube", "reason": "minikube detected; suitable for local operator testing only.", "warnings": warnings}
    if tools.get("docker_compose"):
        return {"profile": "compose", "reason": "docker compose detected and no Kubernetes runtime detected.", "warnings": warnings}
    if tools.get("systemd"):
        return {"profile": "bare-metal-systemd", "reason": "systemd detected and no container/Kubernetes runtime detected; advanced manual fallback.", "warnings": warnings}
    return {"profile": "manual-review", "reason": "No supported runtime tool detected; operator review required.", "warnings": warnings}


def require_runtime_metadata() -> list[str]:
    required = [
        PROFILE_DIR / "profiles.yaml",
        PROFILE_DIR / "compose.yaml",
        PROFILE_DIR / "k8s.yaml",
        PROFILE_DIR / "k3s.yaml",
        PROFILE_DIR / "kind.yaml",
        PROFILE_DIR / "minikube.yaml",
        PROFILE_DIR / "single-node.yaml",
        PROFILE_DIR / "bare-metal-systemd.yaml",
    ]
    return [rel(path) for path in required if not path.exists()]


def overlay_for(profile: str, env: str) -> Path | None:
    if profile == "k8s":
        mapped = "dev" if env in {"local", "dev"} else env
        return KUBE_OVERLAYS / mapped
    if profile in {"k3s", "kind", "minikube", "single-node"}:
        return KUBE_OVERLAYS / profile
    return None


def command_to_string(command: list[str]) -> str:
    return " ".join(command)


def build_plan(profile: str, env: str, *, mode: str = "dry-run") -> CommandPlan:
    if profile not in SUPPORTED_PROFILES:
        raise ValueError(f"Unsupported profile '{profile}'. Supported profiles: {', '.join(sorted(SUPPORTED_PROFILES))}")
    if env not in SUPPORTED_ENVS:
        raise ValueError(f"Unsupported env '{env}'. Supported envs: {', '.join(sorted(SUPPORTED_ENVS))}")
    missing = require_runtime_metadata()
    if missing:
        raise FileNotFoundError("Missing runtime profile metadata: " + ", ".join(missing))

    notes: list[str] = [
        "Dry-run is the default; apply requires --apply --yes.",
        "No secrets are generated and no custody/signing behavior is introduced.",
    ]
    warnings: list[str] = []
    commands: list[list[str]]
    display_commands: list[str]
    overlay = overlay_for(profile, env)

    if profile == "compose":
        if env == "production":
            commands = [["docker", "compose", "--env-file", ".env", "up", "-d", "--build"]]
            display_commands = ["docker compose config", "ENVIRONMENT=prod docker compose --env-file .env up -d --build"]
        else:
            commands = [["docker", "compose", "config"], ["docker", "compose", "--env-file", ".env", "up", "-d", "--build"]]
            display_commands = [command_to_string(cmd) for cmd in commands]
        notes.append("Compose is convenient for local development and small self-hosted tests; it is not HA.")
        return CommandPlan(profile, env, commands, display_commands, notes, warnings, None, mode)

    if profile == "bare-metal-systemd":
        commands = [
            ["python", "-m", "alembic", "upgrade", "head"],
            ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            ["python", "-m", "celery", "-A", "app.tasks.celery_app.celery_app", "worker", "--loglevel=info"],
            ["python", "-m", "celery", "-A", "app.tasks.celery_app.celery_app", "beat", "--loglevel=info"],
        ]
        display_commands = [command_to_string(cmd) for cmd in commands]
        notes.extend([
            "Expected service names: bitcoin-bastion-api.service, bitcoin-bastion-worker.service, bitcoin-bastion-beat.service.",
            "Requires PostgreSQL, Redis, env file, operator-managed logs, backups, and health checks.",
            "Advanced fallback, not the easiest production path.",
        ])
        return CommandPlan(profile, env, commands, display_commands, notes, warnings, None, mode)

    assert overlay is not None
    overlay_rel = rel(overlay)
    commands = [["kubectl", "kustomize", overlay_rel], ["kubectl", "apply", "-k", overlay_rel]]
    display_commands = [command_to_string(cmd) for cmd in commands]
    if profile == "k3s":
        notes.extend([
            "K3s often includes Traefik by default.",
            "Verify local-path storage class if PVCs are used.",
            "Intended for sovereign VPS/home server/small production with operator evidence.",
        ])
    elif profile == "kind":
        notes.extend(["Local manifest validation only.", "No production claims.", "Use port-forward or NodePort as documented."])
    elif profile == "minikube":
        notes.extend(["Local operator testing only.", "Enable ingress addon if ingress is used."])
    elif profile == "single-node":
        notes.extend(["Conservative single-node profile.", "No HA claims.", "Heavy jobs may be suspended/manual.", "Production use requires explicit operator evidence."])
    elif profile == "k8s":
        notes.append("Production readiness depends on environment-specific evidence artifacts.")
    return CommandPlan(profile, env, commands, display_commands, notes, warnings, overlay_rel, mode)


def plan_to_dict(plan: CommandPlan) -> dict[str, Any]:
    return {
        "profile": plan.profile,
        "env": plan.env,
        "mode": plan.mode,
        "overlay_path": plan.overlay_path,
        "commands": plan.display_commands,
        "notes": plan.notes,
        "warnings": plan.warnings,
    }


def print_detection(result: dict[str, Any], *, verbose: bool = False) -> None:
    print("Bitcoin Bastion Runtime Detection")
    print()
    print("Detected:")
    for key, value in result["tools"].items():
        print(f"- {key}: {'available' if value else 'unavailable'}")
    system = result["system"]
    print(f"- cpu_count: {system.get('cpu_count') if system.get('cpu_count') is not None else 'unknown'}")
    print(f"- ram_gb: {system.get('ram_gb') if system.get('ram_gb') is not None else 'unknown'}")
    print(f"- ci: {str(system.get('ci')).lower()}")
    if verbose:
        print(f"- platform: {system.get('platform')}")
        print(f"- kubectl_context: {system.get('kubectl_context') or 'unavailable'}")
    rec = result["recommendation"]
    print()
    print("Recommended profile:")
    print(f"- profile: {rec['profile']}")
    print(f"- reason: {rec['reason']}")
    print()
    print("Warnings:")
    if rec["warnings"]:
        for warning in rec["warnings"]:
            print(f"- {warning}")
    else:
        print("- none")


def print_plan(plan: CommandPlan) -> None:
    print("Bitcoin Bastion Runtime Profile Plan")
    print(f"Profile: {plan.profile}")
    print(f"Environment: {plan.env}")
    print(f"Mode: {plan.mode}")
    if plan.overlay_path:
        print(f"Overlay: {plan.overlay_path}")
    print()
    print("Command plan:")
    for command in plan.display_commands:
        print(f"- {command}")
    print()
    print("Notes:")
    for note in plan.notes:
        print(f"- {note}")
    if plan.warnings:
        print()
        print("Warnings:")
        for warning in plan.warnings:
            print(f"- {warning}")


def validate_plan(plan: CommandPlan) -> int:
    if plan.profile == "compose":
        if not detect_docker_compose():
            print("Required tool missing for compose validation: docker compose or docker-compose", file=sys.stderr)
            return EXIT_MISSING_TOOL
        command = ["docker", "compose", "config"] if command_exists("docker") else ["docker-compose", "config"]
        return execute_command(command)
    if plan.profile == "bare-metal-systemd":
        docs = ROOT / "docs" / "BARE_METAL_SYSTEMD.md"
        if not docs.exists():
            print("Required systemd guide missing: docs/BARE_METAL_SYSTEMD.md", file=sys.stderr)
            return EXIT_MISSING_FILE
        print(f"Validated documentation exists: {rel(docs)}")
        return 0
    if not plan.overlay_path:
        return 0
    overlay = ROOT / plan.overlay_path
    if not overlay.exists():
        print(f"Required overlay missing: {plan.overlay_path}", file=sys.stderr)
        return EXIT_MISSING_FILE
    if not command_exists("kubectl"):
        print("Required tool missing for Kubernetes validation: kubectl", file=sys.stderr)
        return EXIT_MISSING_TOOL
    return execute_command(["kubectl", "kustomize", plan.overlay_path])


def apply_plan(plan: CommandPlan) -> int:
    if plan.profile == "compose":
        if not detect_docker_compose():
            print("Required tool missing for compose apply: docker compose or docker-compose", file=sys.stderr)
            return EXIT_MISSING_TOOL
        for command in plan.commands:
            if command[:3] == ["docker", "compose", "config"]:
                continue
            code = execute_command(command, env={"ENVIRONMENT": "prod"} if plan.env == "production" else None)
            if code != 0:
                return code
        return 0
    if plan.profile == "bare-metal-systemd":
        print("Refusing to execute bare-metal/systemd process commands automatically. Use the printed plan intentionally.", file=sys.stderr)
        return EXIT_COMMAND_FAILED
    if not plan.overlay_path:
        return 0
    overlay = ROOT / plan.overlay_path
    if not overlay.exists():
        print(f"Required overlay missing: {plan.overlay_path}", file=sys.stderr)
        return EXIT_MISSING_FILE
    if not command_exists("kubectl"):
        print("Required tool missing for Kubernetes apply: kubectl", file=sys.stderr)
        return EXIT_MISSING_TOOL
    return execute_command(["kubectl", "apply", "-k", plan.overlay_path])


def execute_command(command: list[str], env: dict[str, str] | None = None) -> int:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    result = subprocess.run(command, cwd=ROOT, env=merged_env, check=False)
    if result.returncode != 0:
        return EXIT_COMMAND_FAILED
    return 0


def json_dumps(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True)
