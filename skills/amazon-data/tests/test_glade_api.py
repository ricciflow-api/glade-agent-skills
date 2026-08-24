import json
import os
import sys
import unittest
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import glade_api  # noqa: E402


def mock_response(payload):
    context = MagicMock()
    context.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    return context


class ValidationTests(unittest.TestCase):
    def test_product_requires_exactly_one_identifier(self):
        with self.assertRaisesRegex(glade_api.GladeClientError, "exactly one"):
            glade_api._query_params("product", {"domain": "US"})
        with self.assertRaisesRegex(glade_api.GladeClientError, "exactly one"):
            glade_api._query_params(
                "product",
                {"domain": "US", "asin": "B0D1XD1ZV3", "gtin": "1234567890123"},
            )

    def test_search_requires_term(self):
        with self.assertRaisesRegex(glade_api.GladeClientError, "search-term"):
            glade_api._query_params("search", {"domain": "US"})

    def test_rejects_invalid_page_and_price_range(self):
        with self.assertRaisesRegex(glade_api.GladeClientError, "page"):
            glade_api._query_params(
                "search", {"domain": "US", "search_term": "books", "page": 101}
            )
        with self.assertRaisesRegex(glade_api.GladeClientError, "max-price"):
            glade_api._query_params(
                "search",
                {
                    "domain": "US",
                    "search_term": "books",
                    "min_price": 20,
                    "max_price": 10,
                },
            )

    def test_boolean_uses_lowercase_wire_value(self):
        params = glade_api._query_params(
            "reviews",
            {
                "domain": "US",
                "asin": "B0D1XD1ZV3",
                "only_verified_reviews": True,
            },
        )
        self.assertEqual(params["onlyVerifiedReviews"], "true")


class RequestTests(unittest.TestCase):
    @patch("glade_api.urllib.request.urlopen")
    def test_product_request_path_headers_and_query(self, urlopen):
        urlopen.return_value = mock_response(
            {"data": {"amazonProduct": {"asin": "B0D1XD1ZV3"}}}
        )
        with patch.dict(
            os.environ,
            {"GLADE_API_KEY": "test-key", "GLADE_API_BASE_URL": "https://gladeapi.com"},
            clear=True,
        ):
            payload = glade_api.request(
                "product", {"domain": "US", "asin": "B0D1XD1ZV3"}
            )
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url.split("?")[0], "https://gladeapi.com/api/amazon/product")
        self.assertIn("asin=B0D1XD1ZV3", request.full_url)
        self.assertIn("domain=US", request.full_url)
        self.assertEqual(request.get_header("Api-key"), "test-key")
        self.assertEqual(payload["data"]["amazonProduct"]["asin"], "B0D1XD1ZV3")

    def test_missing_key_is_safe_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(glade_api.GladeClientError, "GLADE_API_KEY"):
                glade_api.request(
                    "product", {"domain": "US", "asin": "B0D1XD1ZV3"}
                )

    def test_rejects_non_loopback_http_origin(self):
        with patch.dict(
            os.environ,
            {"GLADE_API_BASE_URL": "http://example.com", "GLADE_API_KEY": "test-key"},
            clear=True,
        ):
            with self.assertRaisesRegex(glade_api.GladeClientError, "HTTPS"):
                glade_api._base_url()

    def test_allows_loopback_http_origin(self):
        with patch.dict(
            os.environ,
            {"GLADE_API_BASE_URL": "http://127.0.0.1:3000"},
            clear=True,
        ):
            self.assertEqual(glade_api._base_url(), "http://127.0.0.1:3000")

    @patch("glade_api.urllib.request.urlopen")
    def test_http_error_is_bounded_and_structured(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError(
            "https://gladeapi.com/api/amazon/product",
            401,
            "Unauthorized",
            {},
            BytesIO(b'{"success":false,"errors":[{"message":"Unauthorized"}]}'),
        )
        with patch.dict(os.environ, {"GLADE_API_KEY": "bad-key"}, clear=True):
            with self.assertRaisesRegex(glade_api.GladeClientError, "HTTP 401"):
                glade_api.request(
                    "product", {"domain": "US", "asin": "B0D1XD1ZV3"}
                )


if __name__ == "__main__":
    unittest.main()
