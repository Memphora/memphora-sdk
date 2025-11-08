# Publishing Memphora SDK to PyPI

This guide explains how to publish the Memphora SDK to PyPI (Python Package Index).

## Prerequisites

1. **PyPI Account**: Create an account at https://pypi.org/account/register/
2. **TestPyPI Account**: Create an account at https://test.pypi.org/account/register/ (for testing)
3. **API Token**: Generate an API token at https://pypi.org/manage/account/token/
   - For TestPyPI: https://test.pypi.org/manage/account/token/

## Quick Start

### Option 1: Use the Automated Script

```bash
cd sdk
./publish_to_pypi.sh
```

The script will:
1. Install build tools (build, twine)
2. Clean previous builds
3. Use standalone SDK version
4. Build the package
5. Check the build
6. Guide you through uploading

### Option 2: Manual Steps

#### 1. Install Build Tools

```bash
pip install --upgrade build twine
```

#### 2. Navigate to SDK Directory

```bash
cd sdk
```

#### 3. Clean Previous Builds

```bash
rm -rf dist/ build/ *.egg-info/ __pycache__/
```

#### 4. Use Standalone SDK (if needed)

```bash
# Backup original
cp memphora_sdk.py memphora_sdk.py.backup
# Use standalone version
cp memphora_sdk_standalone.py memphora_sdk.py
```

#### 5. Use SDK Configuration

```bash
# Backup original
cp pyproject.toml pyproject.toml.backup
# Use SDK version
cp pyproject.toml.sdk pyproject.toml
```

#### 6. Build the Package

```bash
python3 -m build
```

This creates:
- `dist/memphora-1.0.0.tar.gz` (source distribution)
- `dist/memphora-1.0.0-py3-none-any.whl` (wheel)

#### 7. Check the Build

```bash
python3 -m twine check dist/*
```

#### 8. Upload to TestPyPI (Recommended First)

```bash
python3 -m twine upload --repository testpypi dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token

#### 9. Test Installation from TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ memphora
```

#### 10. Upload to Production PyPI

Once tested, upload to production:

```bash
python3 -m twine upload dist/*
```

## Package Configuration

The SDK package is configured in:
- `setup.py` - Setuptools configuration
- `pyproject.toml.sdk` - Modern Python packaging configuration

**Package Details:**
- Name: `memphora`
- Version: `1.0.0` (update before each release)
- Description: "Memphora SDK - Persistent memory layer for AI agents (SaaS)"
- Dependencies: `requests>=2.31.0`, `urllib3>=2.1.0`

## Updating Version

Before publishing a new version:

1. Update version in `setup.py`:
   ```python
   version="1.0.1",  # Increment version
   ```

2. Update version in `pyproject.toml.sdk`:
   ```toml
   version = "1.0.1"
   ```

3. Build and publish as above

## Files Included in Package

The SDK package includes:
- `memphora_sdk.py` (or `memphora_sdk_standalone.py`)
- `memory_client.py`

Excluded:
- Backend code (`api/`, `core/`)
- Tests
- Examples
- Docker files
- Documentation files

## Verification

After publishing, verify the package:

1. **Check PyPI page**: https://pypi.org/project/memphora/
2. **Test installation**:
   ```bash
   pip install memphora
   python3 -c "import memphora_sdk; print('✅ SDK installed successfully')"
   ```

## Troubleshooting

### "Package already exists" error
- Version already published - increment version number

### "Invalid credentials" error
- Check your PyPI API token
- Make sure you're using `__token__` as username

### "Build failed" error
- Check that all required files exist
- Verify `pyproject.toml.sdk` is valid
- Check Python version (requires Python 3.8+)

## Best Practices

1. **Always test on TestPyPI first** before publishing to production
2. **Increment version** for each release
3. **Update changelog** if you maintain one
4. **Tag releases** in git: `git tag v1.0.0`
5. **Test installation** after publishing

## Current Package Info

- **Package Name**: `memphora`
- **Current Version**: `1.0.0`
- **PyPI URL**: https://pypi.org/project/memphora/
- **Installation**: `pip install memphora`


