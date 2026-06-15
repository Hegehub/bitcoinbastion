import reflex as rx

from bastion_ui.routes.check import check_page
from bastion_ui.routes.console import console_page
from bastion_ui.routes.console_command_center import console_command_center_page
from bastion_ui.routes.console_api_explorer import console_api_explorer_page
from bastion_ui.routes.console_audit import console_audit_page
from bastion_ui.routes.console_deployment import console_deployment_page
from bastion_ui.routes.console_market_intelligence import console_market_intelligence_page
from bastion_ui.routes.console_policy import console_policy_page
from bastion_ui.routes.console_sovereign_grid import console_sovereign_grid_page
from bastion_ui.routes.console_time_machine import console_time_machine_page
from bastion_ui.routes.console_evidence import console_evidence_page
from bastion_ui.routes.console_provider_health import console_provider_health_page
from bastion_ui.routes.console_trace import console_trace_page
from bastion_ui.routes.proof_packet import proof_packet_page
from bastion_ui.routes.trace import trace_page
from bastion_ui.routes.trace_report import trace_report_page
from bastion_ui.routes.developers import developers_page
from bastion_ui.routes.docs import docs_page
from bastion_ui.routes.evidence import evidence_page
from bastion_ui.routes.home import home_page
from bastion_ui.routes.manifesto import manifesto_page
from bastion_ui.routes.operations import operations_page
from bastion_ui.routes.platform import platform_page
from bastion_ui.routes.roadmap import roadmap_page
from bastion_ui.routes.security import security_page
from bastion_ui.routes.status import status_page

app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="orange",
        radius="large",
    )
)

app.add_page(home_page, route="/", title="Bitcoin Bastion")
app.add_page(platform_page, route="/platform", title="Platform")
app.add_page(developers_page, route="/developers", title="Developers")
app.add_page(operations_page, route="/operations", title="Operations")
app.add_page(manifesto_page, route="/manifesto", title="Manifesto")
app.add_page(evidence_page, route="/evidence", title="Evidence")
app.add_page(status_page, route="/status", title="Status")
app.add_page(roadmap_page, route="/roadmap", title="Roadmap")
app.add_page(security_page, route="/security", title="Security")
app.add_page(docs_page, route="/docs", title="Docs")

app.add_page(proof_packet_page, route="/trace/[report_id]/proof-packet", title="Proof Packet")
app.add_page(trace_report_page, route="/trace/[report_id]", title="Trace Report")
app.add_page(check_page, route="/check", title="Bitcoin Address Check")
app.add_page(trace_page, route="/trace", title="Bastion Trace")
app.add_page(console_page, route="/console", title="Bastion Console")
app.add_page(console_trace_page, route="/console/trace", title="Console Trace")
app.add_page(console_evidence_page, route="/console/evidence", title="Console Evidence")
app.add_page(console_provider_health_page, route="/console/provider-health", title="Provider Health")

app.add_page(console_market_intelligence_page, route="/console/market-intelligence", title="Market Intelligence")
app.add_page(console_time_machine_page, route="/console/time-machine", title="Time Machine")
app.add_page(console_sovereign_grid_page, route="/console/sovereign-grid", title="Sovereign Grid")
app.add_page(console_policy_page, route="/console/policy", title="Policy Engine")
app.add_page(console_audit_page, route="/console/audit", title="Audit Log")
app.add_page(console_deployment_page, route="/console/deployment", title="Deployment Status")
app.add_page(console_api_explorer_page, route="/console/api-explorer", title="API Explorer")

app.add_page(console_command_center_page, route="/console/command-center", title="Command Center")
