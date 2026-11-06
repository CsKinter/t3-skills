# Deterministic ranking + LLM explainer

Do not ask the LLM to rank from invented prices. Compute score first, constrain model to returned IDs.

## Features (min-max normalize across candidate set)

- `price_inv` = 1 - norm(price) (lower price better)
- `discount` = (original_price - price)/original_price if original_price else 0, clip at 0.40
- `sold` = log(1+sold_quantity) normalized (bucketed: 25~=6-25, 50~=51-100 — break close races with review totals)
- `rating` = rating_average/5, `reviews` = log(1+paging.total)
- `seller_rep`: green=1.0, light_green=0.8, yellow=0.5, red/null=0 + MercadoLider platinum +0.1; hard gate: drop red/null + high claims proxy unless user opts in
- `shipping`: free FULL=1.0, free standard=0.8, paid<=15% price=0.5, else 0; hard gate shipping cost >15% unless opted in
- `locality`: 1 if seller city ~= target (e.g. Santiago/RM) or logisticType=fulfillment + nextDayDelivery, else 0

## Weights by intent (sum 1.0)

- Best offer: `0.30*price_inv + 0.15*discount + 0.20*sold + 0.10*rating + 0.05*reviews + 0.10*seller_rep + 0.05*shipping + 0.05*locality`
- Most reviewed: `0.15*price_inv + 0.05*discount + 0.30*sold + 0.15*rating + 0.15*reviews + 0.10*seller_rep + 0.05*shipping + 0.05*locality`
- Best local: raise `locality` to 0.20, take from `price_inv`.

Tune on ~50 labeled queries; weights above are a starting proposal, not validated MELI weights (ranking is proprietary). Reputation is the #1 SEO driver on MELI — weight it heavily.

## Most-reviewed recipe (no native sort)

1. `GET /sites/MLC/search?q={q}&limit=50` (relevance order)
2. Client-side sort by `sold_quantity` bucket desc as popularity proxy
3. Top-N (5-10) -> `GET /reviews/item/{id}` for `paging.total` + `rating_average`
4. Final rank = f(total reviews, rating_average, sold_quantity)

## LLM contract (Spanish, temperature 0-0.2)

Input: query + candidates [{id, title, price, original_price, discount_pct, sold_quantity, rating_average, review_total, seller_rep, shipping, permalink}] + top 3-5 review snippets per finalist.

Output JSON schema only:
```json
{"ranked_ids": ["MLA...", "..."], "pick": {"id": "...", "reason": "..."}, "items": [{"id": "...", "verdict_1line": "...", "pros": ["...", "..."], "cons": ["..."], "price_note": "..."}]}
```
Rules: `ranked_ids` must be subset of input IDs (3-5 items), prices/discounts copied verbatim, never generated, 2 pros / 1 contra cited from snippets, 1-line verdict per item. Server-side validator: reject any ID not in candidate set, retry once, else fall back to deterministic order.

Cost: ~1500 in + 400 out tokens ~= $0.0005/query on gpt-4o-mini (less on Gemini Flash-Lite). Latency 1-3s — stream "buscando..." first.

Review summarization MVP = extractive (pass snippets, ask for pros/cons). Skip abstractive synthesis.
