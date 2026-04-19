# Installation Guide

## One-Click Install (Recommended)

```bash
curl -sSL https://raw.githubusercontent.com/rbetree/skillsmp-find/main/install.sh | bash
```

This will show an interactive menu to select your platforms.

Or specify platforms directly:

```bash
# Clone the installer
git clone --depth 1 https://github.com/rbetree/skillsmp-find.git /tmp/skillsmp-find
cd /tmp/skillsmp-find

# Install for specific platforms
./install.sh --claude-code
./install.sh --codex --hermes
./install.sh --all
```

## Choose Your Platform

### Claude Code

#### Global (available in all projects)

```bash
git clone https://github.com/rbetree/skillsmp-find.git ~/.claude/skills/skillsmp-find
```

#### Project-level (current project only)

```bash
cd $(git rev-parse --show-toplevel)
mkdir -p .claude/skills
git clone https://github.com/rbetree/skillsmp-find.git .claude/skills/skillsmp-find
```

Then in Claude Code, type `/skillsmp-find` or describe what you want to search.

### Codex CLI

```bash
git clone https://github.com/rbetree/skillsmp-find.git ~/.codex/skills/skillsmp-find
```

### Hermes Agent

```bash
git clone https://github.com/rbetree/skillsmp-find.git ~/.hermes/skills/research/skillsmp-find
```

### Agent Shared Directory

Shared directory recognized by multiple agents:

```bash
git clone https://github.com/rbetree/skillsmp-find.git ~/.agents/skills/skillsmp-find
```

### OpenClaw

```bash
git clone https://github.com/rbetree/skillsmp-find.git ~/.openclaw/workspace/skills/skillsmp-find
```

### Cursor

Project-level installation:

```bash
cd $(git rev-parse --show-toplevel)
mkdir -p .cursor/skills
git clone https://github.com/rbetree/skillsmp-find.git .cursor/skills/skillsmp-find
```

## Standalone CLI (No Agent Required)

```bash
git clone https://github.com/rbetree/skillsmp-find.git
cd skillsmp-find
python scripts/search.py search "web scraping"
```

Add to PATH for convenience:

```bash
echo 'alias skillsmp="python /path/to/skillsmp-find/scripts/search.py"' >> ~/.bashrc
source ~/.bashrc
skillsmp search "web scraping"
```

## Configuration

### Option 1: Environment Variable (Recommended)

```bash
export SKILLSMP_API_KEY=***
```

Add to `~/.bashrc` or `~/.zshrc` to persist.

### Option 2: Config File

```bash
mkdir -p ~/.skillsmp
cat > ~/.skillsmp/config.yaml << EOF
api_key: ***
default_limit: 20
default_sort: recent
EOF
```

Requires `pyyaml`: `pip3 install pyyaml`

### Option 3: Hermes Config

```bash
hermes config set skills.config.skillsmp.api_key ***
```

### Get API Key

1. Visit https://skillsmp.com/docs/api
2. Sign up for an account
3. Generate an API key

**Rate Limits:**
- Anonymous: 50 requests/day, 10 requests/min
- With API key: 500 requests/day, 30 requests/min

## Dependencies

**None.** This tool uses Python 3.8+ standard library only.

Optional:
- `pyyaml` — enables `~/.skillsmp/config.yaml` config file support

## Troubleshooting

### "command not found: python"

Try `python3` instead of `python`:

```bash
python3 scripts/search.py search "web scraping"
```

### "No module named '_ssl'" or SSL errors

Your Python may be compiled without SSL support. Use the system Python:

```bash
/usr/bin/python3 scripts/search.py search "web scraping"
```

### Permission denied on install.sh

```bash
chmod +x install.sh
./install.sh --claude-code
```

### API key not working

Check your configuration:

```bash
python scripts/search.py config
python scripts/search.py info
```

## Platform Path Reference

| Platform | Path |
|----------|------|
| Claude Code (global) | `~/.claude/skills/skillsmp-find/` |
| Claude Code (project) | `.claude/skills/skillsmp-find/` |
| Codex CLI | `~/.codex/skills/skillsmp-find/` |
| Hermes Agent | `~/.hermes/skills/research/skillsmp-find/` |
| Agent shared | `~/.agents/skills/skillsmp-find/` |
| OpenClaw | `~/.openclaw/workspace/skills/skillsmp-find/` |
| Cursor | `.cursor/skills/skillsmp-find/` |
