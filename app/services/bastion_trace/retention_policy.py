
def retention_allows_delete(auto_delete_enabled: bool, legal_hold_active: bool) -> bool:
    return auto_delete_enabled and not legal_hold_active
