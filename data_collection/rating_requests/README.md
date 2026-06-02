# Rating Requests

Moi file `.txt` tuong ung voi mot san pham tu mot shop.

Quy trinh:

1. Mo trang san pham Shopee.
2. Keo xuong phan danh gia.
3. `F12` -> `Network` -> `Fetch/XHR`.
4. Loc `get_ratings`.
5. Chuot phai request `get_ratings`.
6. Chon `Copy -> Copy as cURL (cmd)`.
7. Dan vao file `.txt` tuong ung.

Vi du:

```text
01_kem_chong_nang/shop_01.txt
01_kem_chong_nang/shop_02.txt
...
01_kem_chong_nang/shop_10.txt
```

Moi nhom san pham chi can `shop_01.txt` den `shop_10.txt`.
Crawler chi doc cac file duoc khai bao trong `data_collection/product_urls.csv`.

Khong commit hoac chia se cac file `.txt` vi chung co the chua cookie/token phien duyet.
