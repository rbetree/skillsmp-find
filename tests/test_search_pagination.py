import importlib.util
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "search.py"
SPEC = importlib.util.spec_from_file_location("skillsmp_search", MODULE_PATH)
search = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(search)


def _api_result(skill_id, name, pagination):
    return {
        "success": True,
        "data": {
            "success": True,
            "data": {
                "skills": [
                    {
                        "id": skill_id,
                        "name": name,
                        "description": name,
                        "stars": 1,
                    }
                ],
                "pagination": pagination,
            },
        },
        "rate_limits": {"daily_limit": "50"},
    }


class SearchPaginationTests(unittest.TestCase):
    def test_single_keyword_search_preserves_upstream_pagination(self):
        upstream_pagination = {
            "page": 2,
            "limit": 1,
            "total": 1000,
            "totalPages": 1000,
            "hasNext": True,
            "hasPrev": True,
        }

        with mock.patch.object(
            search,
            "api_request",
            return_value=_api_result("skill-1", "code-review", upstream_pagination),
        ):
            result = search.search_skills("code review", page=2, limit=1)

        pagination = result["data"]["data"]["pagination"]
        self.assertEqual(pagination, upstream_pagination)
        self.assertEqual(result["_source_tags"], {"skill-1": "kw"})

    def test_bilingual_search_reports_merged_pagination(self):
        def fake_api_request(endpoint, params=None, api_key="", max_retries=3):
            query = params["q"]
            if query == "前端鉴权":
                return _api_result("skill-cn", "iam", {"page": 1, "limit": 1})
            return _api_result("skill-en", "authorization", {"page": 1, "limit": 1})

        with mock.patch.object(search, "api_request", side_effect=fake_api_request):
            result = search.search_skills(
                "前端鉴权",
                limit=5,
                bilingual_query="frontend authorization",
            )

        pagination = result["data"]["data"]["pagination"]
        self.assertEqual(pagination["mode"], "merged")
        self.assertEqual(pagination["total"], 2)
        self.assertFalse(pagination["hasNext"])
        self.assertEqual(result["_queries"], ["前端鉴权", "frontend authorization"])


if __name__ == "__main__":
    unittest.main()
