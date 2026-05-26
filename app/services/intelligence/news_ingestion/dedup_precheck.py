def is_duplicate_candidate(*, existing_canonical: bool, existing_content: bool, existing_title: bool) -> tuple[bool, str]:
    if existing_canonical:
        return True, "canonical_url_hash"
    if existing_content:
        return True, "content_hash"
    if existing_title:
        return True, "normalized_title_hash"
    return False, ""
