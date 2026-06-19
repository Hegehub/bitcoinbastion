from __future__ import annotations

import reflex as rx

from bastion_ui.components.data.status_table import status_table
from bastion_ui.components.ui.card import card

RUNTIME_PROFILE_ROWS = [
    {
        "Profile": "Docker Compose",
        "Status": "baseline",
        "Use": "Local and small operator deployments.",
    },
    {
        "Profile": "Kubernetes",
        "Status": "planned",
        "Use": "Cluster deployments with operator controls.",
    },
    {"Profile": "k3s", "Status": "planned", "Use": "Lightweight sovereign deployments."},
    {"Profile": "kind", "Status": "experimental", "Use": "Local Kubernetes testing."},
    {"Profile": "minikube", "Status": "experimental", "Use": "Developer cluster testing."},
    {"Profile": "single-node", "Status": "baseline", "Use": "Self-hosted local-first operation."},
    {"Profile": "bare-metal/systemd", "Status": "planned", "Use": "Operator-managed hosts."},
]


def runtime_profile_preview() -> rx.Component:
    return card(status_table(RUNTIME_PROFILE_ROWS), title="Runtime profile matrix preview")
