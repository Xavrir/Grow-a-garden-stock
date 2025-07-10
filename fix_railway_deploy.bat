@echo off
echo ========================================
echo Discord Forwarder GitHub Fix and Push
echo ========================================
echo.
echo This script will update your GitHub repository with the fixed requirements
echo to resolve the aiohttp installation issue on Railway.
echo.
pause

cd /d "%~dp0"
echo Current directory: %CD%
echo.

echo Step 1: Staging the updated files...
git add requirements.txt railway.json runtime.txt RAILWAY_TROUBLESHOOTING.md
echo.

echo Step 2: Committing fixes...
git commit -m "Fix aiohttp compatibility issue for Railway deployment"
echo.

echo Step 3: Pushing to GitHub...
git push origin main
if %errorlevel% neq 0 (
    echo.
    echo Trying with master branch instead...
    git push origin master
)

echo.
if %errorlevel% equ 0 (
    echo ========================================
    echo SUCCESS! Your fixed code has been pushed to GitHub.
    echo.
    echo Now go to Railway.app and redeploy your application.
    echo Check the logs to ensure it builds successfully.
    echo ========================================
) else (
    echo ========================================
    echo WARNING: There were issues with the push.
    echo.
    echo Please try pushing manually:
    echo git push origin main
    echo ========================================
)

echo.
pause
