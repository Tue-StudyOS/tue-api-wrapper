import 'package:flutter/material.dart';

class AppSection extends StatelessWidget {
  const AppSection({
    required this.title,
    required this.icon,
    required this.child,
    super.key,
  });

  final String title;
  final IconData icon;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: Border.all(color: colors.outlineVariant),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
            child: Row(
              children: [
                Icon(icon, size: 20, color: colors.primary),
                const SizedBox(width: 10),
                Text(
                  title,
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w600),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          child,
        ],
      ),
    );
  }
}

class EmptyState extends StatelessWidget {
  const EmptyState(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Text(text, style: Theme.of(context).textTheme.bodyMedium),
    );
  }
}

class MapItemList extends StatelessWidget {
  const MapItemList({
    required this.items,
    required this.titleKey,
    this.subtitleKeys = const [],
    this.subtitleBuilder,
    super.key,
  });

  final List<Map<String, Object?>> items;
  final String titleKey;
  final List<String> subtitleKeys;
  final String Function(Map<String, Object?> item)? subtitleBuilder;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const EmptyState('No entries returned.');
    }
    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: items.length,
      separatorBuilder: (_, __) => const Divider(height: 1),
      itemBuilder: (context, index) {
        final item = items[index];
        final title = _value(item[titleKey]) ?? 'Untitled';
        final subtitle = subtitleBuilder?.call(item) ??
            subtitleKeys.map((key) => _value(item[key])).nonNulls.join(' · ');
        return ListTile(
          title: Text(title, maxLines: 2, overflow: TextOverflow.ellipsis),
          subtitle: subtitle.isEmpty
              ? null
              : Text(subtitle, maxLines: 2, overflow: TextOverflow.ellipsis),
        );
      },
    );
  }

  String? _value(Object? value) {
    final text = value?.toString().trim();
    return text == null || text.isEmpty ? null : text;
  }
}
