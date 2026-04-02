@echo off
REM Installation script for Windows

set PLUGIN_DIR=%USERPROFILE%\.claude\plugins\repos\claude-code-tracker

if exist "%PLUGIN_DIR%" (
    echo Updating existing installation...
    git -C "%PLUGIN_DIR%" pull
) else (
    echo Installing claude-code-tracker...
    git clone https://github.com/55onurisik/claude-code-tracker "%PLUGIN_DIR%"
)

echo.
echo Done! Restart Claude Code to activate the plugin.
echo.
echo Test with: /token-tracker:stats
pause
