import 'dart:convert';

import '../auth/university_credentials.dart';
import '../html/html_forms.dart';
import '../http/native_http_session.dart';

class MoodleClient {
  MoodleClient({NativeHttpSession? session, UniversityCredentials? credentials})
      : _session = session ?? NativeHttpSession(),
        _credentials = credentials;

  static final Uri _base = Uri.parse('https://moodle.zdv.uni-tuebingen.de');
  static final RegExp _sesskey = RegExp(r'"sesskey"\s*:\s*"([^"]+)"');
  static const String _ssoPayloadField = 'SAML' 'Response';
  static const String _relayState = 'Relay' 'State';
  static const String _eventProceed = '_eventId_' 'proceed';
  static const String _userField = 'j_' 'username';
  static const String _passwordField = 'j_' 'password';

  final NativeHttpSession _session;
  final UniversityCredentials? _credentials;
  bool _loggedIn = false;

  Future<void> login() async {
    final credentials = _requireCredentials();
    final page = await _session.get(_base.resolve('/login/index.php'));
    final document = parseHtml(page.body, page.uri);
    final shib =
        document.querySelector('a[href*="shibboleth"], a[href*="Shibboleth"]');
    if (shib == null) {
      throw StateError('Could not find Moodle Shibboleth login link.');
    }
    final idp =
        await _session.get(page.uri.resolve(shib.attributes['href'] ?? ''));
    final form = formWithInput(idp.body, idp.uri, _passwordField);
    form.set(_userField, credentials.username);
    form.set(_passwordField, credentials.password);
    form.set(_eventProceed, form.fields[_eventProceed]);
    await _completeSaml(await _session.postForm(form.action, form.fields));
    _loggedIn = true;
  }

  Future<Map<String, Object?>> dashboard({
    int eventLimit = 6,
    int courseLimit = 12,
    int recentLimit = 9,
  }) async {
    final page = await _authenticatedPage(_base.resolve('/my/'));
    final key = _extractSesskey(page);
    final events = await _ajax(
        key,
        'core_calendar_get_action_events_by_timesort',
        {
          'limitnum': eventLimit,
        },
        referer: _base.resolve('/my/'));
    final courses = await _ajax(
        key,
        'core_course_get_enrolled_courses_by_timeline_classification',
        {
          'offset': 0,
          'limit': courseLimit,
          'classification': 'all',
          'sort': 'fullname',
        },
        referer: _base.resolve('/my/'));
    final recent = await _ajax(
        key,
        'block_recentlyaccesseditems_get_recent_items',
        {
          'limit': recentLimit,
        },
        referer: _base.resolve('/my/'));
    return {'events': events, 'courses': courses, 'recent': recent};
  }

  Future<Object?> deadlines({int days = 30, int limit = 50}) async {
    final page = await _authenticatedPage(_base.resolve('/my/'));
    return _ajax(
        _extractSesskey(page),
        'core_calendar_get_action_events_by_timesort',
        {
          'limitnum': limit,
        },
        referer: _base.resolve('/my/'));
  }

  Future<Object?> courses({
    String classification = 'all',
    int limit = 24,
    int offset = 0,
  }) async {
    final page = await _authenticatedPage(_base.resolve('/my/courses.php'));
    return _ajax(
        _extractSesskey(page),
        'core_course_get_enrolled_courses_by_timeline_classification',
        {
          'offset': offset,
          'limit': limit,
          'classification': classification,
          'sort': 'fullname',
        },
        referer: _base.resolve('/my/courses.php'));
  }

  Future<String> categoriesPage() async {
    return _authenticatedPage(_base.resolve('/course/index.php'));
  }

  Future<String> coursePage(int courseId) async {
    return _authenticatedPage(_base.resolve('/enrol/index.php?id=$courseId'));
  }

  Future<String> gradesPage() async {
    return _authenticatedPage(
        _base.resolve('/grade/report/overview/index.php'));
  }

  Future<String> messagesPage() async {
    return _authenticatedPage(_base.resolve('/message/index.php'));
  }

  Future<String> notificationsPage() async {
    return _authenticatedPage(
        _base.resolve('/message/output/popup/notifications.php'));
  }

  Future<String> _authenticatedPage(Uri uri) async {
    await _ensureLoggedIn();
    final response = await _session.get(uri);
    if (response.uri.path.contains('/login/')) {
      throw StateError('Moodle redirected back to login.');
    }
    return response.body;
  }

  Future<Object?> _ajax(
    String sesskey,
    String method,
    Map<String, Object?> args, {
    required Uri referer,
  }) async {
    final uri =
        _base.resolve('/lib/ajax/service.php').replace(queryParameters: {
      'sesskey': sesskey,
      'info': method,
    });
    final payload = [
      {'index': 0, 'methodname': method, 'args': args},
    ];
    return jsonDecode(
        (await _session.postJson(uri, payload, referer: referer.toString()))
            .body);
  }

  Future<void> _completeSaml(NativeResponse response) async {
    var current = response;
    for (var attempt = 0; attempt < 6; attempt++) {
      if (current.uri.host == _base.host &&
          !current.uri.path.contains('/login/index.php')) {
        return;
      }
      final html = current.body;
      if (html.contains(_ssoPayloadField) && html.contains(_relayState)) {
        final form = hiddenFormWithFields(
            html, current.uri, [_ssoPayloadField, _relayState]);
        current = await _session.postForm(form.action, form.fields);
        continue;
      }
      if (current.uri.host == 'idp.uni-tuebingen.de' &&
          html.contains(_eventProceed)) {
        final form = hiddenFormWithFields(html, current.uri, [_eventProceed]);
        current = await _session.postForm(form.action, form.fields);
        continue;
      }
      break;
    }
    throw StateError('Could not complete the Moodle SAML handoff.');
  }

  String _extractSesskey(String html) {
    final match = _sesskey.firstMatch(html);
    if (match == null) {
      throw StateError('Moodle page did not expose a sesskey.');
    }
    return match.group(1)!;
  }

  Future<void> _ensureLoggedIn() async {
    if (!_loggedIn) {
      await login();
    }
  }

  UniversityCredentials _requireCredentials() {
    final credentials = _credentials;
    if (credentials == null || !credentials.isComplete) {
      throw StateError('This Moodle call requires university credentials.');
    }
    return credentials;
  }

  void close() {
    _session.close();
  }
}
