#!/usr/bin/env bash
# ============================================
# Minimal Sphinx documentation build script
# Always performs a clean rebuild
# ============================================

set -e  # exit immediately on error

echo "Cleaning previous build..."
rm -rf docs/_build
rm -rf docs/api

echo "Generating autodoc .rst files..."
sphinx-apidoc -o docs/api .

echo "Building HTML documentation..."
sphinx-build -b html docs docs/_build/html

echo
echo "Build completed successfully."
echo "Output: docs/_build/html/"
echo
