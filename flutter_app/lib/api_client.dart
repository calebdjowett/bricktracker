import 'dart:convert';
import 'package:http/http.dart' as http;
import 'models.dart';

class BrickTrackerApi {
  BrickTrackerApi({http.Client? client, this.baseUrl = 'http://10.0.2.2:8001'}) : _client = client ?? http.Client();
  final http.Client _client;
  final String baseUrl;

  Future<DashboardData> dashboard() async => DashboardData.fromJson(await _get('/dashboard'));
  Future<List<CollectionItem>> collection() async => (await _get('/collection') as List).map((item) => CollectionItem.fromJson(item)).toList();
  Future<Map<String, dynamic>> retiringSoon() async => await _get('/retiring-soon');

  Future<void> addCollectionItem({required String setNumber, required String name, required String theme, required int quantity, required String condition, required int purchasePriceCents}) async {
    final response = await _client.post(Uri.parse('$baseUrl/collection'), headers: {'Content-Type': 'application/json'}, body: jsonEncode({'set': {'set_number': setNumber, 'name': name, 'theme': theme}, 'quantity': quantity, 'condition': condition, 'purchase_price_cents': purchasePriceCents}));
    if (response.statusCode != 201) throw Exception('Could not add set: ${response.body}');
  }

  Future<void> watchSet(int setId) async {
    final response = await _client.post(Uri.parse('$baseUrl/watchlist'), headers: {'Content-Type': 'application/json'}, body: jsonEncode({'set_id': setId, 'notifications_enabled': true}));
    if (response.statusCode != 201) throw Exception('Could not add watchlist item');
  }

  Future<dynamic> _get(String path) async {
    final response = await _client.get(Uri.parse('$baseUrl$path'));
    if (response.statusCode != 200) throw Exception('Request failed: ${response.body}');
    return jsonDecode(response.body);
  }
}
