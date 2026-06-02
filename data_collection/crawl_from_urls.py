"""
Crawl Shopee reviews from product URLs.

Input CSV:
    data_collection/product_urls.csv

Required columns:
    target_product

Optional columns:
    product_url, shop_name, rating_curl_file

Output CSV:
    data/shopee_reviews_all.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

from shopee_reviews_crawler import (
    crawl_product_reviews,
    load_curl_request,
    parse_product_ref,
    product_ref_from_curl_request,
    write_csv,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def read_targets(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    required = {"target_product"}
    missing = required - set(rows[0].keys() if rows else [])
    if missing:
        raise ValueError(f"Input CSV thiếu cột: {sorted(missing)}")

    return [
        row
        for row in rows
        if row.get("target_product", "").strip()
        and (row.get("product_url", "").strip() or row.get("rating_curl_file", "").strip())
    ]


def attach_metadata(rows: list[dict], target: dict) -> list[dict]:
    for row in rows:
        row["target_product"] = target.get("target_product", "").strip()
        row["shop_name"] = target.get("shop_name", "").strip()
        row["star_filter"] = "all"
        row["source_curl_file"] = target.get("rating_curl_file", "").strip()
    return rows


def load_row_curl_request(target: dict):
    curl_file = target.get("rating_curl_file", "").strip()
    if not curl_file:
        return None
    path = Path(curl_file)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy rating_curl_file: {path}")
    content = path.read_text(encoding="utf-8", errors="ignore").lower()
    if "get_ratings" not in content or "curl" not in content:
        return None
    return load_curl_request(str(path))


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl Shopee reviews from product URL CSV.")
    parser.add_argument("--input", default="data_collection/product_urls.csv")
    parser.add_argument("--out", default="data/shopee_reviews_all.csv")
    parser.add_argument("--cookie-file", help="Optional Shopee browser cookie file.")
    parser.add_argument("--limit-per-product", type=int, default=100)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--sleep", type=float, default=2.0)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    cookie = ""
    if args.cookie_file:
        cookie = Path(args.cookie_file).read_text(encoding="utf-8").strip()
        if cookie.lower().startswith("cookie:"):
            cookie = cookie.split(":", 1)[1].strip()

    targets = read_targets(Path(args.input))
    if not targets:
        raise SystemExit(f"Chưa có URL hợp lệ trong {args.input}")

    total_new_rows = 0
    out_path = Path(args.out)

    for index, target in enumerate(targets, start=1):
        curl_request = load_row_curl_request(target)
        if target.get("product_url", "").strip():
            product = parse_product_ref(target["product_url"])
        elif curl_request is not None:
            product = product_ref_from_curl_request(curl_request)
        else:
            print(f"[{index}/{len(targets)}] bỏ qua: chưa có product_url hoặc cURL get_ratings hợp lệ")
            continue

        print(f"[{index}/{len(targets)}] {target['target_product']} - item_id={product.item_id}, shop_id={product.shop_id}")

        try:
            rows = crawl_product_reviews(
                product=product,
                region="vn",
                limit_per_product=args.limit_per_product,
                page_size=args.page_size,
                sleep_seconds=args.sleep,
                timeout=args.timeout,
                cookie=cookie,
                curl_request=curl_request,
            )
        except Exception as exc:
            print(f"  -> lỗi: {type(exc).__name__}: {exc}")
            continue

        rows = attach_metadata(rows, target)
        total_new_rows += len(rows)
        total_rows, duplicate_count = write_csv(rows, out_path, append=True)
        print(f"  -> crawl {len(rows)} reviews, bỏ {duplicate_count} trùng, file có {total_rows} reviews")
        time.sleep(args.sleep)

    print(f"Hoàn tất. Tổng reviews mới trong lượt chạy: {total_new_rows}")
    print(f"File dữ liệu: {out_path}")


if __name__ == "__main__":
    main()
