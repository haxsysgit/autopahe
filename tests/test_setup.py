import ap_core.browser
import ap_core.platform_paths
import auto_pahe


def test_setup_preserves_existing_config(monkeypatch, tmp_path):
    config_path = tmp_path / "config.ini"
    config_path.write_text("[defaults]\nbrowser = firefox\n", encoding="utf-8")

    monkeypatch.setattr(ap_core.platform_paths, "get_config_dir", lambda: tmp_path)
    monkeypatch.setattr(ap_core.browser, "install_playwright_browser", lambda browser: True)

    assert auto_pahe.setup_environment()
    assert config_path.read_text(encoding="utf-8") == "[defaults]\nbrowser = firefox\n"
