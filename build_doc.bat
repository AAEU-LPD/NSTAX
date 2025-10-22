@echo off
REM ============================================
REM Minimal Sphinx documentation build script
REM Always performs a clean rebuild
REM ============================================

ECHO Cleaning previous build...
IF EXIST docs\_build RMDIR /S /Q docs\_build
IF EXIST docs\api RMDIR /S /Q docs\api

ECHO Generating autodoc .rst files...
sphinx-apidoc -o docs/api .

ECHO Building HTML documentation...
sphinx-build -b html docs docs/_build/html

REM ECHO Opening generated documentation...
REM START "" docs\_build\html\index.html

ECHO.
ECHO Build completed successfully.
ECHO Output: docs\_build\html\
ECHO.