from ap_core.config import DEFAULTS, load_app_config, sample_config_text


def test_default_browser_matches_setup_browser():
    assert DEFAULTS["browser"] == "chromium"
    assert "browser = chromium" in sample_config_text()


def test_invalid_browser_falls_back_to_chromium(tmp_path):
    config_path = tmp_path / "config.ini"
    config_path.write_text("[defaults]\nbrowser = netscape\n", encoding="utf-8")

    config, path_used, warnings = load_app_config(str(config_path))

    assert path_used == str(config_path)
    assert config["browser"] == "chromium"
    assert any("Invalid browser" in warning for warning in warnings)
