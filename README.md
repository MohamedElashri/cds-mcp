# CDS MCP Server

A Model Context Protocol (MCP) server for integrating with CERN Document Server (CDS), built on the Invenio digital library framework.

## Features

- **Search CDS documents** with filters for experiments, document types, and date ranges
- **Get detailed document information** including full abstracts, authors, and metadata
- **Access document files** with download URLs and file metadata
- **Browse experiments and document types** for better search filtering


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
        "CERN_CLIENT_ID": "your-client-id",
        "CERN_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

For **public access only**, omit the authentication environment variables:

```json
{
  "mcpServers": {
    "cds": {
      "command": "uvx",
      "args": ["cds-mcp"]
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

To include authentication, add the CERN credentials before the `--`:

```bash
# Example: Global installation with CERN SSO authentication
claude mcp add --scope user -e CERN_CLIENT_ID=your_client_id -e CERN_CLIENT_SECRET=your_client_secret cds-mcp -- uvx cds-mcp
```

Manual Configuration — you can also manually edit your global config at `~/.claude.json` (on Linux/macOS) or `%APPDATA%\Claude\claude.json` (on Windows):

```json
{
  "mcpServers": {
    "cds": {
      "command": "uvx",
      "args": ["cds-mcp"],
      "env": {
        "CERN_CLIENT_ID": "your_client_id",
        "CERN_CLIENT_SECRET": "your_client_secret"
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
          "CERN_CLIENT_ID": "your_client_id",
          "CERN_CLIENT_SECRET": "your_client_secret"
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
        "CERN_CLIENT_ID": "your_client_id",
        "CERN_CLIENT_SECRET": "your_client_secret"
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
        "CERN_CLIENT_ID": "your_client_id",
        "CERN_CLIENT_SECRET": "your_client_secret"
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

# With CERN SSO authentication
CERN_CLIENT_ID=your_client_id CERN_CLIENT_SECRET=your_client_secret uvx cds-mcp
```


## Authentication & Access Control

### CERN SSO Authentication (Recommended)

The CDS MCP server now supports **proper CERN SSO authentication** using OAuth2/OIDC for accessing restricted content.

#### Setup Instructions

1. **Register your application** in the [CERN Application Portal](https://application-portal.web.cern.ch):
   - Create a new OIDC application
   - Select "Confidential Client" type
   - Note your `Client ID` and `Client Secret`

2. **Configure authentication** by setting environment variables:
   ```bash
   export CERN_CLIENT_ID="your-client-id"
   export CERN_CLIENT_SECRET="your-client-secret"
   ```

3. **Use with MCP clients** - the server will automatically handle token acquisition and refresh.

#### Supported Access Levels

- **Public Records**: Available without authentication
- **Restricted Collections**: Requires CERN SSO authentication and appropriate experiment membership
  - **ATLAS**: Internal Notes, Communications, Conference Slides
  - **CMS**: Internal Notes, Analysis Notes
  - **LHCb**: Internal Notes, Analysis Notes
  - **ALICE**: Internal Notes, Analysis Notes

## Tools

1. **`search_cds_documents`** — Search CDS with various filters
2. **`get_cds_document_details`** — Get detailed information about a specific document
3. **`get_cds_document_files`** — Get file information and download URLs
4. **`get_cds_experiments`** — List available CERN experiments for filtering
5. **`get_cds_document_types`** — List available document types for filtering

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
