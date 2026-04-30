#!/usr/bin/env python3
"""
SkillsMP Search CLI - Search the SkillsMP marketplace for AI agent skills.

Zero dependencies! Works with Python 3.8+ standard library only.

Usage:
    python search.py search "query" [--sort stars|recent] [--limit N] [--page N] [--category CAT] [--occupation OCC] [--json]
    python search.py search "query" -b "english keyword"  # Bilingual: Chinese + English in parallel
    python search.py search "query" --ai  # Keyword + AI concurrent search
    python search.py ai-search "query" [--json]
    python search.py analyze [path] [--recommend N]  # Analyze project & recommend skills
    python search.py info
    python search.py config

Configuration:
    Environment variable (recommended):
        export SKILLSMP_API_KEY=sk_live_xxxxx

    Or repository .env file:
        SKILLSMP_API_KEY=sk_live_xxxxx

    Or config file (~/.skillsmp/config.yaml):
        api_key: sk_live_xxxxx
        default_limit: 20
        default_sort: recent

    Or hermes config.yaml (if using hermes agent):
        skills.config.skillsmp.api_key: sk_live_xxxxx

Priority: Environment Variable > repository .env > ~/.skillsmp/config.yaml > hermes config.yaml

Get API key: https://skillsmp.com/docs/api
"""

from __future__ import annotations

import json
import argparse
import os
import re
import sys
import threading
import time
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# ANSI colors for terminal output
BOLD  = "\033[1m"
CYAN  = "\033[36m"
GREEN = "\033[32m"
GRAY  = "\033[90m"
RED   = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

# Constants
VERSION = "1.1.0"
MAX_DESC_LENGTH = 120
API_TIMEOUT = 10
MAX_LIMIT = 100
LOW_QUOTA_THRESHOLD = 10

# Optional yaml support (zero-config works without it)
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

BASE_URL = "https://skillsmp.com/api/v1"
CONFIG_PATH = os.path.expanduser("~/.skillsmp/config.yaml")
HERMES_CONFIG_PATH = os.path.expanduser("~/.hermes/config.yaml")
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOTENV_PATH = os.path.join(REPO_ROOT, ".env")


def _strip_wrapped_quotes(value: str) -> str:
    """去除 .env 值两端成对包裹的引号。"""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def load_dotenv(dotenv_path: Optional[str] = None, override: bool = False) -> bool:
    """从仓库根目录加载 .env，默认不覆盖现有环境变量。"""
    dotenv_path = dotenv_path or DOTENV_PATH
    if not os.path.exists(dotenv_path):
        return False

    try:
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.startswith("export "):
                    line = line[7:].strip()

                if "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                if not key:
                    continue

                value = _strip_wrapped_quotes(value.strip())
                if override or key not in os.environ:
                    os.environ[key] = value
        return True
    except OSError as e:
        print(f"{GRAY}Warning: Failed to load .env file: {e}{RESET}", file=sys.stderr)
        return False


def load_config() -> Dict[str, Any]:
    """Load skillsmp config from multiple sources (priority: env/.env > ~/.skillsmp > hermes)."""
    config = {
        "api_key": "",
        "default_limit": 20,
        "default_sort": "recent"
    }

    # 从仓库根目录加载 .env，但不覆盖外部环境变量。
    load_dotenv()
    
    # Helper function to check file permissions
    def check_file_permissions(filepath: str) -> bool:
        """Check if file has secure permissions (not world-readable)."""
        try:
            if not os.path.exists(filepath):
                return True
            
            stat_info = os.stat(filepath)
            # Check if file is world-readable (other read permission)
            if stat_info.st_mode & 0o004:
                print(f"{YELLOW}⚠️  Config file {filepath} has loose permissions (world-readable){RESET}", file=sys.stderr)
                print(f"{GRAY}   Consider: chmod 600 {filepath}{RESET}", file=sys.stderr)
                return False
            return True
        except OSError:
            return True
    
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
            # Check file permissions before loading
            check_file_permissions(CONFIG_PATH)
            
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


def api_request(endpoint: str, params: Optional[Dict[str, str]] = None, api_key: str = "", max_retries: int = 3) -> Dict[str, Any]:
    """Make API request using standard library only with retry mechanism."""
    url = f"{BASE_URL}{endpoint}"
    if params:
        url = f"{url}?{urlencode(params)}"
    
    headers = {
        "User-Agent": f"skillsmp-find/{VERSION}",
        "Accept": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    req = Request(url, headers=headers)
    
    # Retry logic
    last_error = None
    for attempt in range(max_retries):
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
                        "MISSING_API_KEY": "API key required. Set via:\n  export SKILLSMP_API_KEY=***  Or get one at https://skillsmp.com/docs/api",
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
            last_error = f"Network error: {e.reason}"
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            return {"success": False, "message": last_error}
        
        except Exception as e:
            last_error = f"Error: {str(e)}"
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"success": False, "message": last_error}
    
    return {"success": False, "message": f"Failed after {max_retries} attempts: {last_error}"}


def search_skills(query: str, page: int = 1, limit: int = 20, sort_by: str = "recent",
                  category: Optional[str] = None, occupation: Optional[str] = None,
                  api_key: str = "", bilingual_query: Optional[str] = None,
                  with_ai: bool = False) -> Dict[str, Any]:
    """Search skills by keyword.
    - bilingual_query: pre-translated English query to search in parallel with the original
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

    # Determine search queries
    queries = [query]
    has_chinese = bool(re.search(r"[\u4e00-\u9fff]", query))

    # Warn about silent fallbacks
    if with_ai and not api_key:
        print(f"{YELLOW}⚠️  --ai requires API key, falling back to keyword only{RESET}", file=sys.stderr)

    # Bilingual: add pre-translated query if provided
    if bilingual_query:
        queries.append(bilingual_query)

    is_single_keyword_search = len(queries) == 1 and not (with_ai and api_key)

    # Concurrent search
    results = {
        "kw": {},      # keyword search results
        "ai": {},      # AI search results
        "cn": {},      # Chinese keyword results
        "en": {},      # English keyword results
    }
    results_lock = threading.Lock()  # Protect concurrent writes to results

    def search_kw(q, key):
        """Keyword search for a specific query."""
        result = do_keyword_search(q)
        with results_lock:
            results[key] = result

    threads = []
    query_keys = []  # Track (key, query) pairs for merge phase

    # Keyword searches — use unique keys to avoid overwrite
    for i, q in enumerate(queries):
        if i == 0:
            key = "cn" if has_chinese else "kw"
        else:
            key = "cn" if re.search(r"[\u4e00-\u9fff]", q) else "en"
        # Ensure unique key if same language appears twice
        unique_key = key if key not in [k for k, _ in query_keys] else f"{key}{i}"
        query_keys.append((unique_key, q))
        t = threading.Thread(target=search_kw, args=(q, unique_key))
        threads.append(t)

    # AI search (if enabled and has API key)
    if with_ai and api_key:
        def search_ai():
            result = do_ai_search(query)
            with results_lock:
                results["ai"] = result
        t = threading.Thread(target=search_ai)
        threads.append(t)

    # Start all threads
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if is_single_keyword_search:
        source_key = "cn" if has_chinese else "kw"
        result = results.get(source_key, {})
        if result.get("success"):
            outer = result.get("data", {})
            inner = outer.get("data", {})
            source_tags = {
                s.get("id"): source_key
                for s in inner.get("skills", [])
                if s.get("id")
            }
            result["_source_tags"] = source_tags
            result["_queries"] = queries
            result["_has_ai"] = False
        return result

    # Merge results
    merged_skills = {}
    source_tags = {}

    # Normalize source key (e.g. "cn1" -> "cn", "en2" -> "en")
    def _normalize_source_key(k):
        if k.startswith("cn"):
            return "cn"
        if k.startswith("en"):
            return "en"
        if k.startswith("kw"):
            return "kw"
        return k

    # Process keyword results — iterate all query result keys
    for raw_key in results:
        if raw_key == "ai":
            continue  # AI results handled separately
        result = results.get(raw_key, {})
        source_key = _normalize_source_key(raw_key)
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
                        if source_key not in existing.split("+"):
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
        for k in results
    )

    if not any_success:
        # Collect all error messages
        error_messages = []
        error_codes = []
        for k in results:
            if results.get(k):
                error = results[k]
                if error.get("message"):
                    error_messages.append(f"{k}: {error['message']}")
                if error.get("code"):
                    error_codes.append(f"{k}: {error['code']}")
        
        if error_messages:
            # Return first error but include summary of all errors
            first_error = next((results[k] for k in results if results.get(k)), None)
            if first_error:
                # Add error summary to the message
                summary = f" (Total {len(error_messages)} errors: {', '.join(error_codes[:3])}{'...' if len(error_codes) > 3 else ''})"
                if "message" in first_error:
                    first_error["message"] += summary
                return first_error
        
        return {"success": False, "message": f"All {len(results)} searches failed"}

    # Sort merged local results by stars. Pagination now describes the merged page,
    # not SkillsMP's upstream pagination for any single query.
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
                    "mode": "merged",
                }
            }
        },
        # Extract rate_limits from first successful keyword result
        "rate_limits": next(
            (r.get("rate_limits", {}) for r in results.values()
             if r != results.get("ai") and r.get("success") and r.get("rate_limits")),
            {}
        ),
        "_source_tags": source_tags,
        "_queries": queries,
        "_has_ai": with_ai and api_key,
    }

    return result


def ai_search(query: str, api_key: str = "") -> Dict[str, Any]:
    """AI semantic search (requires API key)."""
    return api_request("/skills/ai-search", {"q": query}, api_key)


def format_skill(skill: Dict[str, Any], index: Optional[int] = None,
                 verbose: bool = False, source_tag: Optional[str] = None) -> str:
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
        if skill_url:
            lines.append(f"    Install: see {skill_url} for details")

    return "\n".join(lines)


def format_rate_limits(rate_limits: Dict[str, str]) -> str:
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
        print(f"\n   export SKILLSMP_API_KEY=***")
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

    print(f"\n📁 Config Sources (priority: env/.env > file):")
    env_status = '✓' if os.environ.get('SKILLSMP_API_KEY') else '✗'
    dotenv_status = '✓' if os.path.exists(DOTENV_PATH) else '✗'
    print(f"  1. Environment: SKILLSMP_API_KEY {env_status}")
    print(f"  2. Repo .env: {DOTENV_PATH} {dotenv_status}")
    print(f"  3. Config file: {CONFIG_PATH} {'✓' if os.path.exists(CONFIG_PATH) else '✗'}")
    print(f"  4. Hermes config: {HERMES_CONFIG_PATH} {'✓' if os.path.exists(HERMES_CONFIG_PATH) else '✗'}")

    print(f"\n📝 Set config:")
    print(f"  Option 1 - Environment variable (recommended):")
    print(f"    export SKILLSMP_API_KEY=***")
    print(f"  Option 2 - Repo .env file:")
    print(f"    echo 'SKILLSMP_API_KEY=***' > {DOTENV_PATH}")
    print(f"  Option 3 - Config file (requires PyYAML):")
    print(f"    mkdir -p ~/.skillsmp")
    print(f"    echo 'api_key: sk_live_xxxxx' > {CONFIG_PATH}")
    print(f"  Option 4 - Hermes config (if using hermes agent):")
    print(f"    hermes config set skills.config.skillsmp.api_key YOUR_KEY")


# ---------------------------------------------------------------------------
# Project Analysis & Skill Recommendation
# ---------------------------------------------------------------------------

# Dependency -> human-readable label mapping
DEP_LABELS = {
    # Frontend
    "react": "React", "vue": "Vue", "next": "Next.js", "nuxt": "Nuxt",
    "svelte": "Svelte", "angular": "Angular", "vite": "Vite",
    "webpack": "Webpack", "tailwindcss": "Tailwind CSS", "element-plus": "Element Plus",
    "ant-design": "Ant Design", "antd": "Ant Design",
    # Backend
    "express": "Express", "fastapi": "FastAPI", "flask": "Flask",
    "django": "Django", "nestjs": "NestJS", "spring-boot": "Spring Boot",
    # Data / ML
    "pandas": "Pandas", "numpy": "NumPy", "tensorflow": "TensorFlow",
    "pytorch": "PyTorch", "scikit-learn": "Scikit-learn", "torch": "PyTorch",
    # Infra
    "docker": "Docker", "kubernetes": "Kubernetes", "terraform": "Terraform",
    # Testing
    "jest": "Jest", "pytest": "Pytest", "vitest": "Vitest", "mocha": "Mocha",
    # Other
    "typescript": "TypeScript", "eslint": "ESLint", "prettier": "Prettier",
}

# Directory pattern -> project trait
STRUCTURE_SIGNALS = {
    "Dockerfile": "docker",
    "docker-compose.yml": "docker", "docker-compose.yaml": "docker",
    ".github/workflows": "github-actions",
    ".gitlab-ci.yml": "gitlab-ci",
    "terraform": "terraform", "*.tf": "terraform",
    "jest.config": "testing", "vitest.config": "testing",
    "pytest.ini": "testing", "conftest.py": "testing",
    "vite.config": "vite", "webpack.config": "webpack",
    "tsconfig.json": "typescript",
    "tailwind.config": "tailwindcss",
    "SKILL.md": "agent-skill",
}

# File extension -> language
EXT_LANG = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".jsx": "JavaScript",
    ".vue": "Vue", ".svelte": "Svelte",
    ".go": "Go", ".rs": "Rust", ".java": "Java",
    ".rb": "Ruby", ".php": "PHP", ".cs": "C#",
    ".cpp": "C++", ".c": "C", ".swift": "Swift",
    ".kt": "Kotlin", ".dart": "Dart",
    ".sh": "Shell", ".bash": "Shell",
}

# Config file readers: filename -> (format, dependency_key)
CONFIG_PARSERS = {
    "package.json": ("json", ["dependencies"], ["devDependencies"]),
    "requirements.txt": ("pip", None),
    "pyproject.toml": ("toml_deps", None),
    "go.mod": ("gomod", None),
    "Cargo.toml": ("toml_deps", None),
    "Gemfile": ("gemfile", None),
}


def _read_file_safe(path, max_chars=8000):
    """Read file content, return empty string on error."""
    try:
        with open(path, "r", errors="ignore") as f:
            return f.read(max_chars)
    except (OSError, IOError):
        return ""


def _parse_json_deps(content, prod_keys, dev_keys=None):
    """Extract dependency names from JSON (package.json), separated by prod/dev."""
    prod = set()
    dev = set()
    try:
        data = json.loads(content)
        for key in prod_keys:
            for name in data.get(key, {}):
                prod.add(name.lower().split("/")[-1])
        if dev_keys:
            for key in dev_keys:
                for name in data.get(key, {}):
                    dev.add(name.lower().split("/")[-1])
    except (json.JSONDecodeError, AttributeError):
        pass
    return prod, dev


def _parse_pip_deps(content):
    """Extract dependency names from requirements.txt."""
    deps = set()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        name = re.split(r"[>=<!\[;]", line)[0].strip().lower()
        if name:
            deps.add(name)
    return deps


def _parse_toml_deps(content):
    """Extract dependency names from pyproject.toml or Cargo.toml (best-effort regex)."""
    deps = set()
    in_deps = False        # inside a [*.dependencies] section
    in_project = False     # inside [project] or [project.*] section (PEP 621)
    in_list = False        # inside a multiline list value

    def _extract_dep(s):
        """Extract a dependency name from a TOML value string like 'fastapi>=0.100'."""
        s = s.strip().strip('"').strip("'")
        # Strip version specifiers: >=, <=, ~=, ==, !=, >, <
        name = re.split(r'[><=~!]', s)[0].strip()
        # Strip extras: uvicorn[standard] -> uvicorn
        name = name.split('[')[0].strip()
        # Strip environment markers: pkg ; python_version >= "3.8"
        name = name.split(';')[0].strip()
        return name.lower() if name and len(name) > 1 else None

    for line in content.splitlines():
        raw = line.strip()

        # Section header
        if raw.startswith("["):
            in_list = False
            section = raw.lower()
            in_deps = "dependencies" in section
            in_project = section == "[project]" or section.startswith("[project.")
            continue

        # Skip comments and empty
        if not raw or raw.startswith("#"):
            continue

        # Inside a multiline list (PEP 621 style)
        if in_list:
            if raw.startswith("]"):
                in_list = False
                continue
            # Parse each quoted entry on this line
            for quoted in re.findall(r'"([^"]+)"', raw):
                dep = _extract_dep(quoted)
                if dep:
                    deps.add(dep)
            continue

        # Key = value
        if "=" not in raw:
            continue

        key = raw.split("=")[0].strip().strip('"').strip("'")
        rest = raw.split("=", 1)[1].strip()

        # [project] section — PEP 621 list-style deps
        if in_project:
            if rest.startswith("["):
                in_list = True
                # Parse inline entries: ["pkg1", "pkg2"]
                for quoted in re.findall(r'"([^"]+)"', rest):
                    dep = _extract_dep(quoted)
                    if dep:
                        deps.add(dep)
                if rest.endswith("]"):
                    in_list = False
                continue
            # Skip non-list keys (name, version, description, etc.)
            continue

        # [*.dependencies] section (Poetry, Cargo)
        if in_deps:
            # Dict-style: tokio = { version = "1", features = ["full"] }
            if rest.startswith("{"):
                dep = _extract_dep(key)
                if dep:
                    deps.add(dep)
                continue
            # Simple: requests = "^2.28"
            dep = _extract_dep(key)
            if dep:
                deps.add(dep)

    return deps


def _parse_gomod(content):
    """Extract dependency names from go.mod."""
    deps = set()
    in_require = False
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("require"):
            in_require = True
            if "(" not in line:
                in_require = False
                parts = line.split()
                if len(parts) >= 2:
                    deps.add(parts[1].split("/")[-1].lower())
            continue
        if in_require:
            if line == ")":
                in_require = False
                continue
            parts = line.split()
            if len(parts) >= 1:
                deps.add(parts[0].split("/")[-1].lower())
    return deps


def _parse_gemfile(content):
    """Extract gem names from Gemfile."""
    deps = set()
    for line in content.splitlines():
        m = re.match(r"^\s*gem\s+['\"](\w[\w-]+)['\"]", line)
        if m:
            deps.add(m.group(1).lower())
    return deps


def extract_tech_stack(path):
    """Extract dependencies from config files, separated into production and dev."""
    prod_deps = set()
    dev_deps = set()

    # Scan root + immediate subdirectories (for monorepo layouts like frontend/ + backend/)
    scan_dirs = [path]
    try:
        for name in os.listdir(path):
            sub = os.path.join(path, name)
            if os.path.isdir(sub) and name not in {".git", "node_modules", "__pycache__",
                                                      ".venv", "venv", "dist", "build",
                                                      ".next", ".nuxt", "vendor", "target"}:
                scan_dirs.append(sub)
    except OSError:
        pass

    for scan_dir in scan_dirs:
        for filename, (fmt, prod_keys, *rest) in CONFIG_PARSERS.items():
            filepath = os.path.join(scan_dir, filename)
            if not os.path.isfile(filepath):
                continue
            content = _read_file_safe(filepath)
            if not content:
                continue

            dev_keys = rest[0] if rest else None

            if fmt == "json":
                p, d = _parse_json_deps(content, prod_keys, dev_keys)
                prod_deps |= p
                dev_deps |= d
            elif fmt == "pip":
                prod_deps |= _parse_pip_deps(content)
            elif fmt == "toml_deps":
                prod_deps |= _parse_toml_deps(content)
            elif fmt == "gomod":
                prod_deps |= _parse_gomod(content)
            elif fmt == "gemfile":
                prod_deps |= _parse_gemfile(content)

    return prod_deps, dev_deps


def extract_languages(path, max_scan=2000):
    """Count file extensions to detect programming languages."""
    ext_count = {}
    scanned = 0
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv",
                 "dist", "build", ".next", ".nuxt", "vendor", "target"}

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in EXT_LANG:
                ext_count[ext] = ext_count.get(ext, 0) + 1
            scanned += 1
            if scanned >= max_scan:
                break
        if scanned >= max_scan:
            break

    lang_count = {}
    for ext, count in ext_count.items():
        lang = EXT_LANG[ext]
        lang_count[lang] = lang_count.get(lang, 0) + count

    return dict(sorted(lang_count.items(), key=lambda x: -x[1]))


def scan_structure(path):
    """Detect project traits from directory structure and config files."""
    traits = set()

    for root, dirs, files in os.walk(path):
        # Only scan top 2 levels
        depth = root[len(path):].count(os.sep)
        if depth > 2:
            dirs[:] = []
            continue

        for name in files + dirs:
            for pattern, trait in STRUCTURE_SIGNALS.items():
                if pattern.startswith("*"):
                    if name.endswith(pattern[1:]):
                        traits.add(trait)
                elif pattern in name:
                    traits.add(trait)

    return traits



def analyze_project(path: str, as_json: bool = False) -> None:
    """Dump raw project info for AI agent to decide search keywords.
    
    Does NOT auto-generate keywords or auto-search.
    AI agent reads this output, decides keywords, then calls search.
    """
    path = os.path.abspath(path)

    if not os.path.isdir(path):
        print(f"{RED}Error: {path} is not a directory{RESET}", file=sys.stderr)
        sys.exit(1)

    # Extract raw project info
    prod_deps, dev_deps = extract_tech_stack(path)
    langs = extract_languages(path)
    traits = scan_structure(path)

    # Read README description (first non-badge, non-empty line)
    description = ""
    for name in ["README.md", "readme.md", "README.rst", "README"]:
        readme_path = os.path.join(path, name)
        if os.path.isfile(readme_path):
            content = _read_file_safe(readme_path, max_chars=4000)
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith(("#", "<", "[!", "|", "```")):
                    description = line[:200]
                    break
            break

    # Project name from directory or package.json
    project_name = os.path.basename(path)
    pkg_path = os.path.join(path, "package.json")
    if os.path.isfile(pkg_path):
        try:
            pkg = json.loads(_read_file_safe(pkg_path, max_chars=2000))
            if pkg.get("name"):
                project_name = pkg["name"]
            if not description and pkg.get("description"):
                description = pkg["description"]
        except (json.JSONDecodeError, AttributeError):
            pass

    # JSON output for machine consumption
    if as_json:
        data = {
            "project": project_name,
            "path": path,
            "description": description,
            "languages": langs,
            "dependencies": {
                "production": sorted(prod_deps),
                "dev": sorted(dev_deps),
            },
            "traits": sorted(traits),
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    # Human-readable output
    print(f"\n{BOLD}Project:{RESET} {project_name}")
    if description:
        print(f"{GRAY}{description}{RESET}")

    if langs:
        print(f"\n{BOLD}Languages:{RESET}")
        for lang, count in list(langs.items())[:6]:
            bar = "█" * min(count, 30)
            print(f"  {lang:15s} {GRAY}{bar} {count} files{RESET}")

    if prod_deps:
        print(f"\n{BOLD}Production Dependencies:{RESET}")
        labels = [DEP_LABELS.get(d, d) for d in sorted(prod_deps)]
        for i in range(0, len(labels), 4):
            print(f"  {', '.join(labels[i:i+4])}")

    if dev_deps:
        print(f"\n{BOLD}Dev Dependencies:{RESET}")
        labels = [DEP_LABELS.get(d, d) for d in sorted(dev_deps)]
        for i in range(0, len(labels), 4):
            print(f"  {GRAY}{', '.join(labels[i:i+4])}{RESET}")

    if traits:
        print(f"\n{BOLD}Detected:{RESET}")
        print(f"  {', '.join(sorted(traits))}")

    print(f"\n{GRAY}Use this info to decide search keywords, then run:{RESET}")
    print(f"  python search.py search \"<keyword>\" --sort stars --limit 5")


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
  %(prog)s analyze .                                # Dump project info for AI
  %(prog)s analyze . --json                         # Project info as JSON
  %(prog)s info                                     # Check API status
  %(prog)s config                                   # Show configuration

Configuration:
  export SKILLSMP_API_KEY=***             # Set API key (recommended)
  Or create .env in repo root             # SKILLSMP_API_KEY=***
  Or get key: https://skillsmp.com/docs/api
""",
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {VERSION}")
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
    search_parser.add_argument("--bilingual", "-b", metavar="EN_KEYWORD", help="Pre-translated English keyword for bilingual search (e.g. -b \"code review\")")
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

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Dump project info for AI agent")
    analyze_parser.add_argument("path", nargs="?", default=".", help="Project path (default: current directory)")
    analyze_parser.add_argument("--json", action="store_true", help="Output raw JSON")

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
            bilingual_query=args.bilingual,
            with_ai=args.ai
        )
        print_results(data, verbose=args.verbose, as_json=args.json, save_path=args.save)

    elif args.command == "ai-search":
        if not config["api_key"]:
            print("❌ Error: API key required for AI search.")
            print("   Set via: export SKILLSMP_API_KEY=***")
            print("   Or get key: https://skillsmp.com/docs/api")
            return
        data = ai_search(args.query, api_key=config["api_key"])
        print_results(data, verbose=args.verbose, as_json=args.json, save_path=args.save)

    elif args.command == "info":
        print_info(config)

    elif args.command == "config":
        print_config(config)

    elif args.command == "analyze":
        analyze_project(args.path, as_json=args.json)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
