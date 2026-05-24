from fastapi import FastAPI


def apply_openapi_defaults(app: FastAPI) -> None:
    app.openapi_tags = [
        {'name': 'public', 'description': 'Public presentation-safe endpoints'},
        {'name': 'trace', 'description': 'Bastion Trace advisory endpoints'},
    ]
