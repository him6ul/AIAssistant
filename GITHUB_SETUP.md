# GitHub Integration Setup

This guide shows how to connect your AI Assistant to your GitHub account (him6ul).

## Step 1: Create GitHub Personal Access Token

1. **Go to GitHub Settings**:
   - Visit: https://github.com/settings/tokens
   - Or: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)

2. **Generate New Token**:
   - Click "Generate new token" → "Generate new token (classic)"
   - Give it a name: "AI Assistant"
   - Set expiration (recommended: 90 days or custom)

3. **Select Scopes** (permissions):
   - ✅ `repo` - Full control of private repositories
   - ✅ `read:org` - Read org and team membership (if needed)
   - ✅ `read:user` - Read user profile data
   - ✅ `user:email` - Access user email addresses

4. **Generate and Copy Token**:
   - Click "Generate token"
   - **IMPORTANT**: Copy the token immediately (you won't see it again!)
   - It will look like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Step 2: Add Token to Environment

Add the token to your `.env` file:

```bash
cd /Users/himanshu/SourceCode/Personal/AI_Assistant
echo "GITHUB_ACCESS_TOKEN=your_token_here" >> .env
```

Or edit `.env` directly and add:
```env
GITHUB_ACCESS_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Step 3: Install PyGithub (if not already installed)

```bash
source venv/bin/activate
pip install PyGithub
```

## Step 4: Restart Backend

```bash
# Stop current backend
pkill -f "python.*app.main"

# Start again (it will load the new token)
./scripts/run_backend.sh
```

## Step 5: Test Connection

### Test via API

```bash
# Get your GitHub user info
curl http://localhost:8000/github/user

# Get your repositories
curl http://localhost:8000/github/repos

# Get repositories for specific user
curl "http://localhost:8000/github/repos?username=him6ul"

# Get specific repository
curl http://localhost:8000/github/repos/him6ul/AI_Assistant

# Get issues from a repo
curl http://localhost:8000/github/repos/him6ul/AI_Assistant/issues

# Get pull requests
curl http://localhost:8000/github/repos/him6ul/AI_Assistant/pulls
```

### Test via Chat

Ask the assistant:
- "Show me my GitHub repositories"
- "What are the open issues in my AI_Assistant repo?"
- "Create a GitHub issue in AI_Assistant with title 'Test issue'"

## Available GitHub Endpoints

### GET `/github/user`
Get authenticated user information (your profile)

### GET `/github/repos`
Get all repositories for a user
- Query param: `username` (optional, defaults to authenticated user)

### GET `/github/repos/{repo_name}`
Get information about a specific repository
- Example: `/github/repos/him6ul/AI_Assistant`

### GET `/github/repos/{repo_name}/issues`
Get issues for a repository
- Query param: `state` (open, closed, all) - default: open

### POST `/github/repos/{repo_name}/issues`
Create a new issue
- Body: `{"title": "Issue title", "body": "Description", "labels": ["bug", "enhancement"]}`

### GET `/github/repos/{repo_name}/pulls`
Get pull requests for a repository
- Query param: `state` (open, closed, all) - default: open

## Example Usage

### Get Your Repositories
```bash
curl http://localhost:8000/github/repos
```

### Get Issues from a Repo
```bash
curl "http://localhost:8000/github/repos/him6ul/AI_Assistant/issues?state=open"
```

### Create an Issue
```bash
curl -X POST http://localhost:8000/github/repos/him6ul/AI_Assistant/issues \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New feature request",
    "body": "This is a test issue created by AI Assistant",
    "labels": ["enhancement"]
  }'
```

## Troubleshooting

### "GitHub not configured"
- Make sure `GITHUB_ACCESS_TOKEN` is in your `.env` file
- Restart the backend after adding the token
- Check that the token is valid (not expired)

### "Bad credentials"
- Token may be invalid or expired
- Generate a new token and update `.env`
- Make sure you copied the full token

### "Not found" errors
- Check repository name format: `owner/repo` or just `repo` for your own repos
- Verify the repository exists and you have access

### Rate limiting
- GitHub API has rate limits (5000 requests/hour for authenticated users)
- If you hit the limit, wait an hour or use a token with higher limits

## Security Notes

- ⚠️ **Never commit your `.env` file** - it contains your token!
- ✅ The token is stored locally in `.env` only
- ✅ Use tokens with minimal required permissions
- ✅ Set token expiration dates
- ✅ Rotate tokens periodically

## Next Steps

1. ✅ Get GitHub token
2. ✅ Add to `.env`
3. ✅ Restart backend
4. ✅ Test connection
5. ✅ Use in chat/voice commands!

---

**Ready to connect?** Get your token at: https://github.com/settings/tokens

