import 'dart:convert';

import 'package:xml/xml.dart';

import '../http/native_http_session.dart';

class CampusClient {
  CampusClient({NativeHttpSession? session})
      : _session = session ?? NativeHttpSession();

  static final Uri _mealplan =
      Uri.parse('https://www.my-stuwe.de/wp-json/mealplans/v1/');
  static final Uri _buildings = Uri.parse(
    'https://uni-tuebingen.de/universitaet/standort-und-anfahrt/lageplaene/adressenliste/',
  );
  static final Uri _events = Uri.parse(
    'https://uni-tuebingen.de/universitaet/campusleben/veranstaltungen/veranstaltungskalender/feed.xml',
  );
  static final Uri _kuf = Uri.parse(
    'https://buchung.hsp.uni-tuebingen.de/angebote/aktueller_zeitraum/_Anzahl_der_Trainierenden_in_der_KuF.html',
  );
  static final Uri _seatfinder =
      Uri.parse('https://seatfinder.bibliothek.kit.edu/tuebingen/getdata.php');

  final NativeHttpSession _session;

  Future<Object?> canteens({String? date}) async {
    final uri = _mealplan.resolve('canteens').replace(queryParameters: {
      'lang': 'de',
      if (date != null && date.isNotEmpty) 'date': date,
    });
    return jsonDecode((await _session.get(uri)).body);
  }

  Future<Object?> canteen(int canteenId, {String? date}) async {
    final uri =
        _mealplan.resolve('canteens/$canteenId').replace(queryParameters: {
      'lang': 'de',
      if (date != null && date.isNotEmpty) 'date': date,
    });
    return jsonDecode((await _session.get(uri)).body);
  }

  Future<String> buildingsPage() async {
    return (await _session.get(_buildings)).body;
  }

  Future<String> buildingDetail(String pathOrUrl) async {
    final uri = Uri.tryParse(pathOrUrl);
    if (uri != null && uri.hasScheme) {
      return (await _session.get(uri)).body;
    }
    return (await _session
            .get(Uri.parse('https://uni-tuebingen.de/').resolve(pathOrUrl)))
        .body;
  }

  Future<List<Map<String, String?>>> events(
      {String query = '', int limit = 24}) async {
    final body = (await _session.get(_events)).body;
    final document = XmlDocument.parse(body);
    final normalizedQuery = query.trim().toLowerCase();
    final items = <Map<String, String?>>[];
    for (final item in document.findAllElements('item')) {
      final title = _xmlText(item, 'title');
      final description = _xmlText(item, 'description');
      final haystack = '$title $description'.toLowerCase();
      if (normalizedQuery.isNotEmpty && !haystack.contains(normalizedQuery)) {
        continue;
      }
      items.add({
        'title': title,
        'link': _xmlText(item, 'link'),
        'published': _xmlText(item, 'pubDate'),
        'description': description,
      });
      if (limit > 0 && items.length >= limit) {
        break;
      }
    }
    return items;
  }

  Future<String> kufOccupancyPage() async {
    return (await _session.get(_kuf)).body;
  }

  Future<String> seatAvailability() async {
    final locations = 'UBH1,UBB2,UBB2HLS,UBA3A,UBA3C,UBA4A,UBA4B,UBA4C,'
        'UBA5A,UBA5B,UBA5C,UBA6A,UBA6B,UBA6C,UBCEG,UBCUG,UBLZN,UBNEG,UBWZA,UBWZB';
    final uri = _seatfinder.replace(queryParameters: {
      'location[0]': locations,
      'values[0]': 'seatestimate,manualcount',
      'after[0]': '-10800seconds',
      'before[0]': 'now',
      'limit[0]': '-17',
      'location[1]': locations,
      'values[1]': 'location',
      'before[1]': 'now',
      'limit[1]': '1',
    });
    return (await _session.get(uri)).body;
  }

  String? _xmlText(XmlElement item, String name) {
    final matches = item.findElements(name);
    if (matches.isEmpty) {
      return null;
    }
    final value = matches.first.innerText.trim();
    return value.isEmpty ? null : value;
  }

  void close() {
    _session.close();
  }
}
