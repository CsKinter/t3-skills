---
name: MercadoLibre API
description: Search and rank MercadoLibre listings with AI assistance for deal bots and shopping assistants. Use this whenever the user mentions MercadoLibre, Mercado Libre, Meli, MLC/MLA/MLM, building a Telegram or WhatsApp product-search bot, or asks for best offer, most reviewed, best local offer, price tracking, seller reputation, or review summarization on MercadoLibre - even if they don't explicitly say API.
---

# MercadoLibre API for AI deal bots

Use raw HTTPS against the official MercadoLibre API. There is no maintained SDK (official Python/Node SDKs archived 2021). Do not invent endpoints.

Base: `https://api.mercadolibre.com`
Country = SITE_ID: `MLC` Chile, `MLA` Argentina, `MLM` Mexico, `MLB` Brazil, `MCO` Colombia, `MLU` Uruguay, `MPE` Peru.

## Auth

Current docs (2026) show `Authorization: Bearer APP_USR-...` on all examples including search. Older bots worked without a token.
Rule: try with token first, fall back to anonymous on 403 only for read-only search.

1. Create app at per-country DevCenter (e.g. developers.mercadolibre.cl) -> My Applications -> Client ID + Secret, HTTPS redirect URI, scopes `read` (+ `offline_access` only if you need refresh).
2. OAuth Authorization Code Grant: `GET https://auth.mercadolibre.{cc}/authorization?response_type=code&client_id=$APP_ID&redirect_uri=$URL` -> `POST /oauth/token` with `grant_type=authorization_code`.
3. Access token 6h (`expires_in` 10800). Refresh single-use rotation: `grant_type=refresh_token`. Refresh before expiry minus 5min. Re-auth on `invalid_grant`.

Read-only deal bot needs only `read` scope. Never hardcode secrets; use env vars.

## Core workflow (vague Spanish query -> ranked picks)

For queries like "mouse con ruedita infinita", "mejor oferta local de audifonos", "mas resenado X":

1. **Expand** query with LLM into 2-4 Spanish variants (e.g. `mouse scroll infinito` -> `mouse ruedita infinita`, `mouse hyperscroll`, `Logitech MX Master`).
2. **Search**: `GET /sites/{SITE}/search?q={variant}&limit=20` (or 50 for "most reviewed"). Read `available_filters` / `available_sorts` from response to discover valid filter IDs. Second filtered call with `category`, `shipping_cost=free`, price range if known.
3. **Pin category (do not hardcode IDs)**: `GET /sites/{SITE}/domain_discovery/search?limit=1&q={query}` -> `category_id` + inferred attributes, or `GET /sites/{SITE}/category_predictor/predict?q={title}`. Then `GET /categories/{ID}/attributes` for feature vocabulary. Cache tree/attrs 7-30 days. Category IDs are site-namespaced (`MLC...` != `MLA...`).
4. **Enrich top-N only**: `GET /items/{id}` (or `/items/bulk?ids=` after 2026-10-25 deprecation of `/items?ids=`, max 20 IDs, `&attributes=` projection) for exact stock/pictures, `GET /reviews/item/{id}?limit=5` for `rating_average` + `paging.total`, `GET /users/{seller_id}` for `seller_reputation`.
5. **Score deterministically first, LLM explains second.** Never let the LLM invent prices/IDs. See `references/ranking.md`.
6. **Reply** with photo + price/discount/sold/rating line + `[Ver en MELI](permalink)` button. Telegram first; WhatsApp only on demand (see below).

## Endpoint cheat sheet

```
GET /sites/{SITE}/search?q=&category=&sort=&limit=&offset=&attributes=
GET /sites/{SITE}/domain_discovery/search?limit=1&q=
GET /sites/{SITE}/category_predictor/predict?q=  (or ?title=)
GET /sites/{SITE}/categories
GET /categories/{CATEGORY_ID}  (path_from_root, children_categories)
GET /categories/{CATEGORY_ID}/attributes
GET /items/{id} / GET /items/bulk?ids=A,B (max 20, attributes=body.X after Oct 2026)
GET /users/{id} / GET /users/bulk?ids=  (seller_reputation, address.city/state)
GET /reviews/item/{id}?limit=&offset=  (needs token, no special scope, reviewer_id always 0)
GET /questions/search?item_id=  (needs token)
```

Sort: only `price_asc` / `price_desc` + relevance are documented for public search. No `sold_quantity_desc` / `reviews` sort — sort client-side. See `references/endpoints.md`.

Key fields: `id, title, price, original_price (discount = (orig-price)/orig), sold_quantity (bucketed: 25~=6-25, 50~=51-100), available_quantity (bucketed RANGO_1_50->1 in search, exact only in item detail), condition, shipping.free_shipping/logistic_type, seller_reputation{level_id, power_seller_status}, permalink, thumbnail (list) vs pictures[].url (detail, use largest for Telegram sendPhoto), catalog_product_id (dedupe key), seller_address.city/state.

Local (e.g. Santiago) heuristic: `seller_address.city ~= Santiago/RM` + `logisticType=fulfillment` (Full) + `nextDayDelivery=true` + `freeShipping=true` + `isInternational=false`. No commune-level filter exists; Mercado Envios is national.

## Rules to avoid failures

- 429 = backoff with jitter (1s,2s,4s), respect `Retry-After`. No published RPM; assume low for anonymous, ~hundreds/min per app. Cache categories/attrs 15min in-memory + SQLite persistent. Collapse polls.
- Search window ~1000 results max (`limit` default 50, `offset`/`limit` pagination). For sweeps, narrow by category rather than deep-offsetting. Never combine `scroll_id` with `offset`/`limit`.
- Empty `results` with `category=` set -> retry q-only, then predictor, then browse tree. Over-constrained `category+q` is the #1 zero-result cause.
- Images: list `thumbnail` is blurry; detail `pictures[0]` for cards, fallback to thumbnail.
- `original_price` often null (only during promo) -> fallback to category median ratio, cap discount at 40% to avoid fake-original bait.
- Reviews: paginate on `total_pageable`, not deprecated `reviews_with_comment`. Paused/removed items -> empty/404. Mega-reviewed items cap after a few hundred; dedupe across star sorts.
- No price-history endpoint. Build own: poll every 6-24h into SQLite `(item_id, price, ts)`, alert on `price <= min(history)*0.9` or `<= user_target`. MercadoTrack is in maintenance (MELI policy changes) — do not depend on trackers.
- For bulk unauthenticated sweeps or Q&A-as-shown/badges only, rent Apify `sourabhbgp/mercadolibre-scraper` (~$1/1k search rows, $2/1k product/reviews, Chile supported). Official API first for live ranking.

## Messaging

Telegram Bot API: free, 30 msg/s overall, 1 msg/s per chat, 4096-char text, inline keyboards with URL buttons to `permalink`. Start with long-polling (`aiogram 3`), switch to webhook (`FastAPI POST /webhook`) for scale. Cost ~$0 + $5-6 VPS.

WhatsApp Cloud API (Chile Oct 2026): Service/Utility $0.02, Marketing $0.0889 per delivered msg; only first 1000 service msgs/number/month free. 9000 replies/mo ~= $160. Use same `notify(text, image)` interface, Telegram default. Every outbound outside 24h window must fit a template category.

Minimal stack: `aiogram 3 + FastAPI + httpx (meli.py) + SQLite (searches, items_seen, watches) + APScheduler hourly watch checks`. On-demand search default; scheduled polling only for watched price drops. Dedup on `item_id`, near-dup collapse by normalized title or `catalog_product_id`, keep cheapest/full-shipping variant.

Latency budget p50: MELI 300-800ms x2 + bulk 300ms + scorer <50ms + LLM 1-3s = ~2-5s. Send "buscando..." placeholder first; text before photo.

See `references/endpoints.md` for params/auth/quotas, `references/ranking.md` for scoring + LLM JSON contract, `scripts/meli_search.py` for a working client.
