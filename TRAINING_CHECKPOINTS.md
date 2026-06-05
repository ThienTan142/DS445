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
complete
```

Data da tao:

```text
Rows: 50,649
positive: 23,040
negative: 21,949
neutral: 5,660
Train sample khi fine-tune: 500 moi nhan
Accuracy: 0.6969
Macro F1: 0.6911
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
complete
```

Data da tao:

```text
Rows: 12,395
negative: 6,657
positive: 4,756
neutral: 982
Train sample khi fine-tune: 500 moi nhan
Accuracy: 0.6253
Macro F1: 0.5681
Negative F1: 0.69
Neutral F1: 0.31
Positive F1: 0.71
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
complete
```

Data da tao:

```text
Rows: 11,682
positive: 7,594
neutral: 2,985
negative: 1,103
Train sample khi fine-tune: 500 moi nhan
Accuracy: 0.7692
Macro F1: 0.7050
Negative F1: 0.65
Neutral F1: 0.59
Positive F1: 0.87
```
