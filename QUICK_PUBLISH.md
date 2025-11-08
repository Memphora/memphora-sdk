# Quick Publishing Guide

## Prerequisites
1. Create PyPI account: https://pypi.org/account/register/
2. Create API token: https://pypi.org/manage/account/token/
   - Username: `__token__`
   - Password: Your API token

## Publish Steps

### Method 1: Automated Script
```bash
cd sdk
./publish_to_pypi.sh
```

### Method 2: Manual Steps

```bash
cd sdk

# 1. Install build tools
pip install --upgrade build twine

# 2. Clean previous builds
rm -rf dist/ build/ *.egg-info/

# 3. Use standalone SDK (no internal dependencies)
cp memphora_sdk_standalone.py memphora_sdk.py
cp pyproject.toml.sdk pyproject.toml

# 4. Build package
python3 -m build

# 5. Check build
python3 -m twine check dist/*

# 6. Upload to TestPyPI (test first!)
python3 -m twine upload --repository testpypi dist/*
# Username: __token__
# Password: [Your API token]

# 7. Test installation
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ memphora

# 8. Upload to Production PyPI
python3 -m twine upload dist/*
```

## After Publishing

Install with:
```bash
pip install memphora
```

Use in code:
```python
from memphora_sdk import Memphora

memory = Memphora(
    user_id="user123",
    api_key="your_api_key"
)
```

## Updating Version

Before publishing a new version, update:
1. `setup.py` - version="1.0.1"
2. `pyproject.toml.sdk` - version = "1.0.1"

Then rebuild and publish.
