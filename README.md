# DS445

De tai:

```text
Phan tich cam xuc va khia canh binh luan Shopee tieng Viet bang PhoBERT-base
```

Pipeline moi khong crawl Shopee:

```text
download Kaggle ABSA Vietnamese
-> chuan hoa Review + aspect labels thanh 3 nhan sentiment
-> fine-tune PhoBERT-base
-> danh gia bang Accuracy, Macro F1, Confusion Matrix
-> dung model de du doan sentiment cho review moi
```

Dataset chinh:

```text
data/raw/absa_vietnamese/train_data.csv
data/raw/absa_vietnamese/val_data.csv
data/raw/absa_vietnamese/test_data.csv
data/shopee_vietnamese_absa_sentiment.csv
```

Model hien tai:

```text
models/phobert_absa_shopee_vietnamese
```

Chay lai pipeline:

```powershell
.\activate_project.ps1

curl.exe -L "https://www.kaggle.com/api/v1/datasets/download/cthng123/absa-vietnamese" `
  -o data\raw\absa-vietnamese.zip

Expand-Archive -LiteralPath data\raw\absa-vietnamese.zip `
  -DestinationPath data\raw\absa_vietnamese -Force

python data_collection\prepare_absa_vietnamese.py `
  --raw-dir data\raw\absa_vietnamese `
  --out data\shopee_vietnamese_absa_sentiment.csv

python modeling\train_phobert.py `
  --data data\shopee_vietnamese_absa_sentiment.csv `
  --model-name vinai/phobert-base `
  --output-dir models\phobert_absa_shopee_vietnamese `
  --text-col review_text `
  --include-sources kaggle_absa_vietnamese_shopee `
  --split-col split `
  --train-splits train,val `
  --eval-split test `
  --train-max-per-label 500 `
  --epochs 1 `
  --batch-size 4 `
  --max-length 128
```

Ket qua lan chay hien tai:

```text
Train: 1,500 review can bang, 500 moi nhan
Test: 2,335 review
Accuracy: 0.7537
Macro F1: 0.6857
```

Ghi chu: Kaggle ABSA Vietnamese co nhan theo aspect. Script
`prepare_absa_vietnamese.py` collapse cac nhan aspect thanh sentiment tong quat:
negative, neutral, positive.
