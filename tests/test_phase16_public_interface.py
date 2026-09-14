from __future__ import annotations

import json

from ksupervisor.cli import main
from ksupervisor.config import PlatformConfig, load_config


def test_platform_config_loads_json_and_toml(tmp_path):
    json_path = tmp_path / "config.json"
    json_path.write_text(json.dumps({"state_db_path": "state/test.db"}), encoding="utf-8")
    assert load_config(json_path).state_db_path == "state/test.db"

    toml_path = tmp_path / "config.toml"
    toml_path.write_text('state_db_path = "state/test.db"\nstrict_extensions = false\n', encoding="utf-8")
    loaded = load_config(toml_path)
    assert loaded == PlatformConfig(state_db_path="state/test.db", strict_extensions=False)


def test_cli_version_and_config_validation(tmp_path, capsys):
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == "0.1.0"

    path = tmp_path / "config.json"
    path.write_text("{}", encoding="utf-8")
    assert main(["validate-config", str(path)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["config_version"] == "1"
