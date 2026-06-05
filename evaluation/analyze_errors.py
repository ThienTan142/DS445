"""
Create a compact error analysis report from PhoBERT evaluation predictions.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def format_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "No rows"
    return df.to_markdown(index=False)


def shorten(value: object, max_len: int = 160) -> str:
    text = "" if pd.isna(value) else str(value)
    text = " ".join(text.split())
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze sentiment model errors.")
    parser.add_argument("--predictions", default="reports/evaluation/ckpt_03_shopee_absa_vietnamese/predictions.csv")
    parser.add_argument("--out", default="reports/evaluation/ckpt_03_shopee_absa_vietnamese/error_analysis.md")
    parser.add_argument("--top-n", type=int, default=12)
    args = parser.parse_args()

    df = pd.read_csv(args.predictions, encoding="utf-8-sig")
    if "is_correct" not in df.columns:
        df["is_correct"] = df["label"].eq(df["predicted_label"])
    errors = df[~df["is_correct"]].copy()

    pair_counts = (
        errors.groupby(["label", "predicted_label"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    aspect_counts = pd.DataFrame()
    if "aspect" in errors.columns:
        exploded = errors.assign(aspect=errors["aspect"].fillna("").astype(str).str.split(",")).explode("aspect")
        exploded["aspect"] = exploded["aspect"].str.strip()
        aspect_counts = (
            exploded[exploded["aspect"].ne("")]
            .groupby("aspect")
            .size()
            .reset_index(name="error_count")
            .sort_values("error_count", ascending=False)
            .head(args.top_n)
        )

    source_counts = pd.DataFrame()
    if "source" in errors.columns:
        source_counts = (
            errors.groupby("source")
            .size()
            .reset_index(name="error_count")
            .sort_values("error_count", ascending=False)
            .head(args.top_n)
        )

    high_conf_cols = ["review_text", "label", "predicted_label", "confidence", "aspect"]
    high_conf_cols = [col for col in high_conf_cols if col in errors.columns]
    high_conf = errors.sort_values("confidence", ascending=False).head(args.top_n)[high_conf_cols].copy()
    if "review_text" in high_conf.columns:
        high_conf["review_text"] = high_conf["review_text"].map(shorten)

    mixed_examples = pd.DataFrame()
    if "aspect_labels" in errors.columns:
        mixed = errors[errors["aspect_labels"].astype(str).str.contains("negative", case=False, na=False)]
        mixed = mixed[mixed["aspect_labels"].astype(str).str.contains("positive", case=False, na=False)]
        mixed_cols = ["review_text", "label", "predicted_label", "confidence", "aspect_labels"]
        mixed_cols = [col for col in mixed_cols if col in mixed.columns]
        mixed_examples = mixed.sort_values("confidence", ascending=False).head(args.top_n)[mixed_cols].copy()
        if "review_text" in mixed_examples.columns:
            mixed_examples["review_text"] = mixed_examples["review_text"].map(shorten)

    report = f"""# Error Analysis

Input predictions:

```text
{args.predictions}
```

Total samples: {len(df)}
Correct samples: {int(df["is_correct"].sum())}
Error samples: {len(errors)}
Error rate: {len(errors) / len(df):.4f}

## Confusion Pairs

{format_table(pair_counts)}

## Error Counts By Aspect

{format_table(aspect_counts)}

## Error Counts By Source

{format_table(source_counts)}

## High-confidence Errors

{format_table(high_conf)}

## Mixed-aspect Error Examples

{format_table(mixed_examples)}

## Notes For Report

- Nhom loi lon nhat thuong la `positive -> neutral` va `neutral -> negative/positive`.
- Nhieu cau co ngon ngu rat tich cuc nhung bi gan nhan `neutral` do cach collapse nhan aspect hoac annotation co nhan `Others`.
- Cac cau mixed-sentiment nhu vua khen san pham vua che gia/size/giao hang de lam model nham giua `neutral` va mot nhan cuc tinh.
- F1 cua `neutral` thap hon `positive` vi neutral la lop kho: vua co cau trung lap that su, vua co cau mixed-aspect.
"""

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Saved error analysis: {out_path}")


if __name__ == "__main__":
    main()
