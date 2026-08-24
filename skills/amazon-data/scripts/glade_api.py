#!/usr/bin/env python3
"""Zero-dependency CLI for the public Glade REST API."""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_BASE_URL = "https://gladeapi.com"
TIMEOUT_SECONDS = 30
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
USER_AGENT = "glade-agent-skills/1.0 (+https://github.com/asterism-software/glade-agent-skills)"
MARKETPLACES = ("US", "UK", "CA", "DE", "FR", "IT", "ES", "AU", "IN", "MX", "BR", "JP", "PL")
SORTS = (
    "FEATURED",
    "MOST_RECENT",
    "PRICE_ASCENDING",
    "PRICE_DESCENDING",
    "AVERAGE_CUSTOMER_REVIEW",
)
RATINGS = ("ALL", "FIVE_STAR", "FOUR_STAR", "THREE_STAR", "TWO_STAR", "ONE_STAR")

PATHS = {
    "product": "/api/amazon/product",
    "gtin-from-asin": "/api/amazon/product/gtin-from-asin",
    "asin-from-gtin": "/api/amazon/product/asin-from-gtin",
    "variants": "/api/amazon/product/variants",
    "stock": "/api/amazon/product/stock",
    "sales": "/api/amazon/product/sales",
    "reviews": "/api/amazon/product/reviews",
    "offers": "/api/amazon/product/offers",
    "search": "/api/amazon/search",
    "autocomplete": "/api/amazon/autocomplete",
    "categories": "/api/amazon/categories",
    "category": "/api/amazon/category",
    "seller": "/api/amazon/seller",
    "author": "/api/amazon/author",
    "deals": "/api/amazon/deals",
    "bestsellers": "/api/amazon/bestsellers",
    "bestseller-categories": "/api/amazon/bestseller-categories",
}

PARAMETER_MAP = {
    "domain": "domain",
    "asin": "asin",
    "url": "url",
    "gtin": "gtin",
    "page": "page",
    "limit": "limit",
    "sort": "sort",
    "rating": "rating",
    "search": "search",
    "search_term": "searchTerm",
    "category": "category",
    "category_id": "categoryId",
    "category_ids": "categoryIds",
    "seller_id": "sellerId",
    "conditions": "conditions",
    "min_price": "minPrice",
    "max_price": "maxPrice",
    "only_verified_reviews": "onlyVerifiedReviews",
}

OPERATION_PARAMETERS = {
    "product": ("asin", "url", "gtin"),
    "gtin-from-asin": ("asin",),
    "asin-from-gtin": ("gtin",),
    "variants": ("asin", "url", "gtin"),
    "stock": ("asin", "url", "gtin"),
    "sales": ("asin", "url", "gtin"),
    "reviews": ("asin", "url", "gtin", "page", "only_verified_reviews", "rating", "search"),
    "offers": ("asin", "url", "gtin", "page"),
    "search": (
        "search_term",
        "category_id",
        "sort",
        "conditions",
        "min_price",
        "max_price",
        "page",
        "limit",
    ),
    "autocomplete": ("search_term", "category"),
    "categories": (),
    "category": ("category_id", "page", "sort"),
    "seller": ("seller_id", "page"),
    "author": ("asin", "page"),
    "deals": ("page", "limit", "category_ids"),
    "bestsellers": ("category_id", "url", "page", "limit"),
    "bestseller-categories": (),
}

EXACTLY_ONE = {
    "product": ("asin", "url", "gtin"),
    "variants": ("asin", "url", "gtin"),
    "stock": ("asin", "url", "gtin"),
    "sales": ("asin", "url", "gtin"),
    "reviews": ("asin", "url", "gtin"),
    "offers": ("asin", "url", "gtin"),
    "bestsellers": ("category_id", "url"),
}

REQUIRED = {
    "gtin-from-asin": ("asin",),
    "asin-from-gtin": ("gtin",),
    "search": ("search_term",),
    "autocomplete": ("search_term",),
    "category": ("category_id",),
    "seller": ("seller_id",),
    "author": ("asin",),
}


class GladeClientError(RuntimeError):
    """A safe, user-facing client or API error."""


def _api_key():
    key = os.environ.get("GLADE_API_KEY", "").strip()
    if not key:
        raise GladeClientError(
            "GLADE_API_KEY is not configured. Create a key at "
            "https://gladeapi.com/auth/login?next=/dashboard and store it in your secret manager."
        )
    return key


def _base_url():
    value = os.environ.get("GLADE_API_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    parsed = urllib.parse.urlparse(value)
    loopback = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if parsed.username or parsed.password or not parsed.hostname:
        raise GladeClientError("GLADE_API_BASE_URL must be an origin without credentials")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
        raise GladeClientError("GLADE_API_BASE_URL must use HTTPS or an HTTP loopback origin")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise GladeClientError("GLADE_API_BASE_URL must not include a path, query, or fragment")
    return value


def _validate(operation, params):
    if operation not in PATHS:
        raise GladeClientError(f"Unsupported operation: {operation}")
    if params.get("domain", "US") not in MARKETPLACES:
        raise GladeClientError("Unsupported Amazon marketplace code")

    for name in REQUIRED.get(operation, ()):
        if params.get(name) in (None, ""):
            raise GladeClientError(f"{operation} requires {name.replace('_', '-')}")

    names = EXACTLY_ONE.get(operation)
    if names:
        supplied = [name for name in names if params.get(name) not in (None, "")]
        if len(supplied) != 1:
            display = ", ".join(name.replace("_", "-") for name in names)
            raise GladeClientError(f"{operation} requires exactly one of: {display}")

    asin = params.get("asin")
    if asin and not re.fullmatch(r"[A-Za-z0-9]{10}", str(asin)):
        raise GladeClientError("asin must contain exactly 10 letters or digits")
    for name in ("page", "limit"):
        value = params.get(name)
        if value is not None and not 1 <= value <= 100:
            raise GladeClientError(f"{name} must be from 1 through 100")
    if params.get("min_price") is not None and params["min_price"] < 0:
        raise GladeClientError("min-price must not be negative")
    if params.get("max_price") is not None and params["max_price"] < 0:
        raise GladeClientError("max-price must not be negative")
    if (
        params.get("min_price") is not None
        and params.get("max_price") is not None
        and params["max_price"] < params["min_price"]
    ):
        raise GladeClientError("max-price must not be below min-price")


def _query_params(operation, params):
    _validate(operation, params)
    allowed = ("domain",) + OPERATION_PARAMETERS[operation]
    result = {}
    for name in allowed:
        value = params.get(name)
        if value is None:
            continue
        if isinstance(value, bool):
            value = "true" if value else "false"
        result[PARAMETER_MAP[name]] = value
    return result


def request(operation, params):
    """Call one allowlisted Glade operation and return decoded JSON."""
    query = urllib.parse.urlencode(_query_params(operation, params))
    url = f"{_base_url()}{PATHS[operation]}"
    if query:
        url += "?" + query
    request_object = urllib.request.Request(
        url,
        headers={
            "API-KEY": _api_key(),
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request_object, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise GladeClientError("Glade API response exceeded the 8 MiB safety limit")
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read(2000).decode("utf-8", errors="replace")
        raise GladeClientError(f"Glade API returned HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise GladeClientError(f"Could not reach Glade API: {error.reason}") from error
    except json.JSONDecodeError as error:
        raise GladeClientError("Glade API returned invalid JSON") from error


def _add_parameter(parser, name):
    if name == "asin":
        parser.add_argument("--asin")
    elif name == "url":
        parser.add_argument("--url")
    elif name == "gtin":
        parser.add_argument("--gtin")
    elif name == "page":
        parser.add_argument("--page", type=int, default=1)
    elif name == "limit":
        parser.add_argument("--limit", type=int)
    elif name == "sort":
        parser.add_argument("--sort", choices=SORTS)
    elif name == "rating":
        parser.add_argument("--rating", choices=RATINGS)
    elif name == "search":
        parser.add_argument("--search")
    elif name == "search_term":
        parser.add_argument("--search-term", dest="search_term")
    elif name == "category":
        parser.add_argument("--category")
    elif name == "category_id":
        parser.add_argument("--category-id", dest="category_id")
    elif name == "category_ids":
        parser.add_argument("--category-ids", dest="category_ids")
    elif name == "seller_id":
        parser.add_argument("--seller-id", dest="seller_id")
    elif name == "conditions":
        parser.add_argument("--conditions")
    elif name == "min_price":
        parser.add_argument("--min-price", dest="min_price", type=float)
    elif name == "max_price":
        parser.add_argument("--max-price", dest="max_price", type=float)
    elif name == "only_verified_reviews":
        parser.add_argument(
            "--only-verified-reviews",
            dest="only_verified_reviews",
            action="store_true",
            default=None,
        )


def build_parser():
    parser = argparse.ArgumentParser(description="Call the public Glade REST API")
    subparsers = parser.add_subparsers(dest="operation", required=True)
    for operation in PATHS:
        operation_parser = subparsers.add_parser(operation)
        operation_parser.add_argument("--domain", choices=MARKETPLACES, default="US")
        for name in OPERATION_PARAMETERS[operation]:
            _add_parameter(operation_parser, name)
    return parser


def main():
    args = vars(build_parser().parse_args())
    operation = args.pop("operation")
    try:
        payload = request(operation, args)
    except GladeClientError as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
