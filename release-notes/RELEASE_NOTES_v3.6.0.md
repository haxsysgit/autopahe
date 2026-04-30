# AutoPahe v3.6.0 Release Notes

## Major Workflow Update
- AutoPahe now treats Kwik downloads as browser-required.
- `-d` and `-md` prepare browser download links and verify the downloaded file before updating records.
- `-l` prints the generated link only and does not mark an episode as downloaded.

## Fixes
- Updated AnimePahe domains from stale `.si`/`.ru` references to `.pw`, `.com`, and `.org`.
- Added `autopahe --update` so users can update existing installs without recloning.
- Fixed Playwright cleanup after failed browser startup.
- Fixed download completion tracking so blocked or unverified downloads are not recorded as successful.

## Packaging
- Bumped version to `3.6.0`.
- Added explicit `click` dependency.

## Installation
```bash
uv tool install autopahe==3.6.0
```

## Updating
```bash
uv tool upgrade autopahe
```
