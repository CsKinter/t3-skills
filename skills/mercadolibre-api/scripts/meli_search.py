"""Minimal MercadoLibre search client: raw httpx, no SDK, 429 backoff.
Usage:
    MELI_TOKEN=APP_USR-... python meli_search.py "mouse inalambrico" --site MLC --limit 20
    python meli_search.py "audifonos bluetooth" --site MLC --limit 20 --no-token
"""
import argparse, os, sys, time, random
import httpx

BASE = "https://api.mercadolibre.com"

def meli_get(path, params=None, token=None, retries=4):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    last = None
    for attempt in range(retries):
        try:
            r = httpx.get(f"{BASE}{path}", params=params or {}, headers=headers, timeout=20)
            if r.status_code == 429:
                wait = float(r.headers.get("Retry-After", 2 ** attempt)) + random.uniform(0, 0.5)
                time.sleep(wait)
                last = r
                continue
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            last = e
            if e.response is not None and e.response.status_code in (429, 500, 502, 503):
                time.sleep(2 ** attempt + random.uniform(0, 0.5))
                continue
            raise
    raise last

def search(site, query, limit=20, token=None, extra=None):
    params = {"q": query, "limit": limit}
    if extra:
        params.update(extra)
    data = meli_get(f"/sites/{site}/search", params=params, token=token)
    for it in data.get("results", []):
        price = it.get("price")
        orig = it.get("original_price")
        disc = round((orig - price) / orig * 100, 1) if orig and orig > price else 0.0
        print(f"{it.get('id')} | {price} ({disc}% off) | sold={it.get('sold_quantity')} | {it.get('title', '')[:90]}")
        print(f"  {it.get('permalink', '')}")
    print(f"\navailable_sorts={[s.get('id') for s in data.get('available_sorts', [])]}", file=sys.stderr)
    filt_ids = [f.get('id') for f in data.get('available_filters', [])]
    print(f"available_filters={filt_ids}", file=sys.stderr)
    return data

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--site", default="MLC")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--no-token", action="store_true")
    ap.add_argument("--category", default=None)
    args = ap.parse_args()
    token = None if args.no_token else os.getenv("MELI_TOKEN")
    extra = {}
    if args.category:
        extra["category"] = args.category
    try:
        search(args.site, args.query, limit=args.limit, token=token, extra=extra)
    except httpx.HTTPStatusError as e:
        code = e.response.status_code if e.response is not None else "?"
        body = (e.response.text[:500] if e.response is not None else "")
        print(f"HTTP {code}: {body}", file=sys.stderr)
        print("Hint: set MELI_TOKEN=APP_USR-... (current docs show Bearer on search; anonymous may 403).", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
