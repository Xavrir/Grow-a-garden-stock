@echo off
echo ========================================
echo Discord Forwarder GitHub Push Helper
echo ========================================
echo.
echo This script will help you push your Discord Forwarder code to:
echo https://github.com/Xavrir/Grow-a-garden-stock.git
echo.
echo Make sure you have Git installed and have access to this repository.
echo.
pause

cd /d "%~dp0"
echo Current directory: %CD%
echo.

echo Step 1: Initializing Git repository...
git init
echo.

echo Step 2: Adding remote repository...
git remote add origin https://github.com/Xavrir/Grow-a-garden-stock.git
echo.

echo Step 3: Staging all files...
git add .
echo.

echo Step 4: Committing files...
set /p commit_msg="Enter commit message (or press Enter for default): "
if "%commit_msg%"=="" set commit_msg="Add Discord message forwarder with role mention handling"
git commit -m "%commit_msg%"
echo.

echo Step 5: Pushing to GitHub...
echo Choose branch to push to:
echo 1. main (default)
echo 2. master
echo 3. other (you'll be prompted for name)
set /p branch_choice="Enter choice (1-3): "

if "%branch_choice%"=="2" (
    set branch=master
) else if "%branch_choice%"=="3" (
    set /p branch="Enter branch name: "
) else (
    set branch=main
)

echo.
echo Trying to push to %branch% branch...
git push -u origin %branch%

if %errorlevel% neq 0 (
    echo.
    echo First push failed. Trying with pull first...
    git pull origin %branch% --allow-unrelated-histories
    echo.
    echo Now trying push again...
    git push -u origin %branch%
)

echo.
if %errorlevel% equ 0 (
    echo ========================================
    echo SUCCESS! Your code has been pushed to GitHub.
    echo Visit https://github.com/Xavrir/Grow-a-garden-stock to confirm.
    echo ========================================
) else (
    echo ========================================
    echo ATTENTION: There were some issues with the push.
    echo.
    echo If you're asked for credentials, remember:
    echo - Username: Your GitHub username
    echo - Password: Use a GitHub personal access token (not your regular password)
    echo.
    echo To create a token, go to:
    echo GitHub.com → Settings → Developer settings → Personal access tokens
    echo ========================================
)

echo.
pause
