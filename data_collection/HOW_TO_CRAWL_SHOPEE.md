# Crawl Review Shopee Bang URL

Flow moi:

```text
nhap URL san pham cua tung shop
-> crawl tat ca binh luan ben duoi
-> gan label ban dau tu rating
-> model du doan sentiment
-> rerank shop theo predicted_label
```

## 1. Dien URL dau vao

Mo file:

```text
data_collection/product_urls.csv
```

Minh da tao san 50 dong cho 5 vat pham, moi vat pham 10 shop:

```text
kem chong nang
tai nghe bluetooth
den led
ao thun nu
may xay mini
```

Moi dong tro toi mot file `.txt` trong:

```text
data_collection/rating_requests
```

Neu ban muon crawl bang URL cong khai, dien `product_url` va `shop_name`:

```csv
target_product,product_url,shop_name,rating_curl_file
kem chong nang,https://shopee.vn/product/<shop_id>/<item_id>,Ten shop A,
kem chong nang,https://shopee.vn/product/<shop_id>/<item_id>,Ten shop B,
tai nghe bluetooth,https://shopee.vn/product/<shop_id>/<item_id>,Ten shop C,
```

Luu y: review nam duoi trang san pham, nen URL can la URL san pham co `shop_id/item_id`,
khong phai trang profile shop chung chung.

## 2. Crawl tat ca review

```powershell
cd F:\DS445
.\activate_project.ps1

python data_collection\crawl_from_urls.py `
  --input data_collection\product_urls.csv `
  --out data\shopee_reviews_all.csv `
  --limit-per-product 30 `
  --page-size 6 `
  --sleep 6
```

## 3. Neu Shopee tra 403

Thu cach cookie truoc. Lay cookie tu trinh duyet cua ban va chay them:

```powershell
python data_collection\crawl_from_urls.py `
  --input data_collection\product_urls.csv `
  --out data\shopee_reviews_all.csv `
  --cookie-file data_collection\shopee_cookie.txt `
  --limit-per-product 30 `
  --page-size 6 `
  --sleep 6
```

Neu van bi `403 Forbidden`, dung cach chac an hon: copy request `get_ratings` cua dung san pham.

Trong Chrome/Edge:

```text
F12 -> Network -> Fetch/XHR -> loc get_ratings
```

Sau do:

```text
chuot phai request get_ratings -> Copy -> Copy as cURL (cmd)
```

Tao file trong:

```text
data_collection/rating_requests
```

Vi du:

```text
data_collection/rating_requests/01_kem_chong_nang/shop_01.txt
```

Dan toan bo cURL vao file do. `product_urls.csv` da co san duong dan file; ban chi can dien them `shop_name` neu muon hien ten shop.

```csv
target_product,product_url,shop_name,rating_curl_file
kem chong nang,,Ten shop A,data_collection/rating_requests/01_kem_chong_nang/shop_01.txt
```

Chay lai lenh crawl:

```powershell
python data_collection\crawl_from_urls.py `
  --input data_collection\product_urls.csv `
  --out data\shopee_reviews_all.csv `
  --limit-per-product 30 `
  --page-size 6 `
  --sleep 6
```

## 4. Kiem tra du lieu

```powershell
python -c "import pandas as pd; df=pd.read_csv('data/shopee_reviews_all.csv'); print(df.shape); print(df[['target_product','shop_id','rating','label']].head())"
```

Cot quan trong:

```text
target_product, review_text, rating, label, predicted_label,
shop_id, shop_name, item_id, product_url, ctime
```
