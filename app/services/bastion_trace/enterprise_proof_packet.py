from app.schemas.bastion_trace import EnterpriseProofPacket


def build_enterprise_proof_packet(payload: dict[str, object]) -> EnterpriseProofPacket:
    return EnterpriseProofPacket.model_validate(payload)
