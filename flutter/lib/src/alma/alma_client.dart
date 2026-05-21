import 'package:html/dom.dart';

import '../auth/university_credentials.dart';
import '../html/html_forms.dart';
import '../http/native_http_session.dart';
import 'ics_calendar.dart';

class AlmaClient {
  AlmaClient({NativeHttpSession? session, UniversityCredentials? credentials})
      : _session = session ?? NativeHttpSession(),
        _credentials = credentials;

  static final Uri _base = Uri.parse('https://alma.uni-tuebingen.de');
  static final Uri _start =
      _base.resolve('/alma/pages/cs/sys/portal/hisinoneStartPage.faces');
  static final Uri _current = _base.resolve(
    '/alma/pages/cm/exa/timetable/currentLectures.xhtml'
    '?_flowId=showEventsAndExaminationsOnDate-flow'
    '&navigationPosition=studiesOffered,currentLecturesGeneric&recordRequest=true',
  );
  static final Uri _exams = _base.resolve(
    '/alma/pages/sul/examAssessment/personExamsReadonly.xhtml'
    '?_flowId=examsOverviewForPerson-flow'
    '&navigationPosition=hisinoneMeinStudium%2CexamAssessmentForStudent&recordRequest=true',
  );
  static final Uri _timetable = _base.resolve(
    '/alma/pages/plan/individualTimetable.xhtml'
    '?_flowId=individualTimetableSchedule-flow'
    '&navigationPosition=hisinoneMeinStudium%2CindividualTimetableSchedule&recordRequest=true',
  );

  final NativeHttpSession _session;
  final UniversityCredentials? _credentials;
  bool _loggedIn = false;

  Future<void> login() async {
    final credentials = _requireCredentials();
    final page = await _session.get(_start);
    final form = _loginForm(page.body, page.uri);
    form.set('asdf', credentials.username);
    form.set('fdsa', credentials.password);
    form.set('submit', '');
    final response = await _session.postForm(form.action, form.fields);
    if (_looksLoggedOut(response.body, response.uri)) {
      throw StateError('Alma login did not reach an authenticated page.');
    }
    _loggedIn = true;
  }

  Future<Map<String, Object?>> currentLectures(
      {String? date, int limit = 20}) async {
    var response = await _session.get(_current);
    if (date != null && date.trim().isNotEmpty) {
      final document = parseHtml(response.body, response.uri);
      final form = formById(
          response.body, response.uri, 'showEventsAndExaminationsOnDateForm');
      final dateField = document.querySelector('input[name\$=":date"]');
      final search = document.querySelector('button[name\$=":searchButtonId"]');
      if (dateField == null || search == null) {
        throw StateError('Could not identify Alma current-lectures fields.');
      }
      final dateName = dateField.attributes['name']!;
      final searchName = search.attributes['name']!;
      form.set(dateName, date);
      form.set('activePageElementId', searchName);
      form.set(searchName, 'Suchen');
      response = await _session.postForm(form.action, form.fields);
    }
    return _parseCurrentLectures(response.body, response.uri, limit);
  }

  Future<List<Map<String, Object?>>> exams({int limit = 50}) async {
    await _ensureLoggedIn();
    final response = await _session.get(_exams);
    return _parseExams(response.body, limit);
  }

  Future<Map<String, Object?>> upcomingLectures(
      {int days = 14, int limit = 32}) async {
    await _ensureLoggedIn();
    final page = await _session.get(_timetable);
    final term = _selectedTerm(page.body, page.uri);
    final exportUrl = _exportUri(page.body, page.uri, term['value']!);
    final rawCalendar = (await _session.get(exportUrl)).body;
    if (!rawCalendar.contains('BEGIN:VCALENDAR')) {
      throw StateError(
          'Expected Alma timetable iCalendar export, but Alma returned a different response.');
    }
    final now = DateTime.now();
    final end = now.add(Duration(days: days));
    final lectures = expandIcsEvents(parseIcsEvents(rawCalendar), now, end)
        .take(limit)
        .map((event) => event.toJson())
        .toList();
    return {
      'source_term': term['label'],
      'refreshed_at': now.toIso8601String(),
      'events': lectures,
    };
  }

  Future<String> timetablePage() async {
    await _ensureLoggedIn();
    return (await _session.get(_timetable)).body;
  }

  Future<String> enrollmentsPage() async {
    await _ensureLoggedIn();
    final uri = _base.resolve(
      '/alma/pages/cm/exa/enrollment/info/start.xhtml'
      '?_flowId=searchOwnEnrollmentInfo-flow'
      '&navigationPosition=hisinoneMeinStudium%2ChisinoneOwnEnrollmentList&recordRequest=true',
    );
    return (await _session.get(uri)).body;
  }

  Future<String> studyservicePage() async {
    await _ensureLoggedIn();
    return (await _session.get(
      _base.resolve(
          '/alma/pages/cs/sys/portal/subMenu.faces?navigationPosition=hisinoneMeinStudium%2Cstudyservice'),
    ))
        .body;
  }

  Future<String> moduleSearch({String? query}) async {
    final uri = _base.resolve(
      '/alma/pages/cm/exa/curricula/moduleDescriptionSearch.xhtml'
      '?_flowId=searchElementsInModuleDescription-flow'
      '&navigationPosition=studiesOffered%2CmoduleDescriptions%2CsearchElementsInModuleDescription&recordRequest=true',
    );
    final page = await _session.get(uri);
    if (query == null || query.trim().isEmpty) {
      return page.body;
    }
    final document = parseHtml(page.body, page.uri);
    final formNode = document.querySelector('form');
    final textInput = document.querySelector('input[type=text][name]');
    final search = document
        .querySelector('button[name\$=":search"], input[type=submit][name]');
    if (formNode == null || textInput == null || search == null) {
      throw StateError('Could not identify Alma module-search fields.');
    }
    final form = formFromElement(formNode, page.uri);
    form.set(textInput.attributes['name']!, query);
    form.set('activePageElementId', search.attributes['name']);
    form.set(search.attributes['name']!, 'Suchen');
    return (await _session.postForm(form.action, form.fields)).body;
  }

  Future<void> _ensureLoggedIn() async {
    if (!_loggedIn) {
      await login();
    }
  }

  UniversityCredentials _requireCredentials() {
    final credentials = _credentials;
    if (credentials == null || !credentials.isComplete) {
      throw StateError('This Alma call requires university credentials.');
    }
    return credentials;
  }

  HtmlForm _loginForm(String html, Uri uri) {
    try {
      return formById(html, uri, 'loginForm');
    } on StateError {
      return formById(html, uri, 'mobileLoginForm');
    }
  }

  bool _looksLoggedOut(String html, Uri uri) {
    final document = parseHtml(html, uri);
    return document.body?.classes.contains('notloggedin') == true ||
        document.querySelector('form#loginForm') != null;
  }

  Map<String, Object?> _parseCurrentLectures(String html, Uri uri, int limit) {
    final document = parseHtml(html, uri);
    final table = document.querySelector(
        'table[id\$="coursesAndExaminationsOnDateListTableTable"]');
    final results = <Map<String, String?>>[];
    if (table != null) {
      for (final row in table.querySelectorAll('tr')) {
        final cells = row.querySelectorAll('td');
        if (cells.length < 13 || (limit > 0 && results.length >= limit)) {
          continue;
        }
        results.add({
          'title': nullableText(cells[1]),
          'start': nullableText(cells[2]),
          'end': nullableText(cells[3]),
          'number': nullableText(cells[4]),
          'event_type': nullableText(cells[6]),
          'lecturer': nullableText(cells[8]),
          'building': nullableText(cells[9]),
          'room': nullableText(cells[10]),
        });
      }
    }
    return {
      'page_url': uri.toString(),
      'selected_date':
          document.querySelector('input[name\$=":date"]')?.attributes['value'],
      'results': results,
    };
  }

  List<Map<String, Object?>> _parseExams(String html, int limit) {
    final document = parseHtml(html, _exams);
    final rows = <Map<String, Object?>>[];
    for (final row
        in document.querySelectorAll('table.treeTableWithIcons tr')) {
      final title =
          row.querySelector('[id\$=":defaulttext"], [id\$=":unDeftxt"]');
      if (title == null || (limit > 0 && rows.length >= limit)) {
        continue;
      }
      rows.add({
        'level': _level(row),
        'title': cleanText(title),
        'number': _field(row, 'elementnr'),
        'attempt': _field(row, 'attempt'),
        'grade': _field(row, 'grade'),
        'cp': _field(row, 'bonus'),
        'status': _field(row, 'workstatus'),
      });
    }
    return rows;
  }

  Map<String, String> _selectedTerm(String html, Uri uri) {
    final document = parseHtml(html, uri);
    final select = document.querySelector(
        'select[name="plan:scheduleConfiguration:anzeigeoptionen:changeTerm_input"]');
    final selected = select?.querySelector('option[selected]') ??
        select?.querySelector('option');
    final value = selected?.attributes['value']?.trim();
    final label = selected == null ? null : cleanText(selected);
    if (value == null || value.isEmpty || label == null || label.isEmpty) {
      throw StateError('Could not determine the selected Alma timetable term.');
    }
    return {'label': label, 'value': value};
  }

  Uri _exportUri(String html, Uri uri, String termId) {
    final document = parseHtml(html, uri);
    final raw = nullableText(document.querySelector(
        'textarea[name="plan:scheduleConfiguration:anzeigeoptionen:ical:cal_add"]'));
    if (raw == null) {
      throw StateError('Could not find the Alma iCalendar export URL.');
    }
    final target = uri.resolve(raw);
    final query = Map<String, String>.from(target.queryParameters)
      ..['termgroup'] = termId;
    return target.replace(queryParameters: query);
  }

  int _level(Element row) {
    for (final className in row.classes) {
      if (className.startsWith('treeTableCellLevel')) {
        return int.tryParse(className.substring('treeTableCellLevel'.length)) ??
            0;
      }
    }
    return 0;
  }

  String? _field(Element row, String suffix) {
    return nullableText(row.querySelector('[id\$=":$suffix"]'));
  }

  void close() {
    _session.close();
  }
}
