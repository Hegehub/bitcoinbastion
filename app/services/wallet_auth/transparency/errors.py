"""Typed, non-sensitive transparency failures."""


class TransparencyError(ValueError):
    pass


class UnsupportedCheckpointTypeError(TransparencyError):
    pass


class InvalidCheckpointSourceError(TransparencyError):
    pass


class CheckpointCanonicalizationError(TransparencyError):
    pass


class CheckpointSequenceConflictError(TransparencyError):
    pass


class CheckpointSignatureError(TransparencyError):
    pass


class CheckpointVerificationError(TransparencyError):
    pass


class CheckpointChainGapError(TransparencyError):
    pass


class MerkleProofError(TransparencyError):
    pass


class CheckpointPrivacyViolationError(TransparencyError):
    pass


class CheckpointPublicationError(TransparencyError):
    pass


class UnsupportedTransparencySignatureSuiteError(TransparencyError):
    pass
