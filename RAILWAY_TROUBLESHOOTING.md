# Troubleshooting Railway Deployment Issues

If you encounter issues deploying to Railway, here are some common problems and solutions:

## Issue: aiohttp Build Failures

### Problem:
Error messages like:
```
ERROR: Failed building wheel for aiohttp
```

### Solution:
This is typically caused by compatibility issues between aiohttp and the Python version. We've already updated the requirements.txt to specify a compatible version, but if you still encounter issues:

1. Make sure you're pushing the updated requirements.txt to GitHub
2. Add runtime.txt (already included) to specify Python 3.11
3. Try manually setting the Python version in Railway:
   - Go to your project settings
   - Add a variable: `NIXPACKS_PYTHON_VERSION=3.11`

## Issue: Role Mapping Not Working

### Problem:
Role mentions still showing as @unknown-role after deployment

### Solution:
1. Verify that role_map.json exists on the server:
   - Go to the Railway "Shell" tab
   - Run: `ls -la` to check if role_map.json exists
   - If not, create it using: `python fix_unknown_role_emergency.py --auto`

2. Check environment variables:
   - Make sure all environment variables are correctly set
   - Specifically check that ALWAYS_CONVERT_ROLE_MENTIONS_TO_TEXT is set to "False"

## Issue: Authentication Failures

### Problem:
Errors about invalid token or authentication failures

### Solution:
1. Make sure your Discord token is still valid
2. Check if you need to re-generate your token
3. Update the token in Railway environment variables

## Issue: General Railway Deployment Issues

### Solution:
1. Check Railway logs for specific error messages
2. Try redeploying by clicking "Deploy" in the Railway dashboard
3. If needed, delete the project and create a new one

## Getting More Help

If you continue to experience issues:
1. Check Railway's documentation: https://docs.railway.app/
2. Look for similar issues on GitHub
3. Ask for help on Discord developer forums

Remember: When sharing logs or error messages for help, always remove sensitive information like tokens and IDs.
