from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class SignalStatus(StrEnum):
    NEW = "new"
    SUPPRESSED = "suppressed"
    PUBLISHED = "published"
