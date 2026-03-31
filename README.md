# CDS MCP Server

A Model Context Protocol (MCP) server for integrating with CERN Document Server (CDS), built on the Invenio digital library framework.

## Features

- **Search CDS documents** with filters for experiments, document types, and date ranges
- **Get detailed document information** including full abstracts, authors, and metadata
- **Access document files** with download URLs and file metadata
- **Browse experiments and document types** for better search filtering

### Future Authentication

We are working on implementing proper authentication through:
- CERN Single Sign-On (SSO) integration
- OAuth/SAML authentication flows
- Automatic session management

## Installation

Requires Python 3.10+.

### Quickstart (recommended)

No installation needed, just use [uvx](https://docs.astral.sh/uv/) to run directly:

```bash
uvx cds-mcp
```

### From PyPI

```bash
pip install cds-mcp
```

### From source

```bash
git clone https://github.com/MohamedElashri/cds-mcp
cd cds-mcp
uv sync
```

## Usage

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "cds": {
      "command": "uvx",
      "args": ["cds-mcp"],
      "env": {
        "CDS_SESSION_COOKIE": "your_session_cookie_here"
      }
    }
  }
}
```

For **public access only**, omit the `CDS_SESSION_COOKIE`:

```json
{
  "mcpServers": {
    "cds": {
      "command": "uvx",
      "args": ["cds-mcp"],
      "env": {}
    }
  }
}
```

Note for macOS users: If you see an error about `uvx` not being found, you may need to provide the absolute path. Claude Desktop does not support `~` or `$HOME` expansion.

1. Run `which uvx` in your terminal to find the path (e.g., `/Users/yourusername/.local/bin/uvx`).
2. Use that absolute path in the `command` field:

```json
"command": "/Users/yourusername/.local/bin/uvx"
```

### Claude Code

Project-specific (default) — installs in the current directory's configuration:

```bash
claude mcp add cds-mcp -- uvx cds-mcp
```

Global — installs for your user account (works in all projects):

```bash
claude mcp add --scope user cds-mcp -- uvx cds-mcp
```

To include authentication, add `-e CDS_SESSION_COOKIE=your_session_cookie_here` before the `--`:

```bash
# Example: Global installation with authentication
claude mcp add --scope user -e CDS_SESSION_COOKIE=your_session_cookie_here cds-mcp -- uvx cds-mcp
```

Manual Configuration — you can also manually edit your global config at `~/.claude.json` (on Linux/macOS) or `%APPDATA%\Claude\claude.json` (on Windows):

```json
{
  "mcpServers": {
    "cds": {
      "command": "uvx",
      "args": ["cds-mcp"],
      "env": {
        "CDS_SESSION_COOKIE": "your_session_cookie_here"
      }
    }
  }
}
```

### GitHub Copilot

Add to your VS Code `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "cds": {
        "command": "uvx",
        "args": ["cds-mcp"],
        "env": {
          "CDS_SESSION_COOKIE": "your_session_cookie_here"
        }
      }
    }
  }
}
```

Or add a `.vscode/mcp.json` to your project:

```json
{
  "servers": {
    "cds": {
      "command": "uvx",
      "args": ["cds-mcp"],
      "env": {
        "CDS_SESSION_COOKIE": "your_session_cookie_here"
      }
    }
  }
}
```

### Gemini CLI

Add to your `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "cds": {
      "command": "uvx",
      "args": ["cds-mcp"],
      "env": {
        "CDS_SESSION_COOKIE": "your_session_cookie_here"
      }
    }
  }
}
```

### Direct usage

```bash
# Run with uvx (no install needed)
uvx cds-mcp

# Or if installed from PyPI
cds-mcp

# Or from source
uv run cds-mcp

# With authentication
CDS_SESSION_COOKIE=your_session_cookie_here uvx cds-mcp
```


## Access Limitations & Authentication

**⚠️ Current Status: Public Access Only**

This MCP server currently **only accesses public CDS records**. Experiment-specific restricted content (ATLAS/CMS/LHC Internal Notes, etc.) requires authentication that is not yet fully supported.

### Restricted Collections

The following collections in particular require experiment membership and authentication:
- **ATLAS**: Internal Notes, Communications, Conference Slides
- **CMS**: Internal Notes, Analysis Notes
- **LHCb**: Internal Notes, Analysis Notes
- **ALICE**: Internal Notes, Analysis Notes

### Workaround for Restricted Access

**⚠️ TEMPORARY SOLUTION**: If you need access to restricted content, you can use your browser session cookie as a workaround:

1. **Log into CDS** in your browser (https://cds.cern.ch)
2. **Extract your session cookie**:
   - Open Developer Tools (F12)
   - Go to Application/Storage → Cookies → https://cds.cern.ch
   - Copy the value of `INVENIOSESSION`
3. **Set the environment variable**:
   ```bash
   export CDS_SESSION_COOKIE="session_cookie_here"
   ```

**Important Notes**:
- This is a **temporary workaround** while we develop proper authentication
- Session cookies **expire** and need to be refreshed periodically
- This method requires **manual cookie management**
- **Proper CERN SSO integration** is planned for future releases

I'm not sure how happy CERN IT will be happy about this approach. So please be carefull while doing it. Deal with this session cookie as a secret and don't share it with anyone.


## Tools

1. **`search_cds_documents`** — Search CDS with various filters
2. **`get_cds_document_details`** — Get detailed information about a specific document
3. **`get_cds_document_files`** — Get file information and download URLs
4. **`get_cds_experiments`** — List available CERN experiments for filtering
5. **`get_cds_document_types`** — List available document types for filtering

## Example Prompts

### Search for repositories
- "Search CDS for LHCb notes about trigger systems from 2023, then fetch the files for the most recent one."
- "Find ATLAS papers about machine learning published in the last year."

### Understand a project
- "Show me the latest CMS conference papers and get detailed information about the first three."
- "What experiments are available in CDS? Then search for recent theoretical physics papers."

### Find fitting examples
- "Find CDS documents about ROOT data analysis with example code."
- "Search for ALICE papers that include Python analysis scripts."

### View LHCb software stack code
- "Find LHCb software documentation and analysis frameworks in CDS."

### Analyze a project structure
- "Get detailed metadata for this CDS record and analyze its file structure."

### Find usage context
- "Search for papers that cite this specific CDS document."

### Track releases
- "Find the latest versions of ATLAS analysis software documentation."

### Find framework configurations
- "Search for CDS records containing configuration files for physics analysis frameworks."

## Development

```bash
git clone https://github.com/MohamedElashri/cds-mcp
cd cds-mcp
uv sync
uv run python test_integration.py  # Test real CDS API integration
uv run python test_mcp_server.py   # Test MCP server functionality
```

## License

MIT License - see [LICENSE](LICENSE) for details.
