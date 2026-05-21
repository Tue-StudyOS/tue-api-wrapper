import 'package:flutter/material.dart';

import 'app_section.dart';

class TodaySummarySection extends StatelessWidget {
  const TodaySummarySection({
    required this.schedule,
    required this.tasks,
    required this.moodle,
    required this.warnings,
    super.key,
  });

  final Map<String, Object?>? schedule;
  final List<Map<String, String?>> tasks;
  final Map<String, Object?>? moodle;
  final Map<String, String> warnings;

  @override
  Widget build(BuildContext context) {
    final events = scheduleEvents(schedule);
    final deadlines = moodleDeadlineItems(moodle);
    final next = events.firstOrNull;
    return AppSection(
      title: 'Today',
      icon: Icons.sunny,
      child: Column(
        children: [
          _StatusTile(
            title: next?['title']?.toString() ?? 'No upcoming lecture loaded',
            subtitle: next == null
                ? 'Refresh private data to load your Alma timetable.'
                : eventSubtitle(next),
            icon: Icons.event_outlined,
          ),
          const Divider(height: 1),
          _StatusTile(
            title:
                '${deadlines.length} Moodle deadlines · ${tasks.length} ILIAS tasks',
            subtitle: warnings.isEmpty
                ? 'Private study systems loaded independently.'
                : warnings.values.join(' '),
            icon: warnings.isEmpty
                ? Icons.checklist
                : Icons.warning_amber_rounded,
          ),
        ],
      ),
    );
  }
}

class AlmaPrivateSection extends StatelessWidget {
  const AlmaPrivateSection({required this.exams, super.key});

  final List<Map<String, Object?>> exams;

  @override
  Widget build(BuildContext context) {
    return AppSection(
      title: 'Alma Exams',
      icon: Icons.school_outlined,
      child: MapItemList(
          items: exams,
          titleKey: 'title',
          subtitleKeys: const ['grade', 'cp', 'status']),
    );
  }
}

class IliasSection extends StatelessWidget {
  const IliasSection({required this.tasks, super.key});

  final List<Map<String, String?>> tasks;

  @override
  Widget build(BuildContext context) {
    return AppSection(
      title: 'ILIAS Tasks',
      icon: Icons.task_alt_outlined,
      child: MapItemList(
          items: tasks.cast<Map<String, Object?>>(),
          titleKey: 'title',
          subtitleKeys: const ['kind']),
    );
  }
}

class MoodleSection extends StatelessWidget {
  const MoodleSection({required this.dashboard, this.warning, super.key});

  final Map<String, Object?>? dashboard;
  final String? warning;

  @override
  Widget build(BuildContext context) {
    final deadlines = moodleDeadlineItems(dashboard);
    final courses = moodleCourseItems(dashboard);
    return AppSection(
      title: 'Moodle Deadlines',
      icon: Icons.forum_outlined,
      child: Column(
        children: [
          if (warning != null) WarningStrip(warning!),
          if (deadlines.isEmpty)
            EmptyState(dashboard == null
                ? 'No Moodle data loaded.'
                : 'No actionable Moodle deadlines are visible right now.')
          else
            MapItemList(
              items: deadlines,
              titleKey: 'name',
              subtitleBuilder: (item) => [
                item['courseName'],
                item['formattedTime'] ?? item['dueAt']
              ].map((value) => value?.toString()).nonNulls.join(' · '),
            ),
          if (courses.isNotEmpty) ...[
            const Divider(height: 1),
            EmptyState('${courses.length} Moodle courses visible.'),
          ],
        ],
      ),
    );
  }
}

class WarningStrip extends StatelessWidget {
  const WarningStrip(this.message, {super.key});

  final String message;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      color: colors.tertiaryContainer,
      child: Text(message, style: TextStyle(color: colors.onTertiaryContainer)),
    );
  }
}

List<Map<String, Object?>> scheduleEvents(Map<String, Object?>? schedule) {
  return (schedule?['events'] as List?)
          ?.map((item) => Map<String, Object?>.from(item as Map))
          .toList() ??
      const [];
}

String eventSubtitle(Map<String, Object?> item) {
  return [
    formattedDateRange(item['start']?.toString(), item['end']?.toString()),
    item['location']?.toString(),
    item['room']?.toString(),
    item['lecturer']?.toString(),
  ]
      .where((value) => value != null && value.trim().isNotEmpty)
      .cast<String>()
      .join(' · ');
}

String? formattedDateRange(String? start, String? end) {
  final startDate = start == null ? null : DateTime.tryParse(start);
  if (startDate == null) {
    return start;
  }
  final endDate = end == null ? null : DateTime.tryParse(end);
  final startText =
      '${_weekday(startDate)} ${_two(startDate.day)}.${_two(startDate.month)} ${_two(startDate.hour)}:${_two(startDate.minute)}';
  if (endDate == null) {
    return startText;
  }
  return '$startText-${_two(endDate.hour)}:${_two(endDate.minute)}';
}

List<Map<String, Object?>> moodleDeadlineItems(
    Map<String, Object?>? dashboard) {
  final data = _ajaxData(dashboard?['events']);
  final events = data is Map ? data['events'] : null;
  return events is List
      ? events.map((item) => Map<String, Object?>.from(item as Map)).toList()
      : const [];
}

List<Map<String, Object?>> moodleCourseItems(Map<String, Object?>? dashboard) {
  final data = _ajaxData(dashboard?['courses']);
  final courses = data is Map ? data['courses'] : null;
  return courses is List
      ? courses.map((item) => Map<String, Object?>.from(item as Map)).toList()
      : const [];
}

Object? _ajaxData(Object? value) {
  if (value is List && value.isNotEmpty && value.first is Map) {
    return (value.first as Map)['data'];
  }
  return value;
}

String _two(int value) => value.toString().padLeft(2, '0');

String _weekday(DateTime date) {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  return days[date.weekday - 1];
}

class _StatusTile extends StatelessWidget {
  const _StatusTile(
      {required this.title, required this.subtitle, required this.icon});

  final String title;
  final String subtitle;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
      title: Text(title, maxLines: 2, overflow: TextOverflow.ellipsis),
      subtitle: Text(subtitle, maxLines: 3, overflow: TextOverflow.ellipsis),
    );
  }
}
