# Evaluation Summary

Model:

```text
models\ckpt_03_shopee_absa_vietnamese
```

Data:

```text
data\shopee_vietnamese_absa_sentiment.csv
split_col=split
eval_split=test
include_sources=all
```

Metrics:

```text
Accuracy: 0.7692
Macro F1: 0.7050
Weighted F1: 0.7769
Samples: 2335
Errors: 539
```

True label counts:

```text
label
positive    1499
neutral      605
negative     231
```

Predicted label counts:

```text
predicted_label
positive    1344
neutral      640
negative     351
```

Classification report:

```text
              precision    recall  f1-score   support

    negative       0.54      0.82      0.65       231
     neutral       0.57      0.61      0.59       605
    positive       0.92      0.83      0.87      1499

    accuracy                           0.77      2335
   macro avg       0.68      0.75      0.70      2335
weighted avg       0.79      0.77      0.78      2335

```
