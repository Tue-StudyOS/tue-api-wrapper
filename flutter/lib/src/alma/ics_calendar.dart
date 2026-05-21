class IcsEvent {
  const IcsEvent({
    required this.summary,
    required this.start,
    this.end,
    this.location,
    this.detail,
    this.uid,
    this.rule,
    this.excludedStarts = const {},
  });

  final String summary;
  final DateTime start;
  final DateTime? end;
  final String? location;
  final String? detail;
  final String? uid;
  final String? rule;
  final Set<DateTime> excludedStarts;
}

class IcsOccurrence {
  const IcsOccurrence({
    required this.id,
    required this.title,
    required this.start,
    this.end,
    this.location,
    this.detail,
  });

  final String id;
  final String title;
  final DateTime start;
  final DateTime? end;
  final String? location;
  final String? detail;

  Map<String, Object?> toJson() => {
        'id': id,
        'title': title,
        'start': start.toIso8601String(),
        'end': end?.toIso8601String(),
        'location': location,
        'detail': detail,
      };
}

List<IcsEvent> parseIcsEvents(String rawIcs) {
  final properties = _unfold(rawIcs).map(_parseProperty).nonNulls;
  final events = <IcsEvent>[];
  Map<String, List<_IcsProperty>>? current;
  for (final property in properties) {
    if (property.name == 'BEGIN' && property.value == 'VEVENT') {
      current = {};
      continue;
    }
    if (property.name == 'END' && property.value == 'VEVENT') {
      final event = current == null ? null : _parseEvent(current);
      if (event != null) {
        events.add(event);
      }
      current = null;
      continue;
    }
    current?[property.name] = [...current[property.name] ?? const [], property];
  }
  return events;
}

List<IcsOccurrence> expandIcsEvents(
    List<IcsEvent> events, DateTime windowStart, DateTime windowEnd) {
  final output = <IcsOccurrence>[];
  for (final event in events) {
    final rule = event.rule;
    if (rule == null || rule.isEmpty) {
      if (_overlaps(event.start, event.end, windowStart, windowEnd)) {
        output.add(_occurrence(event, event.start));
      }
      continue;
    }
    output.addAll(_expandRecurring(event, rule, windowStart, windowEnd));
  }
  output.sort((a, b) {
    final date = a.start.compareTo(b.start);
    return date == 0
        ? a.title.toLowerCase().compareTo(b.title.toLowerCase())
        : date;
  });
  return output;
}

IcsEvent? _parseEvent(Map<String, List<_IcsProperty>> fields) {
  final start = fields['DTSTART']?.firstOrNull;
  final startDate =
      start == null ? null : _parseIcsDate(start.value, start.parameters);
  if (startDate == null) {
    return null;
  }
  final end = fields['DTEND']?.firstOrNull;
  final excluded = <DateTime>{};
  for (final property in fields['EXDATE'] ?? const <_IcsProperty>[]) {
    for (final value in property.value.split(',')) {
      final parsed = _parseIcsDate(value, property.parameters);
      if (parsed != null) {
        excluded.add(parsed);
      }
    }
  }
  return IcsEvent(
    summary: _text(fields['SUMMARY']?.firstOrNull) ?? '',
    start: startDate,
    end: end == null ? null : _parseIcsDate(end.value, end.parameters),
    location: _text(fields['LOCATION']?.firstOrNull),
    detail: _text(fields['DESCRIPTION']?.firstOrNull),
    uid: _text(fields['UID']?.firstOrNull),
    rule: fields['RRULE']?.firstOrNull?.value,
    excludedStarts: excluded,
  );
}

List<IcsOccurrence> _expandRecurring(
    IcsEvent event, String rule, DateTime windowStart, DateTime windowEnd) {
  final parts = Map.fromEntries(rule
      .split(';')
      .map((part) => part.split('='))
      .where((part) => part.length == 2)
      .map(
        (part) => MapEntry(part[0].toUpperCase(), part[1]),
      ));
  final frequency = parts['FREQ'] ?? '';
  if (frequency != 'WEEKLY' && frequency != 'DAILY') {
    return const [];
  }
  final interval = int.tryParse(parts['INTERVAL'] ?? '1')?.clamp(1, 999) ?? 1;
  final until = parts['UNTIL'] == null
      ? windowEnd
      : _parseIcsDate(parts['UNTIL']!, const {}) ?? windowEnd;
  final maxDate = until.isBefore(windowEnd) ? until : windowEnd;
  final byDays = _weekdays(parts['BYDAY'], event.start.weekday);
  final duration = event.end?.difference(event.start);
  final countLimit = int.tryParse(parts['COUNT'] ?? '');
  var generated = 0;
  var cursor = event.start;
  final lectures = <IcsOccurrence>[];
  while (!cursor.isAfter(maxDate)) {
    final weekdayMatches =
        frequency == 'DAILY' || byDays.contains(cursor.weekday);
    final daysSinceStart = cursor.difference(event.start).inDays;
    final intervalMatches = frequency == 'DAILY'
        ? daysSinceStart % interval == 0
        : (daysSinceStart ~/ 7) % interval == 0;
    if (weekdayMatches &&
        intervalMatches &&
        !event.excludedStarts.contains(cursor)) {
      generated += 1;
      if (countLimit != null && generated > countLimit) {
        break;
      }
      final occurrence = IcsEvent(
        summary: event.summary,
        start: cursor,
        end: duration == null ? null : cursor.add(duration),
        location: event.location,
        detail: event.detail,
        uid: event.uid,
      );
      if (_overlaps(occurrence.start, occurrence.end, windowStart, windowEnd)) {
        lectures.add(_occurrence(occurrence, cursor));
      }
    }
    cursor = cursor.add(const Duration(days: 1));
  }
  return lectures;
}

IcsOccurrence _occurrence(IcsEvent event, DateTime start) => IcsOccurrence(
      id: '${event.uid ?? event.summary}-${start.millisecondsSinceEpoch}',
      title: event.summary.isEmpty ? 'Untitled lecture' : event.summary,
      start: start,
      end: event.end,
      location: event.location,
      detail: event.detail,
    );

bool _overlaps(
    DateTime start, DateTime? end, DateTime windowStart, DateTime windowEnd) {
  final effectiveEnd = end != null && end.isAfter(start) ? end : start;
  return !start.isAfter(windowEnd) && !effectiveEnd.isBefore(windowStart);
}

Set<int> _weekdays(String? raw, int fallback) {
  const map = {'MO': 1, 'TU': 2, 'WE': 3, 'TH': 4, 'FR': 5, 'SA': 6, 'SU': 7};
  if (raw == null || raw.isEmpty) {
    return {fallback};
  }
  return raw
      .split(',')
      .map((value) => map[value.substring(value.length - 2).toUpperCase()])
      .nonNulls
      .toSet();
}

List<String> _unfold(String rawIcs) {
  final lines = <String>[];
  for (final line
      in rawIcs.replaceAll('\r\n', '\n').replaceAll('\r', '\n').split('\n')) {
    if ((line.startsWith(' ') || line.startsWith('\t')) && lines.isNotEmpty) {
      lines[lines.length - 1] = lines.last + line.substring(1);
    } else {
      lines.add(line);
    }
  }
  return lines;
}

_IcsProperty? _parseProperty(String line) {
  final separator = line.indexOf(':');
  if (separator <= 0) {
    return null;
  }
  final keyParts = line.substring(0, separator).split(';');
  final parameters = <String, String>{};
  for (final part in keyParts.skip(1)) {
    final pair = part.split('=');
    if (pair.length == 2) {
      parameters[pair[0].toUpperCase()] = pair[1];
    }
  }
  return _IcsProperty(
      keyParts.first.toUpperCase(), parameters, line.substring(separator + 1));
}

DateTime? _parseIcsDate(String value, Map<String, String> parameters) {
  final date = RegExp(r'^(\d{4})(\d{2})(\d{2})$').firstMatch(value);
  if (date != null || parameters['VALUE'] == 'DATE') {
    final source = date ?? RegExp(r'^(\d{4})(\d{2})(\d{2})').firstMatch(value);
    return source == null
        ? null
        : DateTime(int.parse(source[1]!), int.parse(source[2]!),
            int.parse(source[3]!));
  }
  final match = RegExp(r'^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z?$')
      .firstMatch(value);
  if (match == null) {
    return null;
  }
  final parts = List.generate(6, (index) => int.parse(match[index + 1]!));
  if (value.endsWith('Z')) {
    return DateTime.utc(
            parts[0], parts[1], parts[2], parts[3], parts[4], parts[5])
        .toLocal();
  }
  return DateTime(parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]);
}

String? _text(_IcsProperty? property) {
  final value = property?.value;
  if (value == null || value.isEmpty) {
    return null;
  }
  return value
      .replaceAll(r'\n', '\n')
      .replaceAll(r'\N', '\n')
      .replaceAll(r'\,', ',')
      .replaceAll(r'\;', ';')
      .replaceAll(r'\\', '\\');
}

class _IcsProperty {
  const _IcsProperty(this.name, this.parameters, this.value);

  final String name;
  final Map<String, String> parameters;
  final String value;
}
