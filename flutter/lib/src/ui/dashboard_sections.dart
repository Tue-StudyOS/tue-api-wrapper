import 'dart:convert';

import 'package:flutter/material.dart';

import 'app_section.dart';

class PublicLecturesSection extends StatelessWidget {
  const PublicLecturesSection({required this.lectures, super.key});

  final Map<String, Object?>? lectures;

  @override
  Widget build(BuildContext context) {
    final results =
        (lectures?['results'] as List?)?.cast<Map<String, Object?>>() ??
            const [];
    return AppSection(
      title: 'Public Alma Browse',
      icon: Icons.event_note_outlined,
      child: MapItemList(
        items: results,
        titleKey: 'title',
        subtitleKeys: const ['start', 'end', 'room', 'lecturer'],
      ),
    );
  }
}

class CampusSection extends StatelessWidget {
  const CampusSection(
      {required this.canteens, required this.events, super.key});

  final Object? canteens;
  final List<Map<String, String?>> events;

  @override
  Widget build(BuildContext context) {
    final canteenItems = normalizedCanteens(canteens);
    return AppSection(
      title: 'Campus',
      icon: Icons.location_city_outlined,
      child: Column(
        children: [
          if (canteenItems.isEmpty)
            const EmptyState('No canteen menus returned for today.')
          else
            ...canteenItems.take(4).map((canteen) => CanteenTile(canteen)),
          const Divider(height: 1),
          MapItemList(
            items: events.cast<Map<String, Object?>>(),
            titleKey: 'title',
            subtitleKeys: const ['published'],
          ),
        ],
      ),
    );
  }
}

class TimmsSection extends StatelessWidget {
  const TimmsSection({
    required this.results,
    required this.tree,
    required this.search,
    required this.busy,
    required this.onSearch,
    required this.onNodeSelected,
    super.key,
  });

  final Map<String, Object?>? results;
  final Map<String, Object?>? tree;
  final TextEditingController search;
  final bool busy;
  final VoidCallback onSearch;
  final void Function(Map<String, Object?> node) onNodeSelected;

  @override
  Widget build(BuildContext context) {
    final items = (results?['results'] as List?)
            ?.map((item) => Map<String, Object?>.from(item as Map))
            .toList() ??
        const <Map<String, Object?>>[];
    final treeNodes = (tree?['nodes'] as List?)
            ?.map((item) => Map<String, Object?>.from(item as Map))
            .toList() ??
        const <Map<String, Object?>>[];
    final treeItems = (tree?['items'] as List?)
            ?.map((item) => Map<String, Object?>.from(item as Map))
            .toList() ??
        const <Map<String, Object?>>[];
    final total = results?['total_hits'];
    return AppSection(
      title: 'TIMMS',
      icon: Icons.video_library_outlined,
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: search,
              onSubmitted: (_) {
                if (!busy) {
                  onSearch();
                }
              },
              decoration: const InputDecoration(
                labelText: 'Search archive',
                prefixIcon: Icon(Icons.search),
              ),
            ),
          ),
          const Divider(height: 1),
          if (tree == null)
            const EmptyState('Archive tree not loaded.')
          else ...[
            const EmptyState('Archive tree'),
            ...treeNodes.map((node) => ListTile(
                  dense: true,
                  leading: Icon(
                    node['is_open'] == true
                        ? Icons.folder_open_outlined
                        : Icons.folder_outlined,
                  ),
                  title: Text(node['label']?.toString() ?? 'Folder'),
                  contentPadding: EdgeInsets.only(
                    left: 16 + ((node['depth'] as int?) ?? 0) * 16,
                    right: 16,
                  ),
                  onTap: () => onNodeSelected(node),
                )),
            if (treeItems.isEmpty)
              const EmptyState('Select a TIMMS folder to show recordings.')
            else
              MapItemList(
                items: treeItems,
                titleKey: 'title',
                subtitleKeys: const ['item_id'],
              ),
            const Divider(height: 1),
          ],
          if (results == null)
            const EmptyState('No search loaded.')
          else ...[
            EmptyState('$total public recording matches.'),
            MapItemList(
              items: items,
              titleKey: 'title',
              subtitleBuilder: (item) {
                final chapters = item['chapters'] is List
                    ? (item['chapters'] as List).length
                    : 0;
                return [
                  item['duration']?.toString(),
                  chapters > 0 ? '$chapters chapters' : null,
                ].nonNulls.join(' · ');
              },
            ),
          ],
        ],
      ),
    );
  }
}

class CanteenTile extends StatelessWidget {
  const CanteenTile(this.canteen, {super.key});

  final Map<String, Object?> canteen;

  @override
  Widget build(BuildContext context) {
    final menus = (canteen['menus'] as List?)
            ?.map((item) => Map<String, Object?>.from(item as Map))
            .toList() ??
        const <Map<String, Object?>>[];
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(canteen['canteen']?.toString() ?? 'Canteen',
              style: Theme.of(context)
                  .textTheme
                  .titleSmall
                  ?.copyWith(fontWeight: FontWeight.w600)),
          if (canteen['address'] != null)
            Text(canteen['address'].toString(),
                style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 8),
          for (final menu in menus.take(4))
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                      child: Text(menuTitle(menu),
                          maxLines: 2, overflow: TextOverflow.ellipsis)),
                  const SizedBox(width: 8),
                  Text(menuPrice(menu),
                      style: Theme.of(context).textTheme.labelLarge),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class ErrorBanner extends StatelessWidget {
  const ErrorBanner(this.message, {super.key});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.errorContainer,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(message,
          style:
              TextStyle(color: Theme.of(context).colorScheme.onErrorContainer)),
    );
  }
}

String summaryValue(Object? value) {
  if (value == null) {
    return 'No data loaded.';
  }
  if (value is List) {
    return '${value.length} entries';
  }
  final encoded = jsonEncode(value);
  return encoded.length <= 140 ? encoded : '${encoded.substring(0, 140)}...';
}

List<Map<String, Object?>> normalizedCanteens(Object? value) {
  if (value is List) {
    return value.map((item) => Map<String, Object?>.from(item as Map)).toList();
  }
  if (value is Map) {
    return value.values
        .whereType<Map>()
        .map((item) => Map<String, Object?>.from(item))
        .toList();
  }
  return const [];
}

String menuTitle(Map<String, Object?> menu) {
  final items = menu['items'];
  if (items is List && items.isNotEmpty) {
    return items.take(2).map((item) => item.toString()).join(', ');
  }
  return menu['menu_line']?.toString() ??
      menu['menuLine']?.toString() ??
      'Menu item';
}

String menuPrice(Map<String, Object?> menu) {
  return menu['student_price']?.toString() ??
      menu['studentPrice']?.toString() ??
      '';
}
