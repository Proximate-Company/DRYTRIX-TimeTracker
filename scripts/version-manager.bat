@echo off
REM Version Manager for TimeTracker - Windows Batch Wrapper

if "%1"=="" (
    echo Usage: version-manager.bat [action] [options]
    echo.
    echo Actions:
    echo   tag [version] [message]  - Create a version tag
    echo   build [number]           - Create a build tag
    echo   list                     - List all tags
    echo   info [tag]               - Show tag information
    echo   status                   - Show current status
    echo   suggest                  - Suggest next version
    echo.
    echo Examples:
    echo   version-manager.bat tag v1.2.3 "Release 1.2.3"
    echo   version-manager.bat build 123
    echo   version-manager.bat status
    echo.
    exit /b 1
)

python scripts/version-manager.py %*
