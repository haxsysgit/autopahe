# Publishing AutoPahe to PyPI

## Prerequisites

1. **Install build tools**:
```bash
pip install build twine
```

2. **Create PyPI account**:
- Go to https://pypi.org/account/register/
- Verify your email

3. **Create API token** (recommended):
- Go to https://pypi.org/manage/account/token/
- Create token with scope: "Entire account"
- Save the token securely

---

## Build the Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build source distribution and wheel
python3 -m build
```

This creates:
- `dist/autopahe-3.0.0.tar.gz` (source distribution)
- `dist/autopahe-3.0.0-py3-none-any.whl` (wheel)

---

## Test on TestPyPI (Optional but Recommended)

```bash
# Upload to TestPyPI
python3 -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ autopahe

# Try it
autopahe --help
```

---

## Publish to PyPI

```bash
# Upload to PyPI
python3 -m twine upload dist/*
```

When prompted:
- **Username**: `__token__`
- **Password**: Your API token (starts with `pypi-`)

---

## Verify Publication

1. Check package page: https://pypi.org/project/autopahe/
2. Install and test:
```bash
pip install autopahe
autopahe --help
```

---

## Update Existing Package

When releasing a new version:

1. **Update version** in `pyproject.toml`:
```toml
version = "3.0.1"  # Increment version
```

2. **Build and upload**:
```bash
rm -rf dist/
python3 -m build
python3 -m twine upload dist/*
```

---

## Version Numbering

Follow **Semantic Versioning** (semver):
- **Major** (3.x.x): Breaking changes
- **Minor** (x.0.x): New features, backward compatible
- **Patch** (x.x.1): Bug fixes, backward compatible

Examples:
- `3.0.0` → `3.0.1`: Bug fix
- `3.0.0` → `3.1.0`: New feature
- `3.0.0` → `4.0.0`: Breaking change

---

## Troubleshooting

### "File already exists" error
- You cannot re-upload the same version
- Increment version number in `pyproject.toml`

### "Invalid credentials" error
- Check API token is correct
- Username must be `__token__` (not your PyPI username)

### "Package name already taken" error
- Choose a different name in `pyproject.toml`
- Or contact PyPI support to claim abandoned project

---

## .pypirc Configuration (Optional)

Create `~/.pypirc` for easier uploads:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YourAPITokenHere

[testpypi]
username = __token__
password = pypi-YourTestAPITokenHere
```

Then upload without entering credentials:
```bash
python3 -m twine upload dist/*
```

---

## Recommended Workflow

```bash
# 1. Make changes
git add .
git commit -m "feat: Add new feature"

# 2. Update version
# Edit pyproject.toml: version = "3.1.0"

# 3. Build
rm -rf dist/
python3 -m build

# 4. Test locally
pip install dist/autopahe-3.1.0-py3-none-any.whl
autopahe --help

# 5. Upload to PyPI
python3 -m twine upload dist/*

# 6. Tag release
git tag v3.1.0
git push origin v3.1.0
```

---

## Package Metadata

Current `pyproject.toml` includes:
- ✅ Name, version, description
- ✅ Python version requirements
- ✅ Dependencies
- ✅ License
- ✅ Keywords
- ✅ Classifiers
- ✅ URLs (homepage, repo, issues)
- ✅ CLI entry point (`autopahe` command)

All ready for PyPI publication!

---

## Post-Publication

1. **Update README badge**:
```markdown
[![PyPI version](https://badge.fury.io/py/autopahe.svg)](https://pypi.org/project/autopahe/)
```

2. **Create GitHub release**:
- Go to Releases → Create new release
- Tag: `v3.0.0`
- Title: `AutoPahe v3.0.0 - Major Performance Update`
- Description: Link to OPTIMIZATION_SUMMARY.md

3. **Announce**:
- Reddit: r/anime, r/animepiracy
- GitHub Discussions
- Social media

---

## Useful Commands

```bash
# Check package metadata
python3 -m twine check dist/*

# List uploaded versions
pip index versions autopahe

# Install specific version
pip install autopahe==3.0.0

# Uninstall
pip uninstall autopahe
```

---

**Ready to publish!** 🚀

Just run:
```bash
python3 -m build
python3 -m twine upload dist/*
```
