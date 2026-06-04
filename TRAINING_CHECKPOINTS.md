# Training Checkpoints

Pipeline fine-tune nhieu nganh:

```text
PhoBERT-base
-> ckpt_01_general_sentiment
-> ckpt_02_ecommerce_multidomain
-> ckpt_03_shopee_absa_vietnamese
```

## Checkpoint 01: General Vietnamese Sentiment

Path:

```text
models/ckpt_01_general_sentiment
```

Muc dich:

```text
Giup PhoBERT hoc cam xuc tieng Viet tong quat truoc khi hoc review san pham.
```

Dataset:

```text
data/general_vietnamese_sentiment.csv
```

Nguon:

```text
UIT-VSFC
h-i-e-u/vietnamese-SA-dataset
```

Trang thai:

```text
pending
```

## Checkpoint 02: E-commerce Multi-domain Sentiment

Path:

```text
models/ckpt_02_ecommerce_multidomain
```

Muc dich:

```text
Giup model quen voi ngon ngu review san pham/dich vu nhieu nganh:
giao hang, chat luong, dong goi, gia ca, khieu nai, trai nghiem mua hang.
```

Dataset:

```text
data/ecommerce_multidomain_sentiment.csv
```

Nguon:

```text
ViOCD
CausaSent/Tiki
```

Trang thai:

```text
pending
```

## Checkpoint 03: Shopee ABSA Vietnamese

Path:

```text
models/ckpt_03_shopee_absa_vietnamese
```

Muc dich:

```text
Dieu chinh model ve domain Shopee tieng Viet va aspect sentiment.
```

Dataset:

```text
data/shopee_vietnamese_absa_sentiment.csv
```

Nguon:

```text
Kaggle ABSA Vietnamese - Shopee shoe reviews
```

Trang thai:

```text
pending
```
