# Error Analysis

Input predictions:

```text
reports\evaluation\ckpt_03_shopee_absa_vietnamese\predictions.csv
```

Total samples: 2335
Correct samples: 1796
Error samples: 539
Error rate: 0.2308

## Confusion Pairs

| label    | predicted_label   |   count |
|:---------|:------------------|--------:|
| positive | neutral           |     234 |
| neutral  | negative          |     134 |
| neutral  | positive          |     103 |
| negative | neutral           |      38 |
| positive | negative          |      27 |
| negative | positive          |       3 |

## Error Counts By Aspect

| aspect       |   error_count |
|:-------------|--------------:|
| Outlook      |           264 |
| General      |           152 |
| Quality      |           141 |
| Shop_Service |           119 |
| Size         |           118 |
| Shipping     |           114 |
| Price        |            64 |
| Others       |            59 |

## Error Counts By Source

| source                        |   error_count |
|:------------------------------|--------------:|
| kaggle_absa_vietnamese_shopee |           539 |

## High-confidence Errors

| review_text                                                                                              | label    | predicted_label   |   confidence | aspect                |
|:---------------------------------------------------------------------------------------------------------|:---------|:------------------|-------------:|:----------------------|
| sản phẩm giá mềm, đáng mua nha các bạn, con mình thích lắm và sẽ ủng hộ shop lâu dài                     | neutral  | positive          |     0.955755 | General               |
| Giày đẹp lắm. Rất hài lòng. Sẽ ủng hộ thêm                                                               | neutral  | positive          |     0.952078 | Outlook               |
| Chuẩn tốt phù hợp giá tiền                                                                               | neutral  | positive          |     0.951624 | General               |
| Hàng cx ổn nên mua nha mnguoi giá cả hợp lí 👍                                                           | neutral  | positive          |     0.951285 | General               |
| giày đúng đẹp y hình form chuẩn nma khong có hộp nchung nên mua nhé                                      | neutral  | positive          |     0.94945  | Outlook,Shop_Service  |
| Kg đẹp mọi ng lên mua                                                                                    | negative | positive          |     0.947165 | Outlook               |
| Giá cả hợp lí                                                                                            | neutral  | positive          |     0.943588 | Price                 |
| chất lượng sản phẩm khá tốt mọi người nên mua nhé hh                                                     | neutral  | positive          |     0.943263 | Quality               |
| Chất đẹp nhé nên mua nha mọi ng nhìn ở ngoài đẹp lắm ạ kkk                                               | negative | positive          |     0.943008 | Outlook               |
| Dây ko đúng mẫu                                                                                          | neutral  | negative          |     0.942431 | Others                |
| Sản phẩm ok giao hàng cũng nhanh                                                                         | neutral  | positive          |     0.94222  | Shipping,General      |
| Sản phẩm đẹp,giày mang êm chân,đáng để mua,mà giá hơi mắc hơn chỗ khác nhưng đổi lại hàng chất lượng tốt | neutral  | positive          |     0.942051 | Price,Outlook,Quality |

## Mixed-aspect Error Examples

| review_text                                                                                                                           | label   | predicted_label   |   confidence | aspect_labels                                                                                   |
|:--------------------------------------------------------------------------------------------------------------------------------------|:--------|:------------------|-------------:|:------------------------------------------------------------------------------------------------|
| giày đúng đẹp y hình form chuẩn nma khong có hộp nchung nên mua nhé                                                                   | neutral | positive          |     0.94945  | {"Outlook": "positive", "Shop_Service": "negative"}                                             |
| Sản phẩm đẹp,giày mang êm chân,đáng để mua,mà giá hơi mắc hơn chỗ khác nhưng đổi lại hàng chất lượng tốt                              | neutral | positive          |     0.942051 | {"Outlook": "positive", "Price": "negative", "Quality": "positive"}                             |
| Giày đẹp, giao hàng nhanh , shop nhiệt tình , khuyên mấy bạn nên đặt hơn 2 size nha mang cho ko bị đau chân tại from này cực kì nhỏ ạ | neutral | positive          |     0.938075 | {"Outlook": "positive", "Shipping": "positive", "Shop_Service": "positive", "Size": "negative"} |
| Giao hàng nhanh chất da không đẹp lắm from giầy hơi xấu                                                                               | neutral | negative          |     0.932392 | {"Outlook": "negative", "Shipping": "positive"}                                                 |
| Giày giống như hình nhưg mà pị trầy vs lại dính đóm đỏ trên giày ko pít đó là gì                                                      | neutral | negative          |     0.93136  | {"Outlook": "negative", "Shop_Service": "positive"}                                             |
| Giày đẹp lắm nha mọi người mang êm chân lắm vì ở xa nên ship hoi lâu                                                                  | neutral | positive          |     0.927713 | {"Outlook": "positive", "Quality": "positive", "Shipping": "negative"}                          |
| Đẹp, chuẩn size, ko hộp.                                                                                                              | neutral | positive          |     0.926626 | {"Outlook": "positive", "Shop_Service": "negative", "Size": "positive"}                         |
| Đi thì cx xing lắm ẹ đi đúng size ạ điểm trừ là nhìn nó cx hơi nát nát ở những phần xỏ dây thui                                       | neutral | negative          |     0.923999 | {"Outlook": "positive", "Quality": "negative", "Size": "positive"}                              |
| Dán keo bị lỗi , vài vết bẩn nhỏ , có chỉ thừa, giày cứng , form ko đẹp mua loại cc nhưng vẫn chưa ưng lắm đc cái giao hàng nhanh.    | neutral | negative          |     0.916457 | {"Outlook": "negative", "Quality": "negative", "Shipping": "positive"}                          |
| hàng oke mà không biết như nào bên ngoài trông k ưng lắm nó sao á                                                                     | neutral | negative          |     0.914846 | {"General": "positive", "Outlook": "negative"}                                                  |
| Đóng gói sơ sài tiền nào của đó cx êm                                                                                                 | neutral | negative          |     0.914125 | {"Price": "neutral", "Quality": "positive", "Shop_Service": "negative"}                         |
| Giày đẹp nha, chắc chắn , nhẹ vừa chân , tuy giao hàng khá là lâu nhưng nhận thì không thất vọng nha !                                | neutral | positive          |     0.912736 | {"Outlook": "positive", "Quality": "positive", "Shipping": "negative"}                          |

## Notes For Report

- Nhom loi lon nhat thuong la `positive -> neutral` va `neutral -> negative/positive`.
- Nhieu cau co ngon ngu rat tich cuc nhung bi gan nhan `neutral` do cach collapse nhan aspect hoac annotation co nhan `Others`.
- Cac cau mixed-sentiment nhu vua khen san pham vua che gia/size/giao hang de lam model nham giua `neutral` va mot nhan cuc tinh.
- F1 cua `neutral` thap hon `positive` vi neutral la lop kho: vua co cau trung lap that su, vua co cau mixed-aspect.
