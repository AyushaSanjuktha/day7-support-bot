import pathlib

import app as app_module


def test_no_api_key_written_in_code():
    source = pathlib.Path(app_module.__file__).read_text()
    assert "sk-demo" not in source
    assert "FAKE-KEY" not in source


def test_api_key_is_read_from_environment(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key-from-env")
    import importlib
    reloaded = importlib.reload(app_module)
    assert reloaded.API_KEY == "test-key-from-env"
