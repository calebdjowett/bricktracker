import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'api_client.dart';
import 'models.dart';

void main() => runApp(const BrickTrackerApp());

class BrickTrackerApp extends StatelessWidget {
  const BrickTrackerApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(title: 'BrickTracker', theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xffc43b2f), secondary: const Color(0xff006e5e)), useMaterial3: true), home: const HomeScreen());
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final api = BrickTrackerApi();
  int index = 0;
  @override
  Widget build(BuildContext context) {
    final pages = [DashboardScreen(api: api), CollectionScreen(api: api), RetirementScreen(api: api), AnalyticsScreen(api: api)];
    return Scaffold(appBar: AppBar(title: const Text('BrickTracker')), body: pages[index], bottomNavigationBar: NavigationBar(selectedIndex: index, onDestinationSelected: (value) => setState(() => index = value), destinations: const [NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: 'Dashboard'), NavigationDestination(icon: Icon(Icons.inventory_2_outlined), selectedIcon: Icon(Icons.inventory_2), label: 'Collection'), NavigationDestination(icon: Icon(Icons.event_outlined), selectedIcon: Icon(Icons.event), label: 'Retiring'), NavigationDestination(icon: Icon(Icons.insights_outlined), selectedIcon: Icon(Icons.insights), label: 'Analytics')]));
  }
}

String money(int cents) => '\$${(cents / 100).toStringAsFixed(2)}';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key, required this.api});
  final BrickTrackerApi api;
  @override
  Widget build(BuildContext context) => FutureBuilder<DashboardData>(future: api.dashboard(), builder: (context, snapshot) {
    if (snapshot.hasError) return Center(child: Text('Could not load dashboard\n${snapshot.error}', textAlign: TextAlign.center));
    if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
    final data = snapshot.data!;
    return ListView(padding: const EdgeInsets.all(16), children: [Wrap(spacing: 12, runSpacing: 12, children: [Metric(label: 'Collection value', value: money(data.valueCents)), Metric(label: 'Profit / loss', value: money(data.profitLossCents), positive: data.profitLossCents >= 0)]), const SizedBox(height: 24), Text('Best performing sets', style: Theme.of(context).textTheme.titleLarge), ...data.bestPerforming.map(SetTile.new)]);
  });
}

class Metric extends StatelessWidget {
  const Metric({super.key, required this.label, required this.value, this.positive});
  final String label;
  final String value;
  final bool? positive;
  @override
  Widget build(BuildContext context) => SizedBox(width: 180, child: Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(label), Text(value, style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: positive == null ? null : positive! ? Colors.teal.shade700 : Colors.red.shade700))]))));
}

class SetTile extends StatelessWidget {
  const SetTile(this.item, {super.key});
  final CollectionItem item;
  @override
  Widget build(BuildContext context) => ListTile(contentPadding: const EdgeInsets.symmetric(vertical: 4), title: Text('${item.setNumber}  ${item.name}'), subtitle: Text('${item.theme} | ${item.quantity} owned | ${item.condition == 'sealed' ? 'New / Sealed' : 'Used / Built'}'), trailing: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.end, children: [Text(money(item.currentValueCents)), Text('${item.gainLossCents >= 0 ? '+' : ''}${money(item.gainLossCents)}', style: TextStyle(color: item.gainLossCents >= 0 ? Colors.teal.shade700 : Colors.red.shade700))]));
}

class CollectionScreen extends StatefulWidget { const CollectionScreen({super.key, required this.api}); final BrickTrackerApi api; @override State<CollectionScreen> createState() => _CollectionScreenState(); }
class _CollectionScreenState extends State<CollectionScreen> {
  @override Widget build(BuildContext context) => Scaffold(body: FutureBuilder<List<CollectionItem>>(future: widget.api.collection(), builder: (context, snapshot) { if (!snapshot.hasData) return const Center(child: CircularProgressIndicator()); return ListView(padding: const EdgeInsets.all(16), children: snapshot.data!.map(SetTile.new).toList()); }), floatingActionButton: FloatingActionButton(onPressed: () async { await showModalBottomSheet(context: context, isScrollControlled: true, builder: (_) => AddSetSheet(api: widget.api)); setState(() {}); }, child: const Icon(Icons.add)));
}

class AddSetSheet extends StatefulWidget { const AddSetSheet({super.key, required this.api}); final BrickTrackerApi api; @override State<AddSetSheet> createState() => _AddSetSheetState(); }
class _AddSetSheetState extends State<AddSetSheet> { final form = GlobalKey<FormState>(); final number = TextEditingController(); final name = TextEditingController(); final theme = TextEditingController(); final price = TextEditingController(); final quantity = TextEditingController(text: '1'); String condition = 'sealed'; @override Widget build(BuildContext context) => Padding(padding: EdgeInsets.fromLTRB(24, 24, 24, MediaQuery.viewInsetsOf(context).bottom + 24), child: Form(key: form, child: Wrap(runSpacing: 12, children: [Text('Add set', style: Theme.of(context).textTheme.titleLarge), TextFormField(controller: number, decoration: const InputDecoration(labelText: 'Set number'), validator: (v) => RegExp(r'^\d{3,8}-\d$').hasMatch(v ?? '') ? null : 'Use 12345-1'), TextFormField(controller: name, decoration: const InputDecoration(labelText: 'Set name'), validator: (v) => v!.isEmpty ? 'Required' : null), TextFormField(controller: theme, decoration: const InputDecoration(labelText: 'Theme')), TextFormField(controller: price, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Purchase price (USD)'), validator: (v) => double.tryParse(v ?? '') == null ? 'Enter a price' : null), TextFormField(controller: quantity, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Quantity')), SegmentedButton<String>(segments: const [ButtonSegment(value: 'sealed', label: Text('New / Sealed')), ButtonSegment(value: 'used', label: Text('Used / Built'))], selected: {condition}, onSelectionChanged: (v) => setState(() => condition = v.first)), FilledButton(onPressed: () async { if (!form.currentState!.validate()) return; await widget.api.addCollectionItem(setNumber: number.text, name: name.text, theme: theme.text.isEmpty ? 'Other' : theme.text, quantity: int.parse(quantity.text), condition: condition, purchasePriceCents: (double.parse(price.text) * 100).round()); if (context.mounted) Navigator.pop(context); }, child: const Text('Add to collection'))])));
}

class RetirementScreen extends StatelessWidget { const RetirementScreen({super.key, required this.api}); final BrickTrackerApi api; @override Widget build(BuildContext context) => FutureBuilder<Map<String, dynamic>>(future: api.retiringSoon(), builder: (context, snapshot) { if (!snapshot.hasData) return const Center(child: CircularProgressIndicator()); final groups = snapshot.data!['groups'] as Map<String, dynamic>; return ListView(padding: const EdgeInsets.all(16), children: [const Wrap(spacing: 8, children: [Chip(label: Text('30 days')), Chip(label: Text('90 days')), Chip(label: Text('6 months'))]), ...groups.entries.expand((entry) => [Padding(padding: const EdgeInsets.only(top: 16), child: Text(entry.key, style: Theme.of(context).textTheme.titleLarge)), ...(entry.value as List).map((set) => ListTile(title: Text('${set['set_number']}  ${set['name']}'), subtitle: Text('${set['status']} | ${set['months_remaining'] ?? '?'} months remaining'), trailing: IconButton(icon: const Icon(Icons.notifications_active_outlined), onPressed: () => api.watchSet(set['id'])))]); }); }

class AnalyticsScreen extends StatelessWidget { const AnalyticsScreen({super.key, required this.api}); final BrickTrackerApi api; @override Widget build(BuildContext context) => FutureBuilder<List<CollectionItem>>(future: api.collection(), builder: (context, snapshot) { if (!snapshot.hasData) return const Center(child: CircularProgressIndicator()); final items = snapshot.data!; final spots = [for (var i = 0; i < items.length; i++) FlSpot(i.toDouble(), items[i].currentValueCents / 100)]; final themes = <String, int>{}; for (final item in items) { themes[item.theme] = (themes[item.theme] ?? 0) + item.currentValueCents; } final sections = themes.entries.toList().asMap().entries.map((entry) => PieChartSectionData(value: entry.value.value / 100, title: entry.value.key, color: Colors.primaries[entry.key % Colors.primaries.length])).toList(); return ListView(padding: const EdgeInsets.all(16), children: [Text('Portfolio growth', style: Theme.of(context).textTheme.titleLarge), SizedBox(height: 220, child: LineChart(LineChartData(lineBarsData: [LineChartBarData(spots: spots, isCurved: true, color: Colors.teal)], titlesData: const FlTitlesData(show: false), borderData: FlBorderData(show: false))), const SizedBox(height: 24), Text('Theme allocation', style: Theme.of(context).textTheme.titleLarge), SizedBox(height: 220, child: PieChart(PieChartData(sections: sections))), const SizedBox(height: 24), Text('Set appreciation', style: Theme.of(context).textTheme.titleLarge), ...items.map((item) => ListTile(title: Text(item.name), trailing: Text('${item.gainLossPercent?.toStringAsFixed(1) ?? '0.0'}%')))]); }); }