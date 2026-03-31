# CDS MCP Server

A Model Context Protocol (MCP) server for integrating with CERN Document Server (CDS), built on the Invenio digital library framework.

## Features

- **Search CDS documents** with filters for experiments, document types, and date ranges
- **Get detailed document information** including full abstracts, authors, and metadata
- **Access document files** with download URLs and file metadata
- **Browse experiments and document types** for better search filtering
- **Clean, reusable architecture** that can be extended for other CERN services

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

Manual Configuration — you can also manually edit your global config at `~/.claude.json` (on Linux/macOS) or `%APPDATA%\Claude\claude.json` (on Windows):

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

### GitHub Copilot

Add to your VS Code `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "cds": {
        "command": "uvx",
        "args": ["cds-mcp"],
        "env": {}
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
      "env": {}
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
      "env": {}
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
```

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
