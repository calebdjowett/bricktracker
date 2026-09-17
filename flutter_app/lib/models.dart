class CollectionItem {
  const CollectionItem({required this.id, required this.setId, required this.setNumber, required this.name, required this.theme, required this.quantity, required this.condition, required this.purchasePriceCents, required this.currentValueCents, required this.gainLossCents, required this.gainLossPercent, required this.averageNewPriceCents, required this.averageUsedPriceCents});

  final int id;
  final int setId;
  final String setNumber;
  final String name;
  final String theme;
  final int quantity;
  final String condition;
  final int purchasePriceCents;
  final int currentValueCents;
  final int gainLossCents;
  final double? gainLossPercent;
  final int? averageNewPriceCents;
  final int? averageUsedPriceCents;

  factory CollectionItem.fromJson(Map<String, dynamic> json) => CollectionItem(
    id: json['id'], setId: json['set_id'], setNumber: json['set_number'], name: json['name'], theme: json['theme'], quantity: json['quantity'], condition: json['condition'], purchasePriceCents: json['purchase_price_cents'], currentValueCents: json['current_value_cents'], gainLossCents: json['gain_loss_cents'], gainLossPercent: (json['gain_loss_percent'] as num?)?.toDouble(), averageNewPriceCents: json['average_new_price_cents'], averageUsedPriceCents: json['average_used_price_cents'],
  );
}

class DashboardData {
  const DashboardData({required this.valueCents, required this.profitLossCents, required this.bestPerforming});
  final int valueCents;
  final int profitLossCents;
  final List<CollectionItem> bestPerforming;
  factory DashboardData.fromJson(Map<String, dynamic> json) => DashboardData(valueCents: json['collection_value_cents'], profitLossCents: json['profit_loss_cents'], bestPerforming: (json['best_performing_sets'] as List).map((item) => CollectionItem.fromJson(item)).toList());
}
