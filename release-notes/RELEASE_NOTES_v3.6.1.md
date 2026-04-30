# AutoPahe v3.6.1 Release Notes

## Fixes
- `autopahe --setup` now installs Playwright's bundled Chromium engine directly for consistent Windows, macOS, and Linux setup.
- `--setup` now preserves existing user config files instead of overwriting them.
- Default browser is now `chromium`, matching the browser engine installed by setup.
- Added `autopahe --verify-browser URL` to open AutoPahe's persistent browser profile for normal user-completed verification.

## Documentation
- README now recommends uv-managed installs and upgrades:
```bash
uv tool install autopahe
uv tool upgrade autopahe
```

## Installation
```bash
uv tool install autopahe==3.6.1
```
