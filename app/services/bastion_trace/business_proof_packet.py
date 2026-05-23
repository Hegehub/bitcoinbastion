from app.schemas.bastion_trace import BusinessProofPacket


def build_business_proof_packet(payload: dict[str, object]) -> BusinessProofPacket:
    return BusinessProofPacket.model_validate(payload)
