# MercadoLibre endpoints, auth, quotas

Base: `https://api.mercadolibre.com`. Auth domain per country: `https://auth.mercadolibre.{cl/ar/mx/br/...}/authorization`.

## Search

`GET /sites/{SITE_ID}/search`

Params: `q`, `category` (site-namespaced, re-resolve per country), `shipping_cost=free` (or `shipping` filter id from `available_filters`), price range (verify `price=` syntax live per query), `sort` (use only IDs from `available_sorts`; documented: relevance default, `price_asc`, `price_desc`), `limit` (default 50, keep <=50), `offset`, `include_filters=true` (restores `filters`/`available_filters` hidden by default on seller-scoped search), `attributes` projection (e.g. `id,title,price,currency_id,original_price,permalink,thumbnail,sold_quantity`).

Response: `{results[], paging, filters[], available_filters[], available_sorts[]}`. Always read `available_filters`/`available_sorts` from first response instead of hardcoding.

Pagination: `offset`/`limit`, practical ceiling ~1000. Deep scan uses `search_type=scan` + `scroll_id` (5min expiry, private `/users/{id}/items/search` and `/questions/search`); never combine `scroll_id` with `offset`/`limit`.

## Discovery / taxonomy

- `GET /sites/{SITE}/domain_discovery/search?limit=1&q=` -> `{domain_id, category_id, attributes[] (BRAND, MODEL...)}`
- `GET /sites/{SITE}/category_predictor/predict?q=` or `?title=` -> most accurate category (verify `id` vs `category_id` field live)
- `GET /sites/{SITE}/categories` -> tree; `GET /categories/{ID}` -> `path_from_root`, `children_categories[]` (with `total_items_in_this_category`), `settings`
- `GET /categories/{ID}/attributes` -> `value_type` (string/number/number_unit/boolean/list), `values[]`, `tags[]` (required, allowed_variations, catalog_required...). `GET /categories/{ID}/technical_specs/input` -> required specs; missing specs tag items `incomplete_technical_specs` (ranking penalty).
- Since 2025-10-29 MELI auto-recategorizes API-listed items — never hardcode category IDs long-term; listen for item changes if you list.

## Items / users (bulk migration Oct 2026)

- `GET /items/{id}` full detail (exact stock, `pictures[]`, `seller_address`, `attributes`, `health`).
- Multiget `GET /items?ids=A,B` (max 20, `&attributes=...` projection) deprecated 2026-10-25 -> use `GET /items/bulk?ids=` with `attributes=body.X` prefix and new `status_code` field. Same for `/users?ids=` -> `/users/bulk?ids=`.
- `GET /users/{id}` -> `{nickname, address{city, state}, seller_reputation{level_id (5_green..1_red thermometer), power_seller_status (platinum/gold/silver MercadoLider), transactions{canceled, completed, total, ratings{positive,neutral,negative}}, metrics{sales, claims{rate}, delayed_handling_time, cancellations}}}`. May return 206 Partial Content on reputation sub-fetch failure. Cache days (slow-moving 60-day windows).

## Reviews / questions

- `GET /reviews/item/{ITEM_ID}?limit=&offset=` — needs Bearer token, no special scope. Default `limit=5`, ~50 works in practice. Returns `{paging{total, limit, offset, total_pageable}, rating_average, stars, rating_levels{one..five_star}, reviews[{id, title, content, rate 1-5, date_created, likes/dislikes, buying_date, condition, media[], attributes_variation}]}`. `reviewer_id` always 0, `order_id` confidential. `reviews_with_comment` deprecated, paginate on `total_pageable`. Paused/removed -> empty/404. Mega-reviewed caps after few hundred; dedupe.
- `GET /questions/search?item_id=&seller_id=&from_id=` — needs token. Product page shows 20 latest as shoppers see it (scrape-only for anonymous).

## Locations / currency

- `GET /sites` -> site list (`MLC` Chile CLP, `MLA`, `MLB`, `MLM`, `MCO`, `MLU`, `MPE`...). Currency: `GET /currencies`, conversion `GET /currency_conversions/search?from=&to=`. CLP: `decimal_places 0`.
- `GET /classified_locations/countries|states|cities` — marked Classifieds-only (real estate/vehicles/services). No confirmed city filter for general product search; derive locality per-item.

## Auth / quotas

OAuth2 Authorization Code Grant (server-side). `redirect_uri` exact match, HTTPS, owner account (operators get `invalid_operator_user_id`). Scopes: `read`, `write`, `offline_access` (required for refresh_token). Errors: `invalid_client`, `invalid_grant` (expired/reused code/refresh), `invalid_scope`, `local_rate_limited (429)`, `forbidden (403)`.

Rate limits: no published numeric quota. Official 429 doc (updated 2026-05-05): per-Client-ID per-endpoint control, backoff+jitter, avoid spikes, serialize scrolls. Third-party cites ~1500 req/min/seller (unverified). Search appears free (costs in docs are listing/sale fees, not API calls). Budget well under hundreds RPM/app, serialize, cache.

Live probe Nov 2026: anonymous `GET /sites/MLC/search?q=mouse&limit=3` -> 403 (docs show Bearer everywhere; may be WAF vs token requirement — handle both).
