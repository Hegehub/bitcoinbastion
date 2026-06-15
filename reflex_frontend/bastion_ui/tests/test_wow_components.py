from bastion_ui.components.layout.command_palette import COMMAND_ACTIONS
from bastion_ui.components.wow.bastion_command_center import bastion_command_center
from bastion_ui.components.wow.evidence_chain_viewer import evidence_chain_viewer
from bastion_ui.components.wow.human_confirmation_firewall import human_confirmation_firewall
from bastion_ui.components.wow.proof_packet_explorer import PROOF_STATES, proof_packet_explorer
from bastion_ui.components.wow.provider_trust_matrix import provider_trust_matrix
from bastion_ui.components.wow.trace_radar import trace_radar


def test_core_wow_components_render() -> None:
    assert bastion_command_center() is not None
    assert trace_radar({"risk_band": "unknown"}) is not None
    assert trace_radar() is not None
    assert evidence_chain_viewer([{"source": "preview", "limitation": "unknown"}]) is not None
    assert evidence_chain_viewer() is not None
    assert proof_packet_explorer() is not None
    assert provider_trust_matrix() is not None
    assert human_confirmation_firewall() is not None


def test_proof_packet_states_are_declared() -> None:
    for state in ("unsigned proof packet", "signed proof packet", "preview proof packet", "unavailable proof packet"):
        assert state in PROOF_STATES


def test_command_palette_includes_wow_routes() -> None:
    actions = dict(COMMAND_ACTIONS)
    assert actions["Open Command Center"] == "/console/command-center"
    assert actions["Open Trace Radar"] == "/console/trace"
    assert actions["Open Evidence Chain"] == "/console/evidence"
    assert actions["Open Time Machine Timeline"] == "/console/time-machine"
    assert actions["Open Sovereign Grid Map"] == "/console/sovereign-grid"
    assert actions["Open Policy Simulator"] == "/console/policy"
    assert actions["Open Audit Replay"] == "/console/audit"
    assert actions["Open API Contract Explorer"] == "/console/audit"
    assert "/products" not in actions.values()
    assert "/self-host" not in actions.values()
