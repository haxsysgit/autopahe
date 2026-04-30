from cli import _normalize_cli_argv


def test_normalize_legacy_multi_download_flag():
    assert _normalize_cli_argv(["autopahe", "-md", "1-3"]) == [
        "autopahe",
        "--multi_download",
        "1-3",
    ]


def test_normalize_records_values_into_single_option_payload():
    assert _normalize_cli_argv(["autopahe", "-R", "search", "one", "piece", "-s", "x"]) == [
        "autopahe",
        "--records",
        "search\x1fone\x1fpiece",
        "-s",
        "x",
    ]
