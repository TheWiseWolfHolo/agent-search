import json

from agent_search.config import Config


def reset_config_resolution() -> Config:
    cfg = Config()
    cfg._config_file = None
    cfg._config_dir_source = None
    cfg._cached_model = None
    return cfg


def test_agent_search_config_dir_env_takes_priority(monkeypatch, tmp_path):
    config_dir = tmp_path / "agent-config"
    monkeypatch.setenv("AGENT_SEARCH_CONFIG_DIR", str(config_dir))
    monkeypatch.delenv("SMART_SEARCH_CONFIG_DIR", raising=False)

    cfg = reset_config_resolution()

    assert cfg.config_file == config_dir / "config.json"
    assert cfg.config_dir_source == "environment"
    info = cfg.config_path_info()
    assert info["config_dir_override_value"] == str(config_dir)
    assert "agent-search" in info["default_config_file"]


def test_legacy_smart_search_config_dir_is_read_for_migration(monkeypatch, tmp_path):
    legacy_dir = tmp_path / "legacy-smart-search"
    legacy_dir.mkdir()
    (legacy_dir / "config.json").write_text(json.dumps({"XAI_MODEL": "legacy-model"}), encoding="utf-8")
    monkeypatch.delenv("AGENT_SEARCH_CONFIG_DIR", raising=False)
    monkeypatch.setenv("SMART_SEARCH_CONFIG_DIR", str(legacy_dir))

    cfg = reset_config_resolution()

    assert cfg.config_file == legacy_dir / "config.json"
    assert cfg.config_dir_source == "legacy_smart_search_environment"
    assert cfg.xai_model == "legacy-model"
