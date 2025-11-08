#!/bin/bash
# Script to publish Memphora SDK to PyPI
# Run this from the sdk/ directory

set -e

echo "🚀 Publishing Memphora SDK to PyPI"
echo "===================================="
echo ""

# Check if we're in the right directory
if [ ! -f "setup.py" ] || [ ! -f "pyproject.toml.sdk" ]; then
    echo "❌ Error: Must run from sdk/ directory"
    echo "   Current directory: $(pwd)"
    exit 1
fi

# Step 1: Install build tools
echo "📦 Step 1: Installing build tools..."
pip install --upgrade build twine

# Step 2: Clean previous builds
echo ""
echo "🧹 Step 2: Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/ __pycache__/

# Step 3: Use standalone SDK version (if needed)
if [ -f "memphora_sdk_standalone.py" ]; then
    echo ""
    echo "📝 Step 3: Using standalone SDK version..."
    # Backup original if it exists
    if [ -f "memphora_sdk.py" ]; then
        cp memphora_sdk.py memphora_sdk.py.backup
    fi
    # Use standalone version
    cp memphora_sdk_standalone.py memphora_sdk.py
fi

# Step 4: Use SDK pyproject.toml
echo ""
echo "📋 Step 4: Using SDK configuration..."
if [ -f "pyproject.toml" ]; then
    cp pyproject.toml pyproject.toml.backup
fi
cp pyproject.toml.sdk pyproject.toml

# Step 5: Build package
echo ""
echo "🔨 Step 5: Building package..."
python3 -m build

# Step 6: Check build
echo ""
echo "✅ Step 6: Checking build..."
python3 -m twine check dist/*

# Step 7: Show package info
echo ""
echo "📦 Package built successfully!"
echo ""
ls -lh dist/
echo ""

# Step 8: Ask for upload
echo "📤 Ready to upload!"
echo ""
echo "Options:"
echo "  1. Upload to TestPyPI (recommended first):"
echo "     python3 -m twine upload --repository testpypi dist/*"
echo ""
echo "  2. Upload to PyPI (production):"
echo "     python3 -m twine upload dist/*"
echo ""
read -p "Upload to TestPyPI now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📤 Uploading to TestPyPI..."
    python3 -m twine upload --repository testpypi dist/*
    echo ""
    echo "✅ Uploaded to TestPyPI!"
    echo ""
    echo "Test installation with:"
    echo "  pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ memphora"
    echo ""
    read -p "Upload to production PyPI now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "📤 Uploading to PyPI..."
        python3 -m twine upload dist/*
        echo ""
        echo "✅ Uploaded to PyPI!"
        echo ""
        echo "Install with:"
        echo "  pip install memphora"
    fi
fi

# Step 9: Restore backups (optional)
echo ""
read -p "Restore original files? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "memphora_sdk.py.backup" ]; then
        mv memphora_sdk.py.backup memphora_sdk.py
        echo "✅ Restored memphora_sdk.py"
    fi
    if [ -f "pyproject.toml.backup" ]; then
        mv pyproject.toml.backup pyproject.toml
        echo "✅ Restored pyproject.toml"
    fi
fi

echo ""
echo "✅ Done!"


