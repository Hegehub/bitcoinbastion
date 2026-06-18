from __future__ import annotations


def test_app_module_imports_successfully() -> None:
    import bastion_ui.app as app_module

    assert app_module.app is not None
    assert callable(app_module.index)
