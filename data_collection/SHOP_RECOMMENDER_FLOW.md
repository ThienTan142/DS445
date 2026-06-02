# Shop Recommender Flow

Muc tieu:

```text
crawl data
-> gan label ban dau tu rating
-> model hoc dac trung review va du doan sentiment tung binh luan
-> tong hop dac trung theo shop
-> phan tich shop thuoc loai nao
-> nhap ten vat pham can mua
-> dua ra cac lua chon shop tot nhat
```

## 1. Data Collection

Nhap URL san pham cua cac shop vao:

```text
data_collection/product_urls.csv
```

Format:

```csv
target_product,product_url,shop_name,rating_curl_file
kem chong nang,https://shopee.vn/product/<shop_id>/<item_id>,Ten shop A,
```

Neu bi `403 Forbidden`, copy `get_ratings` as cURL vao file `.txt` trong
`data_collection/rating_requests`, roi dien duong dan vao cot `rating_curl_file`.

Chay:

```powershell
python data_collection\crawl_from_urls.py `
  --input data_collection\product_urls.csv `
  --out data\shopee_reviews_all.csv `
  --limit-per-product 100
```

Output:

```text
data/shopee_reviews_all.csv
```

## 2. Sentiment Model

Train baseline model:

```powershell
python modeling\train_sentiment_model.py `
  --data data\shopee_reviews_all.csv `
  --model-out models\sentiment_tfidf_lr.joblib
```

Predict sentiment cho tung review:

```powershell
python modeling\predict_sentiment.py `
  --data data\shopee_reviews_all.csv `
  --model models\sentiment_tfidf_lr.joblib `
  --out data\shopee_reviews_scored.csv
```

Model se ghi ket qua vao cot:

```text
predicted_label
```

## 3. Rerank Va Goi Y Shop

Tao shop profile:

```powershell
python analysis\profile_shops.py `
  --reviews data\shopee_reviews_scored.csv `
  --out data\shop_profiles.csv `
  --min-reviews 5
```

File `shop_profiles.csv` gom cac dac trung theo `target_product + shop_id`:

```text
total_reviews, avg_rating, positive_rate, negative_rate,
sentiment_score, recommendation_score, shop_type
```

`shop_type` co cac nhom:

```text
rat_tot
tot_on_dinh
trung_tinh_can_can_nhac
can_can_nhac
rui_ro_cao
chua_du_du_lieu
```

Nhap ten vat pham:

```powershell
python analysis\recommend_shop.py `
  --query "kem chong nang" `
  --reviews data\shopee_reviews_scored.csv `
  --profiles data\shop_profiles.csv `
  --min-reviews 5
```

Output:

```text
data/recommended_shops.csv
```

Neu chua co model, script co the dung cot `label` tam thoi, nhung bao cao nen dung
`predicted_label` sau khi da train/predict.
