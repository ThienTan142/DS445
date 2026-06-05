export const examples = [
  {
    id: 'cosmetic-mixed',
    title: 'Mỹ phẩm mixed-sentiment',
    text: 'Kem chống nắng thấm nhanh, nâng tone nhẹ nhưng hơi bí da nếu bôi nhiều.',
    expected: 'Neutral'
  },
  {
    id: 'audio-negative',
    title: 'Điện tử tiêu cực',
    text: 'Tai nghe giao nhanh nhưng mic rè, pin yếu và âm thanh bị delay.',
    expected: 'Negative'
  },
  {
    id: 'shipping-positive',
    title: 'Dịch vụ tích cực',
    text: 'Shop tư vấn nhiệt tình, đóng gói cẩn thận, sản phẩm dùng ổn so với giá.',
    expected: 'Positive'
  },
  {
    id: 'shoe-neutral',
    title: 'Shopee ABSA neutral',
    text: 'Giày đẹp, form chuẩn nhưng giao hàng hơi lâu và hộp bị móp.',
    expected: 'Neutral'
  },
  {
    id: 'quality-positive',
    title: 'Chất lượng tích cực',
    text: 'Sản phẩm rất đẹp, đúng mô tả, giá hợp lý, lần sau sẽ ủng hộ shop tiếp.',
    expected: 'Positive'
  },
  {
    id: 'price-negative',
    title: 'Giá và chất lượng tiêu cực',
    text: 'Hàng không đúng mẫu, chất lượng kém, giá lại mắc hơn nhiều shop khác.',
    expected: 'Negative'
  }
];
