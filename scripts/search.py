#!/usr/bin/env python3
"""
SkillsMP Search CLI - Search the SkillsMP marketplace for AI agent skills.

Zero dependencies! Works with Python 3.8+ standard library only.

Usage:
    python search.py search "query" [--sort stars|recent] [--limit N] [--page N] [--category CAT] [--occupation OCC] [--json]
    python search.py search "query" -b  # Bilingual search (Chinese + English)
    python search.py search "query" --ai  # Keyword + AI concurrent search
    python search.py ai-search "query" [--json]
    python search.py info
    python search.py config

Configuration:
    Environment variable (recommended):
        export SKILLSMP_API_KEY=sk_live_xxxxx

    Or config file (~/.skillsmp/config.yaml):
        api_key: sk_live_xxxxx
        default_limit: 20
        default_sort: recent

    Or hermes config.yaml (if using hermes agent):
        skills.config.skillsmp.api_key: sk_live_xxxxx

Priority: Environment Variable > ~/.skillsmp/config.yaml > hermes config.yaml

Get API key: https://skillsmp.com/docs/api
"""

import sys
import json
import argparse
import os
import re
import threading
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

# ANSI colors for terminal output
BOLD  = "\033[1m"
CYAN  = "\033[36m"
GREEN = "\033[32m"
GRAY  = "\033[90m"
RED   = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

# Constants
MAX_DESC_LENGTH = 120
API_TIMEOUT = 10
MAX_LIMIT = 100
LOW_QUOTA_THRESHOLD = 10

# Common Chinese -> English keyword mappings for skill search
CN_TO_EN = {
    "认证": "authentication", "鉴权": "authorization", "登录": "login",
    "授权": "authorization", "安全": "security", "加密": "encryption",
    "密码": "password", "令牌": "token", "会话": "session",
    "前端": "frontend", "后端": "backend", "测试": "testing",
    "部署": "deployment", "监控": "monitoring", "搜索": "search",
    "爬虫": "scraping", "数据": "data", "文档": "documentation",
    "代码审查": "code review", "重构": "refactoring", "调试": "debugging",
    "性能": "performance", "优化": "optimization", "数据库": "database",
    "缓存": "cache", "日志": "logging", "配置": "config",
    "模板": "template", "生成器": "generator", "分析": "analysis",
    "可视化": "visualization", "图像": "image", "视频": "video",
    "音频": "audio", "翻译": "translation", "摘要": "summary",
    "工作流": "workflow", "自动化": "automation", "集成": "integration",
    "微服务": "microservice", "容器": "docker", "云": "cloud",
    "机器学习": "machine learning", "深度学习": "deep learning",
    "人工智能": "AI", "自然语言": "NLP", "语音": "speech",
    "聊天": "chat", "机器人": "bot", "代理": "agent",
}

# Optional yaml support (zero-config works without it)
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

BASE_URL = "https://skillsmp.com/api/v1"
CONFIG_PATH = os.path.expanduser("~/.skillsmp/config.yaml")
HERMES_CONFIG_PATH = os.path.expanduser("~/.hermes/config.yaml")


def load_config():
    """Load skillsmp config from multiple sources (priority: env > ~/.skillsmp > hermes)."""
    config = {
        "api_key": "",
        "default_limit": 20,
        "default_sort": "recent"
    }

    # Try loading from hermes config.yaml (lowest priority)
    if HAS_YAML and os.path.exists(HERMES_CONFIG_PATH):
        try:
            with open(HERMES_CONFIG_PATH, 'r') as f:
                full_config = yaml.safe_load(f) or {}

            skills_config = full_config.get("skills", {}).get("config", {}).get("skillsmp", {})

            if skills_config.get("api_key"):
                config["api_key"] = skills_config["api_key"]
            if skills_config.get("default_limit"):
                config["default_limit"] = int(skills_config["default_limit"])
            if skills_config.get("default_sort"):
                config["default_sort"] = skills_config["default_sort"]
        except Exception as e:
            print(f"{GRAY}Warning: Failed to load hermes config: {e}{RESET}", file=sys.stderr)

    # Try loading from ~/.skillsmp/config.yaml (medium priority)
    if HAS_YAML and os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                skillsmp_config = yaml.safe_load(f) or {}

            if skillsmp_config.get("api_key"):
                config["api_key"] = skillsmp_config["api_key"]
            if skillsmp_config.get("default_limit"):
                config["default_limit"] = int(skillsmp_config["default_limit"])
            if skillsmp_config.get("default_sort"):
                config["default_sort"] = skillsmp_config["default_sort"]
        except Exception as e:
            print(f"{GRAY}Warning: Failed to load config file: {e}{RESET}", file=sys.stderr)

    # Environment variable overrides config files (highest priority)
    env_key = os.environ.get("SKILLSMP_API_KEY")
    if env_key:
        config["api_key"] = env_key

    return config


def api_request(endpoint, params=None, api_key=""):
    """Make API request using standard library only."""
    url = f"{BASE_URL}{endpoint}"
    if params:
        url = f"{url}?{urlencode(params)}"

    headers = {
        "User-Agent": "skillsmp-find/1.0",
        "Accept": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = Request(url, headers=headers)

    try:
        with urlopen(req, timeout=API_TIMEOUT) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)

            # Extract rate limits from headers
            rate_limits = {
                "daily_limit": response.headers.get("x-ratelimit-daily-limit"),
                "daily_remaining": response.headers.get("x-ratelimit-daily-remaining"),
                "minute_limit": response.headers.get("x-ratelimit-minute-limit"),
                "minute_remaining": response.headers.get("x-ratelimit-minute-remaining"),
            }

            # API returns {"success": true, "data": {...}} structure
            # We keep the full response structure for consistency
            return {"success": True, "data": data, "rate_limits": rate_limits}

    except HTTPError as e:
        try:
            error_body = e.read().decode("utf-8")
            error_data = json.loads(error_body)
            if "error" in error_data:
                error = error_data["error"]
                code = error.get("code", "UNKNOWN")
                message = error.get("message", "Unknown error")

                error_messages = {
                    "MISSING_API_KEY": "API key required. Set via:\n  export SKILLSMP_API_KEY=sk_live_xxxxx\n  Or get one at https://skillsmp.com/docs/api",
                    "INVALID_API_KEY": "Invalid API key. Check your config:\n  python search.py config",
                    "MISSING_QUERY": "Search query is required.",
                    "DAILY_QUOTA_EXCEEDED": "Daily quota exceeded. Try again tomorrow or add an API key.",
                    "INTERNAL_ERROR": "Server error. Try again later.",
                }

                friendly_msg = error_messages.get(code, message)
                return {"success": False, "code": code, "message": friendly_msg}
        except Exception:
            pass

        return {
            "success": False,
            "code": f"HTTP_{e.code}",
            "message": f"HTTP {e.code}: {e.reason}"
        }

    except URLError as e:
        return {"success": False, "message": f"Network error: {e.reason}"}

    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def search_skills(query, page=1, limit=20, sort_by="recent", category=None, occupation=None, api_key="", bilingual=False, with_ai=False):
    """Search skills by keyword. 
    - bilingual: search both Chinese and English
    - with_ai: concurrent keyword + AI search (like OpenDCAI)
    """

    def do_keyword_search(q):
        """Keyword search via API."""
        params = {"q": q, "page": page, "limit": limit, "sortBy": sort_by}
        if category:
            params["category"] = category
        if occupation:
            params["occupation"] = occupation
        return api_request("/skills/search", params, api_key)

    def do_ai_search(q):
        """AI semantic search via API."""
        return api_request("/skills/ai-search", {"q": q}, api_key)

    def translate_cn_to_en(query):
        """Translate Chinese query to English for better results."""
        has_chinese = bool(re.search(r"[\u4e00-\u9fff]", query))
        if not has_chinese:
            return query

        english_parts = []
        remaining = query

        for cn, en in sorted(CN_TO_EN.items(), key=lambda x: -len(x[0])):
            if cn in remaining:
                english_parts.append(en)
                remaining = remaining.replace(cn, " ")

        for word in remaining.split():
            word = word.strip()
            if word and not re.search(r"[\u4e00-\u9fff]", word):
                english_parts.append(word)

        return " ".join(english_parts) if english_parts else query

    # Determine search queries
    queries = [query]
    has_chinese = bool(re.search(r"[\u4e00-\u9fff]", query))

    # Warn about silent fallbacks
    if with_ai and not api_key:
        print(f"{YELLOW}⚠️  --ai requires API key, falling back to keyword only{RESET}", file=sys.stderr)

    if bilingual and has_chinese:
        en_query = translate_cn_to_en(query)
        if en_query != query:
            queries.append(en_query)
        else:
            print(f"{YELLOW}⚠️  Could not translate Chinese keywords, using original query{RESET}", file=sys.stderr)

    # Concurrent search
    results = {
        "kw": {},      # keyword search results
        "ai": {},      # AI search results
        "cn": {},      # Chinese keyword results
        "en": {},      # English keyword results
    }

    def search_kw(q, key):
        """Keyword search for a specific query."""
        results[key] = do_keyword_search(q)

    threads = []

    # Keyword searches
    for i, q in enumerate(queries):
        key = "kw" if i == 0 else "en"
        if i == 0 and has_chinese:
            key = "cn"
        t = threading.Thread(target=search_kw, args=(q, key))
        threads.append(t)

    # AI search (if enabled and has API key)
    if with_ai and api_key:
        def search_ai():
            results["ai"] = do_ai_search(query)
        t = threading.Thread(target=search_ai)
        threads.append(t)

    # Start all threads
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Merge results
    merged_skills = {}
    source_tags = {}

    # Process keyword results
    for source_key in ["kw", "cn", "en"]:
        result = results.get(source_key, {})
        if result.get("success"):
            outer = result.get("data", {})
            inner = outer.get("data", {})
            for s in inner.get("skills", []):
                sid = s.get("id")
                if sid:
                    if sid not in merged_skills:
                        merged_skills[sid] = s
                        source_tags[sid] = source_key
                    else:
                        # Mark as found in multiple sources
                        existing = source_tags[sid]
                        if existing != source_key:
                            source_tags[sid] = f"{existing}+{source_key}"

    # Process AI results
    ai_result = results.get("ai", {})
    if ai_result.get("success"):
        outer = ai_result.get("data", {})
        inner = outer.get("data", {})
        ai_skills = inner.get("data", [])
        for item in ai_skills:
            s = item.get("skill", item)
            sid = s.get("id")
            if sid:
                if sid not in merged_skills:
                    merged_skills[sid] = s
                    source_tags[sid] = "ai"
                else:
                    existing = source_tags[sid]
                    if "ai" not in existing:
                        source_tags[sid] = f"{existing}+ai"

    # Check if any search succeeded
    any_success = any(
        results.get(k, {}).get("success") 
        for k in ["kw", "cn", "en", "ai"]
    )

    if not any_success:
        # Return first error
        for k in ["kw", "cn", "en", "ai"]:
            if results.get(k):
                return results[k]
        return {"success": False, "message": "All searches failed"}

    # Sort by stars
    sorted_skills = sorted(merged_skills.values(), key=lambda x: -x.get("stars", 0))

    # Build result
    result = {
        "success": True,
        "data": {
            "success": True,
            "data": {
                "skills": sorted_skills[:limit],
                "pagination": {
                    "page": 1,
                    "limit": limit,
                    "total": len(sorted_skills),
                    "totalPages": 1,
                    "hasNext": False,
                    "hasPrev": False,
                }
            }
        },
        "rate_limits": results.get("kw", results.get("cn", {})).get("rate_limits", {}),
        "_source_tags": source_tags,
        "_queries": queries,
        "_has_ai": with_ai and api_key,
    }

    return result


def ai_search(query, api_key=""):
    """AI semantic search (requires API key)."""
    return api_request("/skills/ai-search", {"q": query}, api_key)


def format_skill(skill, index=None, verbose=False, source_tag=None):
    """Format a skill for display with colored source tags."""
    prefix = f"[{index}] " if index else ""
    name = skill.get("name", "Unknown")
    author = skill.get("author", "")
    desc = skill.get("description", "No description")
    stars = skill.get("stars", 0)
    github_url = skill.get("githubUrl", "")
    skill_url = skill.get("skillUrl", "")
    updated = skill.get("updatedAt", "")

    # Truncate description
    if len(desc) > MAX_DESC_LENGTH:
        desc = desc[:MAX_DESC_LENGTH - 3] + "..."

    # Source tag with colors (like OpenDCAI)
    tag_str = ""
    if source_tag:
        if source_tag == "kw":
            tag_str = f" {GRAY}[kw]{RESET}"
        elif source_tag == "ai":
            tag_str = f" {CYAN}[ai]{RESET}"
        elif source_tag == "cn":
            tag_str = f" {YELLOW}[cn]{RESET}"
        elif source_tag == "en":
            tag_str = f" {GREEN}[en]{RESET}"
        elif "+" in source_tag:
            # Multiple sources
            tag_str = f" {BOLD}[{source_tag}]{RESET}"

    lines = [
        f"{prefix}{BOLD}★ {stars}{RESET} | {CYAN}{name}{RESET}{tag_str}",
        f"    {GRAY}{desc}{RESET}",
    ]

    if verbose:
        if author:
            lines.append(f"    Author: {author}")
        if github_url:
            lines.append(f"    GitHub: {github_url}")
        if skill_url:
            lines.append(f"    SkillsMP: {skill_url}")
        if updated:
            lines.append(f"    Updated: {updated}")
        # Installation hint
        if github_url:
            lines.append(f"    Install: git clone {github_url} /tmp/skill && cp -r /tmp/skill ~/.claude/skills/")

    return "\n".join(lines)


def format_rate_limits(rate_limits):
    """Format rate limit info."""
    if not rate_limits.get("daily_limit"):
        return ""

    lines = [
        f"\n📊 Rate Limits:",
        f"   Daily: {rate_limits['daily_remaining']}/{rate_limits['daily_limit']} remaining",
        f"   Minute: {rate_limits['minute_remaining']}/{rate_limits['minute_limit']} remaining",
    ]

    remaining = int(rate_limits.get("daily_remaining", 0))
    if remaining < LOW_QUOTA_THRESHOLD:
        lines.append(f"   ⚠️  Low quota! Set API key for 500/day:")
        lines.append(f"   export SKILLSMP_API_KEY=***")

    return "\n".join(lines)


def print_results(data, verbose=False, as_json=False, save_path=None):
    """Print search results with colored output and optional save to JSON."""
    # Save to JSON if requested
    if save_path:
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"{GREEN}✅ Results saved to {save_path}{RESET}")
        except Exception as e:
            print(f"{RED}❌ Failed to save: {e}{RESET}")

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if not data.get("success", True):
        print(f"{RED}❌ Error: {data.get('message', 'Unknown error')}{RESET}")
        if data.get("code"):
            print(f"   Code: {data['code']}")
        return

    outer_data = data.get("data", {})
    skills_data = outer_data.get("data", {})

    if "skills" in skills_data:
        skills = skills_data.get("skills", [])
        pagination = skills_data.get("pagination", {})
    else:
        skills = []
        pagination = {}

    rate_limits = data.get("rate_limits", {})
    source_tags = data.get("_source_tags", {})
    queries = data.get("_queries", [])
    has_ai = data.get("_has_ai", False)

    if not skills:
        print(f"{GRAY}No skills found.{RESET}")
        return

    total = pagination.get("total", len(skills))
    page = pagination.get("page", 1)
    total_pages = pagination.get("totalPages", 1)
    has_next = pagination.get("hasNext", False)

    print(f"\n{'='*60}")

    # Show search info
    if len(queries) > 1:
        print(f"{BOLD}📋 搜索 {' + '.join(queries)} 共 {total} 条{RESET}")
    else:
        print(f"{BOLD}📋 Found {total} skills (page {page}/{total_pages}){RESET}")

    # Show source legend
    sources = set()
    for tag in source_tags.values():
        for s in tag.split("+"):
            sources.add(s)
    legend_parts = []
    if "kw" in sources:
        legend_parts.append(f"{GRAY}[kw]{RESET}=关键词")
    if "cn" in sources:
        legend_parts.append(f"{YELLOW}[cn]{RESET}=中文")
    if "en" in sources:
        legend_parts.append(f"{GREEN}[en]{RESET}=英文")
    if "ai" in sources:
        legend_parts.append(f"{CYAN}[ai]{RESET}=AI")
    if legend_parts:
        print(f"   {' | '.join(legend_parts)}")

    print(f"{'='*60}\n")

    for i, skill in enumerate(skills, 1):
        sid = skill.get("id", "")
        tag = source_tags.get(sid)
        print(format_skill(skill, i, verbose, source_tag=tag))
        print()

    if has_next:
        print(f"💡 More results available. Use --page {page + 1} to see next page.")

    print(format_rate_limits(rate_limits))


def print_info(config):
    """Print API info and rate limits."""
    result = api_request("/skills/search", {"q": "test", "limit": 1}, config["api_key"])

    print("🔍 SkillsMP API Status")
    print("=" * 40)

    if config["api_key"]:
        masked_key = config["api_key"][:8] + "..." + config["api_key"][-4:] if len(config["api_key"]) > 12 else "***"
        print(f"✅ API Key: {masked_key}")
    else:
        print(f"⚠️  API Key: Not set (anonymous)")

    if result.get("success"):
        rate_limits = result.get("rate_limits", {})
        print(f"\n📊 Rate Limits:")
        print(f"   Daily: {rate_limits.get('daily_remaining', '?')}/{rate_limits.get('daily_limit', '?')}")
        print(f"   Minute: {rate_limits.get('minute_remaining', '?')}/{rate_limits.get('minute_limit', '?')}")
    else:
        print(f"\n❌ API Error: {result.get('message', 'Unknown')}")

    print(f"\n⚙️  Config:")
    print(f"   Default limit: {config['default_limit']}")
    print(f"   Default sort: {config['default_sort']}")

    if not config["api_key"]:
        print(f"\n💡 Set API key for:")
        print(f"   - 500 requests/day (vs 50)")
        print(f"   - 30 requests/min (vs 10)")
        print(f"   - AI semantic search access")
        print(f"\\n   export SKILLSMP_API_KEY=***")
        print(f"   Or get key: https://skillsmp.com/docs/api")


def print_config(config):
    """Print current configuration."""
    print("⚙️  SkillsMP Configuration")
    print("=" * 40)

    if config["api_key"]:
        masked_key = config["api_key"][:8] + "..." + config["api_key"][-4:] if len(config["api_key"]) > 12 else "***"
        print(f"API Key: {masked_key}")
    else:
        print(f"API Key: (not set)")

    print(f"Default Limit: {config['default_limit']}")
    print(f"Default Sort: {config['default_sort']}")

    print(f"\n📁 Config Sources (priority: env > file):")
    env_status = 'set' if os.environ.get('SKILLSMP_API_KEY') else 'not set'
    print(f"  1. Environment: SKILLSMP_API_KEY=***")
    print(f"  2. Config file: {CONFIG_PATH} {'✓' if os.path.exists(CONFIG_PATH) else '✗'}")
    print(f"  3. Hermes config: {HERMES_CONFIG_PATH} {'✓' if os.path.exists(HERMES_CONFIG_PATH) else '✗'}")

    print(f"\n📝 Set config:")
    print(f"  Option 1 - Environment variable (recommended):")
    print(f"    export SKILLSMP_API_KEY=***")
    print(f"  Option 2 - Config file (requires PyYAML):")
    print(f"    mkdir -p ~/.skillsmp")
    print(f"    echo 'api_key: sk_live_xxxxx' > {CONFIG_PATH}")
    print(f"  Option 3 - Hermes config (if using hermes agent):")
    print(f"    hermes config set skills.config.skillsmp.api_key YOUR_KEY")


def main():
    config = load_config()

    parser = argparse.ArgumentParser(
        description="Search SkillsMP marketplace for AI agent skills (zero dependencies!)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s search "web scraping"                    # Basic search
  %(prog)s search "teaching" --sort stars --limit 5 # Sort by stars
  %(prog)s search "code review" --page 2            # Next page
  %(prog)s search "automation" --json               # JSON output
  %(prog)s ai-search "browser automation"           # AI search (needs API key)
  %(prog)s info                                     # Check API status
  %(prog)s config                                   # Show configuration

Configuration:
  export SKILLSMP_API_KEY=sk_live_xxxxx             # Set API key (recommended)
  Or get key: https://skillsmp.com/docs/api
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Search command
    search_parser = subparsers.add_parser("search", help="Keyword search")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    search_parser.add_argument("--limit", type=int, default=None, help=f"Results per page (default: {config['default_limit']}, max: {MAX_LIMIT})")
    search_parser.add_argument("--sort", choices=["stars", "recent"], default=None, help=f"Sort order (default: {config['default_sort']})")
    search_parser.add_argument("--category", help="Filter by category slug")
    search_parser.add_argument("--occupation", help="Filter by occupation slug")
    search_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed info with install commands")
    search_parser.add_argument("--json", action="store_true", help="Output raw JSON")
    search_parser.add_argument("--bilingual", "-b", action="store_true", help="Search with both Chinese and English keywords")
    search_parser.add_argument("--ai", action="store_true", help="Concurrent keyword + AI search (needs API key)")
    search_parser.add_argument("--save", metavar="FILE", help="Save results to JSON file")

    # AI search command
    ai_parser = subparsers.add_parser("ai-search", help="AI semantic search (requires API key)")
    ai_parser.add_argument("query", help="Search query")
    ai_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed info")
    ai_parser.add_argument("--json", action="store_true", help="Output raw JSON")
    ai_parser.add_argument("--save", metavar="FILE", help="Save results to JSON file")

    # Info command
    subparsers.add_parser("info", help="Check API status and rate limits")

    # Config command
    subparsers.add_parser("config", help="Show current configuration")

    args = parser.parse_args()

    # Apply defaults from config
    limit = args.limit if hasattr(args, 'limit') and args.limit else config["default_limit"]
    # Validate limit
    if limit < 1:
        print(f"{YELLOW}⚠️  --limit must be >= 1, using default {config['default_limit']}{RESET}", file=sys.stderr)
        limit = config["default_limit"]
    if limit > MAX_LIMIT:
        print(f"{YELLOW}⚠️  --limit {limit} exceeds max {MAX_LIMIT}, using {MAX_LIMIT}{RESET}", file=sys.stderr)
        limit = MAX_LIMIT
    sort = args.sort if hasattr(args, 'sort') and args.sort else config["default_sort"]

    # Validate page
    page = args.page if hasattr(args, 'page') else 1
    if page < 1:
        print(f"{YELLOW}⚠️  --page must be >= 1, using default 1{RESET}", file=sys.stderr)
        page = 1

    if args.command == "search":
        data = search_skills(
            args.query,
            page=page,
            limit=limit,
            sort_by=sort,
            category=args.category,
            occupation=args.occupation,
            api_key=config["api_key"],
            bilingual=args.bilingual,
            with_ai=args.ai
        )
        print_results(data, verbose=args.verbose, as_json=args.json, save_path=args.save)

    elif args.command == "ai-search":
        if not config["api_key"]:
            print("❌ Error: API key required for AI search.")
            print("   Set via: export SKILLSMP_API_KEY=***")
            print("   Or get key: https://skillsmp.com/docs/api")
            sys.exit(1)
        data = ai_search(args.query, api_key=config["api_key"])
        print_results(data, verbose=args.verbose, as_json=args.json, save_path=args.save)

    elif args.command == "info":
        print_info(config)

    elif args.command == "config":
        print_config(config)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
