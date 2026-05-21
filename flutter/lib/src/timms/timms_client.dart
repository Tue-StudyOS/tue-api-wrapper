import 'package:html/dom.dart';

import '../http/native_http_session.dart';
import '../html/html_forms.dart';

class TimmsClient {
  TimmsClient({NativeHttpSession? session})
      : _session = session ?? NativeHttpSession();

  static final Uri _base = Uri.parse('https://timms.uni-tuebingen.de');
  final NativeHttpSession _session;

  Future<String> search(String query, {int offset = 0, int limit = 20}) async {
    final uri = _searchUri(query, offset: offset, limit: limit);
    return (await _session.get(uri)).body;
  }

  Future<Map<String, Object?>> searchResults(String query,
      {int offset = 0, int limit = 20}) async {
    final uri = _searchUri(query, offset: offset, limit: limit);
    final response = await _session.get(uri);
    return _parseSearch(response.body, response.uri,
        query: query, offset: offset, limit: limit);
  }

  Future<String> suggest(String term) async {
    final uri = _base
        .resolve('/Search/AutoCompleteSearch')
        .replace(queryParameters: {'term': term});
    return (await _session.get(uri)).body;
  }

  Future<String> item(String itemId) async {
    return (await _session
            .get(_base.resolve('/tp/${Uri.encodeComponent(itemId)}')))
        .body;
  }

  Future<String> streams(String itemId) async {
    final uri = _base.resolve('/Player/EPlayer').replace(queryParameters: {
      'id': itemId,
      't': '0.0',
    });
    return (await _session.get(uri)).body;
  }

  Future<String> tree({String? nodeId, String? nodePath}) async {
    if (nodeId != null &&
        nodeId.isNotEmpty &&
        nodePath != null &&
        nodePath.isNotEmpty) {
      final uri = _base.resolve('/List/OpenNode').replace(queryParameters: {
        'nodeid': nodeId,
        'nodepath': nodePath,
      });
      return (await _session.get(uri)).body;
    }
    return (await _session.get(_base.resolve('/List/Browse'))).body;
  }

  Future<Map<String, Object?>> treePage(
      {String? nodeId, String? nodePath}) async {
    await _session.get(_base.resolve('/List/Browse'));
    final response = nodeId != null &&
            nodeId.isNotEmpty &&
            nodePath != null &&
            nodePath.isNotEmpty
        ? await _session.get(_base.resolve('/List/OpenNode').replace(
            queryParameters: {'nodeid': nodeId, 'nodepath': nodePath},
          ))
        : await _session.get(_base.resolve('/List/Browse'));
    return _parseTree(response.body, response.uri);
  }

  Uri _searchUri(String query, {required int offset, required int limit}) {
    final path = offset > 0 || limit != 20
        ? '/Search/ListTimecode'
        : '/Search/_QueryControl';
    return _base.resolve(path).replace(queryParameters: {
      'InputQueryString': query,
      'Offset': '$offset',
      'FetchNext': '$limit',
      'Hits': '0',
      'ShowLabel': 'False',
    });
  }

  Map<String, Object?> _parseSearch(String html, Uri sourceUri,
      {required String query, required int offset, required int limit}) {
    final document = parseHtml(html, sourceUri);
    final content = document.querySelector('#content');
    final results = <Map<String, Object?>>[];
    final totalText = content?.querySelector('h1')?.text ?? '';
    final totalMatch = RegExp(r'(\d[\d.]*)\s+Treffer').firstMatch(totalText);
    for (final heading in content?.querySelectorAll('h2') ?? const []) {
      final link = heading.querySelector('a[href]');
      if (link == null) {
        continue;
      }
      final itemUrl = sourceUri.resolve(link.attributes['href'] ?? '');
      final detail = heading.nextElementSibling;
      final chapters = <Map<String, Object?>>[];
      String? duration;
      if (detail != null) {
        for (final cell in detail.querySelectorAll('td')) {
          final text = cleanText(cell);
          if (RegExp(r'^\d{1,2}:\d{2}:\d{2}').hasMatch(text)) {
            duration ??= text;
          }
        }
        for (final row in detail.querySelectorAll('table tr')) {
          final time = nullableText(row.querySelector('td.infoitem'));
          final chapterLink = row.querySelector('td.infoitemcontent a[href]');
          if (time == null || chapterLink == null) {
            continue;
          }
          chapters.add({
            'start': time,
            'title': cleanText(chapterLink),
            'url': sourceUri
                .resolve(chapterLink.attributes['href'] ?? '')
                .toString(),
          });
        }
      }
      results.add({
        'title': cleanText(link),
        'item_url': itemUrl.toString(),
        'item_id':
            itemUrl.pathSegments.isEmpty ? null : itemUrl.pathSegments.last,
        'duration': duration,
        'chapters': chapters,
      });
      if (results.length >= limit) {
        break;
      }
    }
    return {
      'query': query,
      'offset': offset,
      'limit': limit,
      'source_url': sourceUri.toString(),
      'total_hits':
          int.tryParse(totalMatch?.group(1)?.replaceAll('.', '') ?? '') ??
              results.length,
      'results': results,
    };
  }

  Map<String, Object?> _parseTree(String html, Uri sourceUri) {
    final document = parseHtml(html, sourceUri);
    final content = document.querySelector('#content');
    final container = content?.querySelector('div.opennodecontainer');
    if (content == null || container == null) {
      return {
        'source_url': sourceUri.toString(),
        'selected_node_id': null,
        'nodes': const [],
        'items': const [],
      };
    }
    final nodes = <Map<String, Object?>>[];
    _walkTree(container, sourceUri, depth: 0, nodes: nodes);
    final items =
        _parseTreeItems(content.querySelectorAll('a[href*="/tp/"]'), sourceUri);
    final openNodes = nodes.where((node) => node['is_open'] == true).toList();
    return {
      'source_url': sourceUri.toString(),
      'selected_node_id': openNodes.isEmpty ? null : openNodes.last['node_id'],
      'nodes': nodes,
      'items': items,
    };
  }

  void _walkTree(Element container, Uri sourceUri,
      {required int depth, required List<Map<String, Object?>> nodes}) {
    final openHeader = container.children
        .where((child) => child.classes.contains('opennode'))
        .firstOrNull;
    final openLink = openHeader?.querySelector('a[href]');
    if (openLink != null) {
      nodes
          .add(_parseTreeNode(openLink, sourceUri, depth: depth, isOpen: true));
    }
    for (final child in container.children) {
      if (child.classes.contains('closednode')) {
        final link = child.querySelector('a[href]');
        if (link != null) {
          nodes.add(
              _parseTreeNode(link, sourceUri, depth: depth + 1, isOpen: false));
        }
      } else if (child.classes.contains('opennodecontainer') &&
          child != container) {
        _walkTree(child, sourceUri, depth: depth + 1, nodes: nodes);
      }
    }
  }

  Map<String, Object?> _parseTreeNode(Element link, Uri sourceUri,
      {required int depth, required bool isOpen}) {
    final uri = sourceUri.resolve(link.attributes['href'] ?? '');
    return {
      'node_id': uri.queryParameters['nodeid'] ?? link.id,
      'node_path': uri.queryParameters['nodepath'] ?? '',
      'label': cleanText(link),
      'depth': depth,
      'is_open': isOpen,
    };
  }

  List<Map<String, Object?>> _parseTreeItems(
      List<Element> links, Uri sourceUri) {
    final seen = <String>{};
    final items = <Map<String, Object?>>[];
    for (final link in links) {
      final href = link.attributes['href'] ?? '';
      if (href.contains('starttime=')) {
        continue;
      }
      final itemUrl = sourceUri.resolve(href);
      final itemId = itemUrl.pathSegments.isEmpty
          ? itemUrl.toString()
          : itemUrl.pathSegments.last;
      if (!seen.add(itemId)) {
        continue;
      }
      items.add({
        'item_id': itemId,
        'title': cleanText(link),
        'url': itemUrl.toString(),
      });
    }
    return items;
  }

  void close() {
    _session.close();
  }
}
