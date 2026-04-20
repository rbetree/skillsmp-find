# Installation Guide

## Quick Start (For AI Agents)

**Step 1: Detect your platform**

```bash
if [ -d "$HOME/.claude" ]; then echo "Claude Code"; 
elif [ -d "$HOME/.codex" ]; then echo "Codex CLI"; 
elif [ -d "$HOME/.hermes" ]; then echo "Hermes Agent"; 
else echo "Other (use universal path)"; fi
```

**Step 2: Install**

```bash
# Claude Code
git clone https://github.com/rbetree/skillsmp-find.git ~/.claude/skills/skillsmp-find

# Codex CLI
git clone https://github.com/rbetree/skillsmp-find.git ~/.codex/skills/skillsmp-find

# Hermes Agent
git clone https://github.com/rbetree/skillsmp-find.git ~/.hermes/skills/research/skillsmp-find

# Universal (Gemini CLI, Kiro, Antigravity, others)
git clone https://github.com/rbetree/skillsmp-find.git ~/.agents/skills/skillsmp-find
```

**Step 3: Tell the user**

```
✅ 已安装 skillsmp-find

使用方法：
- 输入 /skillsmp-find 或直接描述你想搜索的内容
- 例如："帮我找一个代码审查的 skill"
```

---

## One-Click Install (Interactive Menu)

```bash
curl -sSL https://raw.githubusercontent.com/rbetree/skillsmp-find/main/install.sh | bash
```

Or specify directly:

```bash
./install.sh --claude-code
./install.sh --codex --hermes
./install.sh --all
```

---

## Manual Install by Platform

### Claude Code

Global (available in all projects):
```bash
git clone https://github.com/rbetree/skillsmp-find.git ~/.claude/skills/skillsmp-find
```

Project-level (current project only):
```bash
cd $(git rev-parse --show-toplevel)
mkdir -p .claude/skills
git clone https://github.com/rbetree/skillsmp-find.git .claude/skills/skillsmp-find
```

### Codex CLI
```bash
git clone https://github.com/rbetree/skillsmp-find.git ~/.codex/skills/skillsmp-find
```

### Hermes Agent
```bash
git clone https://github.com/rbetree/skillsmp-find.git ~/.hermes/skills/research/skillsmp-find
```

### Universal Path
Works for Gemini CLI, Kiro, Antigravity, and other agents:
```bash
git clone https://github.com/rbetree/skillsmp-find.git ~/.agents/skills/skillsmp-find
```

### OpenClaw
```bash
git clone https://github.com/rbetree/skillsmp-find.git ~/.openclaw/workspace/skills/skillsmp-find
```

---

## Configuration

### Option 1: Environment Variable (Recommended)
```bash
export SKILLSMP_API_KEY=***
```

### Option 2: Config File
```bash
mkdir -p ~/.skillsmp
cat > ~/.skillsmp/config.yaml << EOF
api_key: ***
default_limit: 20
default_sort: recent
EOF
```

### Option 3: Hermes Config
```bash
hermes config set skills.config.skillsmp.api_key ***
```

**Priority order:**
1. Environment variable `SKILLSMP_API_KEY` (highest)
2. Config file `~/.skillsmp/config.yaml`
3. Hermes config `~/.hermes/config.yaml`

### Get API Key

1. Visit https://skillsmp.com/docs/api
2. Sign up for an account
3. Generate an API key

**Rate Limits:**
- Anonymous: 50 requests/day, 10 requests/min
- With API key: 500 requests/day, 30 requests/min

---

## Dependencies

**None.** This tool uses Python 3.8+ standard library only.

Optional:
- `pyyaml` — enables `~/.skillsmp/config.yaml` config file support

---

## Troubleshooting

### "command not found: python"
Try `python3` instead of `python`:
```bash
python3 scripts/search.py search "web scraping"
```

### "No module named '_ssl'" or SSL errors
Use the system Python:
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
