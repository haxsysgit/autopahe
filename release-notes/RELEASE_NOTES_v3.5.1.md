# AutoPahe v3.5.1 Release Notes

## Fixes
- Streaming: resolve the default player before cached streaming to avoid "default" player errors.
- Streaming: VLC now uses play-and-exit so multi-episode streams can advance automatically.
- Output: streaming logs are indented consistently and avoid extra blank lines.

## Packaging
- Removed legacy `setup.py`; packaging now relies on `pyproject.toml`.

## Installation
```bash
pip install autopahe==3.5.1
```
