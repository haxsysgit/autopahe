from kwikdown import _build_safe_filename, _is_security_challenge


def test_build_safe_filename_normalizes_anime_title_episode_and_quality():
    assert _build_safe_filename("One Piece: East Blue", ep=1, quality="720") == (
        "AnimePahe_One_Piece_East_Blue_01_720p.mp4"
    )


def test_security_challenge_detection_matches_cloudflare_text():
    body = "kwik.cx Performing security verification This website verifies you are not a bot Cloudflare"

    assert _is_security_challenge(body)
