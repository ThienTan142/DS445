"""
Crawl public Shopee product reviews into a reproducible sentiment dataset.

Output schema:
    review_text, rating, label, shop_id, item_id, product_url, ctime

Usage:
    python data_collection/shopee_reviews_crawler.py ^
        --urls https://shopee.vn/some-product-i.123.456 ^
        --out data/shopee_reviews.csv ^
        --limit-per-product 100

    python data_collection/shopee_reviews_crawler.py ^
        --urls-file data/product_urls.txt ^
        --out data/shopee_reviews.csv

Notes:
    - Use only for public reviews and respect Shopee's terms, robots.txt, and rate limits.
    - Do not collect personal data that is not needed for sentiment analysis.
    - Shopee endpoints can change; if API calls fail, use the error message to update
      the endpoint/parameters or switch to browser-based collection for your own pages.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, urlencode, urlparse

import requests


SHOPEE_RATING_ENDPOINTS = {
    "vn": [
        "https://shopee.vn/api/v2/item/get_ratings",
        "https://shopee.vn/api/v4/item/get_ratings",
    ],
    "sg": [
        "https://shopee.sg/api/v2/item/get_ratings",
        "https://shopee.sg/api/v4/item/get_ratings",
    ],
}

FIELDNAMES = [
    "target_product",
    "star_filter",
    "review_text",
    "rating",
    "label",
    "predicted_label",
    "shop_id",
    "shop_name",
    "item_id",
    "product_url",
    "ctime",
    "source_curl_file",
]


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


@dataclass(frozen=True)
class ProductRef:
    shop_id: int
    item_id: int
    url: str


@dataclass(frozen=True)
class CurlRequest:
    endpoint: str
    headers: dict[str, str]
    base_params: dict[str, str]
    cookie: str = ""


def rating_to_label(rating: int) -> str:
    """Map Shopee star rating to 3 sentiment labels."""
    if rating <= 2:
        return "negative"
    if rating == 3:
        return "neutral"
    return "positive"


def parse_product_ref(url: str) -> ProductRef:
    """
    Extract shop_id and item_id from common Shopee URL shapes.

    Supported examples:
        https://shopee.vn/ten-san-pham-i.123456.987654
        https://shopee.vn/product/123456/987654
    """
    parsed = urlparse(url.strip())
    clean_url = parsed.geturl()

    patterns = [
        r"(?:^|[-.])i\.(?P<shop_id>\d+)\.(?P<item_id>\d+)",
        r"/product/(?P<shop_id>\d+)/(?P<item_id>\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, clean_url)
        if match:
            return ProductRef(
                shop_id=int(match.group("shop_id")),
                item_id=int(match.group("item_id")),
                url=clean_url,
            )

    raise ValueError(
        "Không tìm thấy shop_id/item_id trong URL. "
        "Hãy dùng link dạng ...-i.<shop_id>.<item_id> hoặc /product/<shop_id>/<item_id>."
    )


def extract_cookie_value(cookie: str, key: str) -> str:
    """Extract one value from a browser Cookie header string."""
    prefix = f"{key}="
    for part in cookie.split(";"):
        part = part.strip()
        if part.startswith(prefix):
            return part[len(prefix) :]
    return ""


def build_headers(product_url: str, cookie: str = "") -> dict[str, str]:
    """Browser-like headers. Cookie is optional and should come from your own browser session."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": product_url,
        "Origin": "https://shopee.vn",
        "Sec-CH-UA": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "X-Requested-With": "XMLHttpRequest",
    }
    if cookie:
        headers["Cookie"] = cookie
        csrf_token = extract_cookie_value(cookie, "csrftoken")
        if csrf_token:
            headers["X-CSRFToken"] = csrf_token
    return headers


def unescape_windows_curl(value: str) -> str:
    """Undo common escaping produced by Chrome's 'Copy as cURL (cmd)'."""
    return (
        value.strip()
        .replace("^%", "%")
        .replace('^"', '"')
        .replace("^\\^", "")
        .replace("^", "")
    )


def load_curl_request(curl_file: str | None) -> CurlRequest | None:
    """Parse a Chrome 'Copy as cURL' request without printing secrets."""
    if not curl_file:
        return None

    lines = Path(curl_file).read_text(encoding="utf-8-sig").splitlines()
    url = ""
    headers: dict[str, str] = {}
    cookie = ""

    for raw_line in lines:
        line = raw_line.strip().lstrip("\ufeff")
        if not line:
            continue

        if line.lower().startswith("curl "):
            match = re.search(r'curl\s+\^?"(.+?)\^?"\s*\^?$', line)
            if match:
                url = unescape_windows_curl(match.group(1))
            continue

        if line.startswith("-H ") or line.startswith("--header "):
            match = re.search(r'(?:-H|--header)\s+\^?"(.+?)\^?"\s*\^?$', line)
            if not match:
                continue
            header = unescape_windows_curl(match.group(1))
            if ":" not in header:
                continue
            name, value = header.split(":", 1)
            headers[name.strip()] = value.strip()
            continue

        if line.startswith("-b ") or line.startswith("--cookie "):
            match = re.search(r'(?:-b|--cookie)\s+\^?"(.+?)\^?"\s*\^?$', line)
            if match:
                cookie = unescape_windows_curl(match.group(1))

    if not url:
        raise ValueError("Không đọc được URL get_ratings từ file cURL.")

    parsed = urlparse(url)
    endpoint = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    base_params = {
        key: values[-1]
        for key, values in parse_qs(parsed.query, keep_blank_values=True).items()
    }

    if cookie:
        headers["Cookie"] = cookie

    return CurlRequest(endpoint=endpoint, headers=headers, base_params=base_params, cookie=cookie)


def parse_int_param(params: dict[str, str], *names: str) -> int | None:
    """Parse an integer query parameter, tolerating copied cURL escape residue."""
    for name in names:
        value = params.get(name)
        if not value:
            continue
        match = re.search(r"\d+", str(value))
        if match:
            return int(match.group(0))
    return None


def product_ref_from_curl_request(curl_request: CurlRequest) -> ProductRef:
    """Infer Shopee product identity from a get_ratings cURL request."""
    shop_id = parse_int_param(curl_request.base_params, "shopid", "preferred_item_shop_id")
    item_id = parse_int_param(
        curl_request.base_params,
        "itemid",
        "preferred_item_id",
        "preferred_item_item_id",
    )

    if shop_id is None or item_id is None:
        raise ValueError("Không tìm thấy shopid/itemid trong file get_ratings cURL.")

    return ProductRef(
        shop_id=shop_id,
        item_id=item_id,
        url=f"https://shopee.vn/product/{shop_id}/{item_id}",
    )


def request_rating_page(
    endpoint: str,
    product: ProductRef,
    offset: int,
    limit: int,
    timeout: int,
    cookie: str = "",
    curl_request: CurlRequest | None = None,
) -> list[dict]:
    """Fetch one ratings page and return raw rating objects."""
    params = dict(curl_request.base_params) if curl_request else {
        "appid": product.shop_id,
        "exclude_filter": 1,
        "filter": 0,
        "filter_size": 0,
        "fold_filter": 0,
        "flag": 1,
        "itemid": product.item_id,
        "need_translation": 1,
        "preferred_item_id": product.item_id,
        "preferred_item_include_type": 1,
        "preferred_item_shop_id": product.shop_id,
        "relevant_reviews": "false",
        "request_source": 2,
        "shopid": product.shop_id,
        "tag_filter": "",
        "type": 0,
        "offset": offset,
        "limit": limit,
        "variation_filters": "",
    }
    params.update(
        {
            "itemid": str(product.item_id),
            "shopid": str(product.shop_id),
            "offset": str(offset),
            "limit": str(limit),
        }
    )
    if "preferred_item_id" in params:
        params["preferred_item_id"] = str(product.item_id)
    if "preferred_item_item_id" in params:
        params["preferred_item_item_id"] = str(product.item_id)
    if "preferred_item_shop_id" in params:
        params["preferred_item_shop_id"] = str(product.shop_id)

    headers = dict(curl_request.headers) if curl_request else build_headers(product.url, cookie=cookie)
    headers.setdefault("Referer", product.url)
    if curl_request and curl_request.cookie:
        cookie = curl_request.cookie
    if cookie and "Cookie" not in headers:
        headers["Cookie"] = cookie

    response = requests.get(
        curl_request.endpoint if curl_request else endpoint,
        params=params,
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()

    if isinstance(payload, dict) and payload.get("error") not in (None, 0) and not payload.get("data"):
        raise ValueError(
            f"Shopee API error={payload.get('error')}. "
            "Request cURL/cookie/token có thể đã hết hạn hoặc đang bị Shopee chặn."
        )

    data = payload.get("data") or {}
    ratings = data.get("ratings")
    if ratings is None:
        ratings = data.get("item_rating_summary", {}).get("ratings", [])
    if not isinstance(ratings, list):
        raise ValueError(f"Payload không có danh sách ratings hợp lệ: {payload.keys()}")
    return ratings


def normalize_rating(raw: dict, product: ProductRef) -> dict | None:
    """Convert one Shopee rating object to the sentiment dataset schema."""
    comment = (raw.get("comment") or "").strip()
    rating = raw.get("rating_star")

    if not comment or rating is None:
        return None

    rating_int = int(rating)
    return {
        "target_product": "",
        "star_filter": "",
        "review_text": comment,
        "rating": rating_int,
        "label": rating_to_label(rating_int),
        "predicted_label": "",
        "shop_id": product.shop_id,
        "shop_name": raw.get("shop_name", ""),
        "item_id": product.item_id,
        "product_url": product.url,
        "ctime": raw.get("ctime", ""),
        "source_curl_file": "",
    }


def crawl_product_reviews(
    product: ProductRef,
    region: str,
    limit_per_product: int,
    page_size: int,
    sleep_seconds: float,
    timeout: int,
    cookie: str = "",
    curl_request: CurlRequest | None = None,
) -> list[dict]:
    """Crawl reviews for one product, trying known Shopee rating endpoints."""
    endpoints = SHOPEE_RATING_ENDPOINTS.get(region)
    if not endpoints:
        raise ValueError(f"Region chưa hỗ trợ: {region}. Hiện có: {sorted(SHOPEE_RATING_ENDPOINTS)}")

    rows: list[dict] = []
    offset = 0
    endpoint_index = 0
    last_error: Exception | None = None

    while len(rows) < limit_per_product:
        page_limit = min(page_size, limit_per_product - len(rows))
        endpoint = endpoints[endpoint_index]

        try:
            ratings = request_rating_page(
                endpoint=endpoint,
                product=product,
                offset=offset,
                limit=page_limit,
                timeout=timeout,
                cookie=cookie,
                curl_request=curl_request,
            )
        except Exception as exc:
            last_error = exc
            endpoint_index += 1
            if endpoint_index >= len(endpoints):
                raise RuntimeError(
                    "Không crawl được review bằng endpoint công khai. "
                    "Shopee có thể đã đổi API, cần cookie hợp lệ, hoặc đang chặn request tự động."
                ) from last_error
            continue

        if not ratings:
            break

        for raw in ratings:
            row = normalize_rating(raw, product)
            if row:
                rows.append(row)

        offset += page_limit
        time.sleep(sleep_seconds + random.uniform(0, sleep_seconds / 2))

    return rows


def review_key(row: dict) -> tuple[str, str, str, str]:
    """Stable key for deduplicating repeated crawl runs."""
    return (
        str(row.get("shop_id", "")).strip(),
        str(row.get("item_id", "")).strip(),
        str(row.get("ctime", "")).strip(),
        str(row.get("review_text", "")).strip(),
    )


def read_csv_rows(path: Path) -> list[dict]:
    """Read existing review CSV if it exists."""
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def normalize_output_row(row: dict) -> dict:
    """Keep only expected output columns in a stable order."""
    return {field: row.get(field, "") for field in FIELDNAMES}


def merge_rows(existing_rows: Iterable[dict], new_rows: Iterable[dict]) -> tuple[list[dict], int]:
    """Merge rows and drop duplicates from repeated crawl runs."""
    merged: list[dict] = []
    seen: set[tuple[str, str, str, str]] = set()
    duplicate_count = 0

    for row in list(existing_rows) + list(new_rows):
        normalized = normalize_output_row(row)
        key = review_key(normalized)
        if key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
        merged.append(normalized)

    return merged, duplicate_count


def write_csv(rows: Iterable[dict], out_path: Path, append: bool = False) -> tuple[int, int]:
    """Write crawled reviews to CSV using UTF-8 BOM for Excel compatibility."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    existing_rows = read_csv_rows(out_path) if append else []
    merged_rows, duplicate_count = merge_rows(existing_rows, rows)

    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(merged_rows)

    return len(merged_rows), duplicate_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl public Shopee product reviews.")
    parser.add_argument("--urls", nargs="+", default=[], help="Danh sách URL sản phẩm Shopee.")
    parser.add_argument("--urls-file", help="File text chứa URL sản phẩm, mỗi dòng một URL.")
    parser.add_argument("--out", default="data/shopee_reviews.csv", help="File CSV đầu ra.")
    parser.add_argument("--region", default="vn", choices=sorted(SHOPEE_RATING_ENDPOINTS))
    parser.add_argument("--limit-per-product", type=int, default=100)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--sleep", type=float, default=1.5, help="Nghỉ giữa các request.")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--cookie", default="", help="Cookie Shopee lấy từ phiên trình duyệt của chính bạn.")
    parser.add_argument("--cookie-file", help="File text chứa cookie Shopee lấy từ trình duyệt của chính bạn.")
    parser.add_argument("--curl-file", help="File chứa request get_ratings từ Chrome: Copy as cURL.")
    parser.add_argument("--append", action="store_true", help="Gộp review mới vào file CSV hiện có và bỏ trùng.")
    args = parser.parse_args()

    urls = list(args.urls)
    if args.urls_file:
        urls_file = Path(args.urls_file)
        file_urls = [
            line.strip()
            for line in urls_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        urls.extend(file_urls)

    cookie = args.cookie.strip()
    if args.cookie_file:
        cookie = Path(args.cookie_file).read_text(encoding="utf-8").strip()
    if cookie.lower().startswith("cookie:"):
        cookie = cookie.split(":", 1)[1].strip()
    curl_request = load_curl_request(args.curl_file)
    if curl_request and curl_request.cookie:
        cookie = curl_request.cookie
    if not urls and curl_request:
        product = product_ref_from_curl_request(curl_request)
        urls.append(product.url)

    if not urls:
        parser.error("Cần truyền --urls/--urls-file hoặc --curl-file chứa get_ratings.")

    all_rows: list[dict] = []
    for url in urls:
        product = parse_product_ref(url)
        print(f"Crawling item_id={product.item_id}, shop_id={product.shop_id} ...")
        rows = crawl_product_reviews(
            product=product,
            region=args.region,
            limit_per_product=args.limit_per_product,
            page_size=args.page_size,
            sleep_seconds=args.sleep,
            timeout=args.timeout,
            cookie=cookie,
            curl_request=curl_request,
        )
        print(f"  -> {len(rows)} reviews có text")
        all_rows.extend(rows)

    out_path = Path(args.out)
    total_rows, duplicate_count = write_csv(all_rows, out_path, append=args.append)
    print(f"Đã crawl {len(all_rows)} reviews mới")
    print(f"Đã bỏ {duplicate_count} reviews trùng")
    print(f"File CSV hiện có {total_rows} reviews: {out_path}")


if __name__ == "__main__":
    main()
