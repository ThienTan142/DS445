export default function AboutModelPage() {
  return (
    <div className="page-stack">
      <section className="page-header">
        <span className="eyebrow">Model card</span>
        <h1>PhoBERT sentiment analysis</h1>
        <p>Mô hình phân tích cảm xúc bình luận thương mại điện tử tiếng Việt, tối ưu cho demo đồ án tốt nghiệp.</p>
      </section>

      <div className="info-grid">
        <InfoBlock title="Mục tiêu bài toán">
          Phân loại bình luận sản phẩm/dịch vụ thành ba nhãn: Positive, Neutral và Negative.
        </InfoBlock>
        <InfoBlock title="Dữ liệu sử dụng">
          UIT-VSFC, Vietnamese SA, ViOCD, CausaSent/Tiki và Kaggle ABSA Vietnamese Shopee shoe reviews.
        </InfoBlock>
        <InfoBlock title="Quy trình xử lý">
          Chuẩn hóa schema, collapse aspect labels, word segmentation bằng underthesea, tokenizer PhoBERT, fine-tune 3 checkpoint.
        </InfoBlock>
        <InfoBlock title="Model">
          PhoBERT-base fine-tuned theo ba tầng: sentiment tổng quát, e-commerce multi-domain và Shopee ABSA tiếng Việt.
        </InfoBlock>
        <InfoBlock title="Metric đánh giá">
          Checkpoint cuối đạt Accuracy 0.7692, Macro F1 0.7050, Weighted F1 0.7769 trên test set Shopee ABSA.
        </InfoBlock>
        <InfoBlock title="Hạn chế">
          Lớp Neutral khó do mixed-sentiment; dữ liệu Shopee ABSA chủ yếu là giày; sarcasm và teencode vẫn có thể gây lỗi.
        </InfoBlock>
        <InfoBlock title="Hướng phát triển">
          Bổ sung dữ liệu nhiều ngành hơn, thêm aspect-level prediction, calibration confidence và pipeline shop ranking có link Shopee.
        </InfoBlock>
      </div>
    </div>
  );
}

function InfoBlock({ title, children }) {
  return (
    <section className="panel info-block">
      <h2>{title}</h2>
      <p>{children}</p>
    </section>
  );
}
