from __future__ import annotations

from bastion_ui.domain.access.models import ChildKeyCreatedViewModel
from bastion_ui.transport.generated_schemas import ChildApiKeyCreateResponse


def adapt_child_key_created(response: ChildApiKeyCreateResponse) -> ChildKeyCreatedViewModel:
    """Project metadata while deliberately omitting the one-time raw child secret."""
    return ChildKeyCreatedViewModel(
        key_id=response.key_id,
        scopes=tuple(response.scopes),
        expires_at=response.expires_at,
        warning=response.warning,
    )
