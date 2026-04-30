#!/usr/bin/env bash
set -e

REPO_URL="https://github.com/rbetree/skillsmp-find.git"
SKILL_NAME="skillsmp-find"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

install_to() {
    local target="$1"
    local label="$2"

    if [ -d "$target" ]; then
        warn "$label already exists at $target, pulling latest..."
        git -C "$target" pull --quiet 2>/dev/null || warn "Pull failed, skipping."
    else
        mkdir -p "$(dirname "$target")"
        git clone --quiet "$REPO_URL" "$target"
    fi
    ok "$label installed to $target"
}

install_claude_code_global() {
    install_to "$HOME/.claude/skills/$SKILL_NAME" "Claude Code (global)"
}

install_claude_code_project() {
    install_to ".claude/skills/$SKILL_NAME" "Claude Code (project)"
}

install_codex() {
    install_to "$HOME/.codex/skills/$SKILL_NAME" "Codex CLI"
}

install_hermes() {
    install_to "$HOME/.hermes/skills/research/$SKILL_NAME" "Hermes Agent"
}

install_agents() {
    install_to "$HOME/.agents/skills/$SKILL_NAME" "Agent shared directory"
}

install_openclaw() {
    install_to "$HOME/.openclaw/workspace/skills/$SKILL_NAME" "OpenClaw"
}

install_all() {
    install_claude_code_global
    install_codex
    install_hermes
    install_agents
    install_openclaw
    echo ""
    info "Note: Claude Code (project) requires running this script"
    info "inside your project directory with --claude-code --project."
}

show_help() {
    cat << 'EOF'
SkillsMP Find Installer

Usage: install.sh [OPTIONS]

Options:
  --claude-code         Install for Claude Code (global)
  --claude-code --project  Install for Claude Code (project-level)
  --codex               Install for Codex CLI
  --hermes              Install for Hermes Agent
  --agents              Install to shared agent directory (~/.agents/skills/)
  --openclaw            Install for OpenClaw
  --all                 Install for all global platforms
  -h, --help            Show this help

Examples:
  ./install.sh --claude-code
  ./install.sh --claude-code --project
  ./install.sh --codex --hermes
  ./install.sh --all
  curl -sSL https://raw.githubusercontent.com/rbetree/skillsmp-find/main/install.sh | bash

EOF
}

interactive_menu() {
    echo ""
    echo -e "${CYAN}SkillsMP Find Installer${NC}"
    echo "=============================="
    echo ""
    echo "Select platforms to install:"
    echo ""
    echo "  1) Claude Code (global)      ~/.claude/skills/"
    echo "  2) Claude Code (project)     .claude/skills/"
    echo "  3) Codex CLI                 ~/.codex/skills/"
    echo "  4) Hermes Agent              ~/.hermes/skills/research/"
    echo "  5) Agent shared directory    ~/.agents/skills/"
    echo "  6) OpenClaw                  ~/.openclaw/workspace/skills/"
    echo "  7) All global platforms"
    echo "  0) Exit"
    echo ""
    read -rp "Enter choices (e.g. 1 3 5, or 7 for all): " choices

    for c in $choices; do
        case $c in
            1) install_claude_code_global ;;
            2) install_claude_code_project ;;
            3) install_codex ;;
            4) install_hermes ;;
            5) install_agents ;;
            6) install_openclaw ;;
            7) install_all ;;
            0) echo "Bye."; exit 0 ;;
            *) warn "Unknown option: $c" ;;
        esac
    done
}

# Parse arguments
if [ $# -eq 0 ]; then
    interactive_menu
    exit 0
fi

PROJECT_MODE=false
INSTALL_CLAUDE_CODE=false
INSTALL_CODEX=false
INSTALL_HERMES=false
INSTALL_AGENTS=false
INSTALL_OPENCLAW=false
INSTALL_ALL=false

while [ $# -gt 0 ]; do
    case "$1" in
        --claude-code)
            INSTALL_CLAUDE_CODE=true
            ;;
        --project)
            PROJECT_MODE=true
            ;;
        --codex)
            INSTALL_CODEX=true
            ;;
        --hermes)
            INSTALL_HERMES=true
            ;;
        --agents)
            INSTALL_AGENTS=true
            ;;
        --openclaw)
            INSTALL_OPENCLAW=true
            ;;
        --all)
            INSTALL_ALL=true
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            err "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
    shift
done

if [ "$INSTALL_ALL" = true ] && [ "$PROJECT_MODE" = true ]; then
    err "--project can only be used with --claude-code"
    exit 1
fi

if [ "$INSTALL_ALL" = false ] &&
   [ "$INSTALL_CLAUDE_CODE" = false ] &&
   [ "$INSTALL_CODEX" = false ] &&
   [ "$INSTALL_HERMES" = false ] &&
   [ "$INSTALL_AGENTS" = false ] &&
   [ "$INSTALL_OPENCLAW" = false ]; then
    err "No install target selected."
    show_help
    exit 1
fi

if [ "$INSTALL_ALL" = true ]; then
    install_all
else
    if [ "$INSTALL_CLAUDE_CODE" = true ]; then
        if [ "$PROJECT_MODE" = true ]; then
            install_claude_code_project
        else
            install_claude_code_global
        fi
    fi
    [ "$INSTALL_CODEX" = true ] && install_codex
    [ "$INSTALL_HERMES" = true ] && install_hermes
    [ "$INSTALL_AGENTS" = true ] && install_agents
    [ "$INSTALL_OPENCLAW" = true ] && install_openclaw
fi

echo ""
ok "Done!"
