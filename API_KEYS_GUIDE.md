# API Keys Setup Guide

This guide walks you through obtaining all API keys needed for Zoo MCP.

---

## Required vs Optional Keys

| API | Required? | Purpose | Free Tier? |
|-----|-----------|---------|------------|
| GitHub Token | **Recommended** | Higher rate limits (5000/hr vs 60/hr) | ✅ Yes |
| Libraries.io | **Recommended** | Find package dependents | ✅ Yes |
| Exa | **Recommended** | Semantic/neural code search | ✅ Yes ($10 free credits) |
| Grep.app | Optional | Enhanced code search (public instance is free) | ✅ Yes |
| Stack Exchange | Optional | Slightly higher rate limits | ✅ Yes |

---

## 1. GitHub Personal Access Token (Recommended)

**Why:** Without a token, you're limited to 60 requests/hour. With a token: 5000 requests/hour.

### Steps:

1. Go to **[GitHub Settings > Developer Settings > Personal Access Tokens > Tokens (classic)](https://github.com/settings/tokens)**
   - Direct link: https://github.com/settings/tokens

2. Click **"Generate new token"** → **"Generate new token (classic)"**

3. Fill in the form:
   - **Note**: `zoo-mcp-server` (or any name you prefer)
   - **Expiration**: Choose your preference (30 days, 90 days, or no expiration)
   - **Scopes**: Select **ONLY** these:
     - ✅ `public_repo` (under "repo" section) - for public repo access
     - ✅ `read:org` (under "admin:org") - optional, for org filtering

4. Click **"Generate token"** at the bottom

5. **Copy the token immediately** (you won't see it again!)
   - Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

6. Add to your `.env`:
   ```bash
   GITHUB_TOKEN=ghp_your_token_here
   ```

---

## 2. Libraries.io API Key (Recommended)

**Why:** Find which repos use a specific package (e.g., "who uses axios?"). Essential for discovering real-world usage examples.

### Steps:

1. Go to **[Libraries.io](https://libraries.io/)**
   - Direct link: https://libraries.io/

2. Click **"Sign in"** (top right) or **"Sign up"**
   - You can sign in with GitHub (easiest)

3. After signing in, go to **[Account Settings](https://libraries.io/account)**
   - Direct link: https://libraries.io/account

4. Scroll down to **"API Key"** section

5. Your API key will be displayed (format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
   - If you don't see one, click **"Generate API Key"**

6. Copy the key and add to your `.env`:
   ```bash
   LIBRARIESIO_API_KEY=your_key_here
   ```

**Rate Limits:** 60 requests/minute (free tier)

---

## 3. Grep.app API (Optional)

**Why:** Cross-repo regex search for code patterns. The public instance works without a key, but private deployments may need one.

### Public Instance (No Key Required):

The default configuration works out of the box:
```bash
GREP_API_URL=https://grep.app/api/search
GREP_API_KEY=
```

### Private/Self-Hosted Instance:

If you're running your own Grep.app instance:

1. Contact your Grep.app administrator for API credentials

2. Add to your `.env`:
   ```bash
   GREP_API_URL=https://your-grep-instance.com/api/search
   GREP_API_KEY=your_api_key_here
   ```

**Note:** The public grep.app instance has rate limits but no key required.

---

## 4. Exa API Key (Recommended)

**Why:** Semantic/neural search for code examples. Unlike keyword search, Exa understands meaning - search for "authentication patterns" and find relevant implementations even if they don't contain those exact words.

### Steps:

1. Go to **[Exa.ai](https://exa.ai/)**
   - Direct link: https://exa.ai/

2. Click **"Get API Key"** or **"Sign Up"** (top right)
   - Sign in with Google or email

3. After signing in, go to **[Dashboard > API Keys](https://dashboard.exa.ai/api-keys)**
   - Direct link: https://dashboard.exa.ai/api-keys

4. Copy your API key
   - Format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` (UUID format)
   - You get **$10 in free credits** to start

5. Add to your `.env`:
   ```bash
   EXA_API_KEY=your_key_here
   ```

**Key Features:**
- Neural search: finds code by meaning, not just keywords
- Searches 1B+ webpages (GitHub, Stack Overflow, docs)
- Returns dense, relevant context for coding agents
- Rate limit: 5 queries/second (default)

**Pricing:**
- $10 free credits included
- ~$0.005 per search (1-25 results)
- Pay-as-you-go after free credits

---

## 5. Stack Exchange API Key (Optional)

**Why:** Fetch accepted Stack Overflow answers with code. The key gives you higher rate limits (10,000/day vs 300/day).

### Steps:

1. Go to **[Stack Apps](https://stackapps.com/)**
   - Direct link: https://stackapps.com/

2. Log in with your Stack Overflow account (or create one at https://stackoverflow.com/)

3. Go to **[Register a new application](https://stackapps.com/apps/oauth/register)**
   - Direct link: https://stackapps.com/apps/oauth/register

4. Fill in the form:
   - **Application Name**: `zoo-mcp` (or any name)
   - **Description**: `Code example discovery MCP server`
   - **OAuth Domain**: Leave blank (not needed for API key)
   - **Application Website**: `http://localhost` (or your site)

5. After creating, you'll see your **Key** on the app page
   - Format: `xxxxxxxxxxxxxx)`

6. Add to your `.env`:
   ```bash
   STACKEXCHANGE_KEY=your_key_here
   ```

**Alternative (Simpler):** You can also get a key instantly here:
- Go to https://api.stackexchange.com/docs
- Click "Run" on any API endpoint
- You'll get an instant API key displayed

**Rate Limits:**
- Without key: 300 requests/day
- With key: 10,000 requests/day

---

## Final .env Configuration

After obtaining your keys, your `.env` should look like:

```bash
# GitHub API (RECOMMENDED)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Grep.app API (optional - defaults work)
GREP_API_URL=https://grep.app/api/search
GREP_API_KEY=

# Libraries.io API (RECOMMENDED)
LIBRARIESIO_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Exa API (RECOMMENDED for semantic search)
EXA_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Stack Exchange API (optional)
STACKEXCHANGE_KEY=xxxxxxxxxxxxxx

# Organization allowlist (optional - CSV)
# Example: aws-samples,GoogleCloudPlatform,microsoft,openai,tokio-rs
ORG_ALLOWLIST=

# Workspace directory for downloaded archives
ZOO_MCP_WORKSPACE=./workspace

# Maximum response size in bytes (default: 300000 = ~300KB)
ZOO_MCP_MAX_RETURN_BYTES=300000
```

---

## Testing Your Configuration

After setting up your keys, test the server:

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your keys
nano .env  # or use your preferred editor

# Test the server starts
python -m zoo_mcp.server --help

# Test with a tool (if you have MCP client configured)
# The server will log if any API keys are missing
```

---

## Troubleshooting

### GitHub Token Issues

**Error: "Bad credentials"**
- Token may have expired or been revoked
- Regenerate a new token following steps above

**Error: "Rate limit exceeded"**
- You may not have set the token in `.env`
- Check that `GITHUB_TOKEN` is uncommented

### Libraries.io Issues

**Error: "Unauthorized"**
- Check your API key is correct in `.env`
- Verify you copied the entire key (no spaces)

**Warning: "Libraries.io API key not set"**
- The tool will still work but return empty results
- Add the key to enable dependent search

### Stack Exchange Issues

**Low rate limits**
- Add a key to increase from 300 to 10,000 requests/day

---

## Security Notes

1. **Never commit your `.env` file** to version control
   - It's already in `.gitignore`

2. **Keep tokens secure**
   - Treat them like passwords
   - Rotate them periodically

3. **Minimal permissions**
   - GitHub token only needs `public_repo` access
   - Don't grant unnecessary scopes

4. **Revoke unused tokens**
   - Go to GitHub settings to revoke old tokens
   - Libraries.io: regenerate key in account settings

---

## Quick Start (TL;DR)

**Minimum viable setup (works immediately):**

```bash
# Just copy the example
cp .env.example .env

# Run the server (will work with public APIs, reduced rate limits)
python -m zoo_mcp.server stdio
```

**Recommended setup (5 minutes):**

1. Get GitHub token: https://github.com/settings/tokens → Generate (public_repo scope)
2. Get Libraries.io key: https://libraries.io/account → Copy API key
3. Get Exa key: https://dashboard.exa.ai/api-keys → Copy key
4. Add all to `.env`
5. Done!

**Full setup (10 minutes):**
- Follow all sections above for optimal rate limits

---

## Support

- **GitHub API docs**: https://docs.github.com/en/rest
- **Libraries.io docs**: https://libraries.io/api
- **Exa API docs**: https://docs.exa.ai/
- **Stack Exchange API docs**: https://api.stackexchange.com/docs

For Zoo MCP issues, see README.md or open an issue.