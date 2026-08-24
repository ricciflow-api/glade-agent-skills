#!/usr/bin/env python3
"""Non-billable live checks for the public contract and auth boundary."""

import json
import urllib.error
import urllib.request


BASE_URL = "https://gladeapi.com"
EXPECTED_PATHS = {
    "/api/amazon/author",
    "/api/amazon/autocomplete",
    "/api/amazon/bestseller-categories",
    "/api/amazon/bestsellers",
    "/api/amazon/categories",
    "/api/amazon/category",
    "/api/amazon/deals",
    "/api/amazon/product",
    "/api/amazon/product/asin-from-gtin",
    "/api/amazon/product/gtin-from-asin",
    "/api/amazon/product/offers",
    "/api/amazon/product/reviews",
    "/api/amazon/product/sales",
    "/api/amazon/product/stock",
    "/api/amazon/product/variants",
    "/api/amazon/search",
    "/api/amazon/seller",
}

contract_request = urllib.request.Request(
    f"{BASE_URL}/api/v1/openapi.json",
    headers={"Accept": "application/json", "User-Agent": "glade-agent-skills-live-check/1.0"},
)
with urllib.request.urlopen(contract_request, timeout=30) as response:
    contract = json.load(response)
assert contract["openapi"] == "3.1.0"
assert set(contract["paths"]) == EXPECTED_PATHS

request = urllib.request.Request(
    f"{BASE_URL}/api/amazon/product?asin=B0D1XD1ZV3&domain=US",
    headers={"Accept": "application/json", "User-Agent": "glade-agent-skills-live-check/1.0"},
)
try:
    urllib.request.urlopen(request, timeout=30)
except urllib.error.HTTPError as error:
    assert error.code == 401
else:
    raise AssertionError("REST must reject a missing credential")

print("Live OpenAPI and REST authentication checks passed.")
