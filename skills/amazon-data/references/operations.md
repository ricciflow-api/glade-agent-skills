# Glade operation catalog

Use this reference when selecting an exact MCP tool or REST fallback command.
All operations accept an optional `domain` marketplace code that defaults to
`US`.

| REST command | MCP tool | REST path | Operation parameters |
|---|---|---|---|
| `product` | `get_amazon_product` | `/api/amazon/product` | Exactly one of `asin`, `url`, `gtin` |
| `gtin-from-asin` | `get_amazon_gtin_from_asin` | `/api/amazon/product/gtin-from-asin` | `asin` |
| `asin-from-gtin` | `get_amazon_asin_from_gtin` | `/api/amazon/product/asin-from-gtin` | `gtin` |
| `variants` | `get_amazon_product_variants` | `/api/amazon/product/variants` | Exactly one of `asin`, `url`, `gtin` |
| `stock` | `get_amazon_product_stock` | `/api/amazon/product/stock` | Exactly one of `asin`, `url`, `gtin` |
| `sales` | `get_amazon_product_sales` | `/api/amazon/product/sales` | Exactly one of `asin`, `url`, `gtin` |
| `reviews` | `get_amazon_product_reviews` | `/api/amazon/product/reviews` | Identifier; `page`, `onlyVerifiedReviews`, `rating`, `search` |
| `offers` | `get_amazon_product_offers` | `/api/amazon/product/offers` | Identifier; `page` |
| `search` | `search_amazon_products` | `/api/amazon/search` | `searchTerm`; optional filters, sort, page, limit |
| `autocomplete` | `get_amazon_autocomplete` | `/api/amazon/autocomplete` | `searchTerm`; optional `category` |
| `categories` | `get_amazon_categories` | `/api/amazon/categories` | None |
| `category` | `get_amazon_category` | `/api/amazon/category` | `categoryId`; optional `page`, `sort` |
| `seller` | `get_amazon_seller` | `/api/amazon/seller` | `sellerId`; optional `page` |
| `author` | `get_amazon_author` | `/api/amazon/author` | Book `asin`; optional `page` |
| `deals` | `get_amazon_deals` | `/api/amazon/deals` | Optional `page`, `limit`, `categoryIds` |
| `bestsellers` | `get_amazon_bestsellers` | `/api/amazon/bestsellers` | Exactly one of `categoryId`, `url`; optional `page`, `limit` |
| `bestseller-categories` | `get_amazon_bestseller_categories` | `/api/amazon/bestseller-categories` | None |

## Filters

- `page`: integer from 1 through 100.
- `limit`: integer from 1 through 100.
- Search `sort`: `FEATURED`, `MOST_RECENT`, `PRICE_ASCENDING`,
  `PRICE_DESCENDING`, or `AVERAGE_CUSTOMER_REVIEW`.
- Search `conditions`: comma-separated `NEW`, `USED`, or `RENEWED`.
- Review `rating`: `ALL`, `FIVE_STAR`, `FOUR_STAR`, `THREE_STAR`,
  `TWO_STAR`, or `ONE_STAR`.
- `categoryIds`: comma-separated Amazon category node IDs.

The OpenAPI 3.1 source of truth is
<https://gladeapi.com/api/v1/openapi.json>.
