# OpenAPI Stability

API version is `/api/v1`.
Contracts are baseline locked for frontend-critical paths, not final external SLA.
Backward compatibility policy:
- add fields backward-compatibly,
- avoid enum renames,
- avoid breaking DTO shape without migration notes.
TypeScript type generation is currently manual baseline and automated generation is pending.
