import 'package:flutter/material.dart';

import 'app_section.dart';
import 'private_sections.dart';

class PrivateScheduleSection extends StatelessWidget {
  const PrivateScheduleSection({required this.schedule, super.key});

  final Map<String, Object?>? schedule;

  @override
  Widget build(BuildContext context) {
    final events =
        scheduleEvents(schedule).map(TimetableEvent.fromMap).nonNulls.toList();
    final term = schedule?['source_term']?.toString();
    return AppSection(
      title: term == null ? 'Schedule' : 'Schedule · $term',
      icon: Icons.calendar_today_outlined,
      child: events.isEmpty
          ? const EmptyState('No timetable entries loaded.')
          : TimetableGrid(events: events),
    );
  }
}

class TimetableGrid extends StatelessWidget {
  const TimetableGrid({required this.events, super.key});

  static const double _hourWidth = 48;
  static const double _dayWidth = 136;
  static const double _headerHeight = 58;
  static const double _hourHeight = 70;

  final List<TimetableEvent> events;

  @override
  Widget build(BuildContext context) {
    final days = _days(events);
    final minHour = _minHour(events);
    final maxHour = _maxHour(events);
    final hourCount = maxHour - minHour + 1;
    final height = _headerHeight + hourCount * _hourHeight;
    final width = _hourWidth + days.length * _dayWidth;
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: SizedBox(
        width: width,
        height: height,
        child: Stack(
          children: [
            for (var index = 0; index < days.length; index++)
              _dayHeader(context, days[index], index),
            for (var hour = minHour; hour <= maxHour; hour++)
              _hourLine(context, hour, minHour, width),
            for (final event in events)
              _eventBlock(context, event, days, minHour),
          ],
        ),
      ),
    );
  }

  Widget _dayHeader(BuildContext context, DateTime day, int index) {
    final x = _hourWidth + index * _dayWidth;
    return Positioned(
      left: x,
      top: 0,
      width: _dayWidth,
      height: _headerHeight,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(6, 10, 6, 8),
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.secondaryContainer,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Center(
            child: Text(
              '${_weekday(day)}\n${_two(day.day)}.${_two(day.month)}',
              textAlign: TextAlign.center,
              style: Theme.of(context)
                  .textTheme
                  .labelLarge
                  ?.copyWith(fontWeight: FontWeight.w700),
            ),
          ),
        ),
      ),
    );
  }

  Widget _hourLine(BuildContext context, int hour, int minHour, double width) {
    final y = _headerHeight + (hour - minHour) * _hourHeight;
    return Positioned(
      left: 0,
      top: y,
      width: width,
      height: _hourHeight,
      child: Stack(
        children: [
          Positioned(
            left: _hourWidth,
            right: 0,
            top: 0,
            child: Divider(
                height: 1, color: Theme.of(context).colorScheme.outlineVariant),
          ),
          Positioned(
            left: 8,
            top: 8,
            child: Text('${_two(hour)}:00',
                style: Theme.of(context).textTheme.labelSmall),
          ),
        ],
      ),
    );
  }

  Widget _eventBlock(BuildContext context, TimetableEvent event,
      List<DateTime> days, int minHour) {
    final dayIndex = days.indexWhere((day) => _sameDay(day, event.start));
    if (dayIndex < 0) {
      return const SizedBox.shrink();
    }
    final startMinutes = event.start.hour * 60 + event.start.minute;
    final endMinutes =
        (event.end ?? event.start.add(const Duration(minutes: 60))).hour * 60 +
            (event.end ?? event.start).minute;
    final top =
        _headerHeight + ((startMinutes - minHour * 60) / 60) * _hourHeight;
    final height =
        (((endMinutes - startMinutes).clamp(40, 240)) / 60) * _hourHeight;
    final color = _eventColor(context, event.title);
    return Positioned(
      left: _hourWidth + dayIndex * _dayWidth + 6,
      top: top + 4,
      width: _dayWidth - 12,
      height: height - 8,
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
          border: Border(left: BorderSide(color: color, width: 4)),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Padding(
          padding: const EdgeInsets.all(8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(event.timeRange,
                  style: Theme.of(context)
                      .textTheme
                      .labelSmall
                      ?.copyWith(fontWeight: FontWeight.w700, color: color)),
              const SizedBox(height: 4),
              Text(event.title,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context)
                      .textTheme
                      .bodySmall
                      ?.copyWith(fontWeight: FontWeight.w700)),
              if (event.location != null)
                Text(event.location!,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.labelSmall),
            ],
          ),
        ),
      ),
    );
  }
}

class TimetableEvent {
  const TimetableEvent(
      {required this.title, required this.start, this.end, this.location});

  final String title;
  final DateTime start;
  final DateTime? end;
  final String? location;

  String get timeRange =>
      end == null ? _time(start) : '${_time(start)}-${_time(end!)}';

  static TimetableEvent? fromMap(Map<String, Object?> item) {
    final start = DateTime.tryParse(item['start']?.toString() ?? '');
    if (start == null) {
      return null;
    }
    final location = [item['location'], item['room']]
        .map((value) => value?.toString())
        .nonNulls
        .join(', ');
    return TimetableEvent(
      title: item['title']?.toString() ?? 'Untitled lecture',
      start: start,
      end: DateTime.tryParse(item['end']?.toString() ?? ''),
      location: location.isEmpty ? null : location,
    );
  }
}

List<DateTime> _days(List<TimetableEvent> events) {
  final rawDays = events
      .map((event) =>
          DateTime(event.start.year, event.start.month, event.start.day))
      .toSet()
      .toList();
  rawDays.sort();
  return rawDays;
}

int _minHour(List<TimetableEvent> events) => events
    .map((event) => event.start.hour)
    .fold(8, (a, b) => a < b ? a : b)
    .clamp(6, 22);

int _maxHour(List<TimetableEvent> events) {
  final latest = events
      .map((event) => event.end?.hour ?? event.start.hour + 1)
      .fold(18, (a, b) => a > b ? a : b);
  return latest.clamp(8, 23);
}

Color _eventColor(BuildContext context, String title) {
  final colors = [
    Colors.red,
    Colors.orange,
    Colors.blue,
    Colors.teal,
    Colors.green,
    Colors.indigo,
    Colors.pink
  ];
  final seed = title.codeUnits.fold<int>(0, (sum, unit) => sum + unit);
  return colors[seed % colors.length];
}

bool _sameDay(DateTime lhs, DateTime rhs) =>
    lhs.year == rhs.year && lhs.month == rhs.month && lhs.day == rhs.day;

String _weekday(DateTime date) =>
    const ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][date.weekday - 1];

String _time(DateTime date) => '${_two(date.hour)}:${_two(date.minute)}';

String _two(int value) => value.toString().padLeft(2, '0');
