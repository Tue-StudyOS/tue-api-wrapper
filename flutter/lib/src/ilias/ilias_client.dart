import '../auth/university_credentials.dart';
import '../html/html_forms.dart';
import '../http/native_http_session.dart';

class IliasClient {
  IliasClient({NativeHttpSession? session, UniversityCredentials? credentials})
      : _session = session ?? NativeHttpSession(),
        _credentials = credentials;

  static final Uri _base =
      Uri.parse('https://ovidius.uni-tuebingen.de/ilias3/');
  static final Uri _login = _base.resolve('login.php?cmd=force_login');
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
    final page = await _session.get(_login);
    final document = parseHtml(page.body, page.uri);
    final shib = document.querySelector('a[href*="shib_login.php"]');
    if (shib == null) {
      throw StateError('Could not find the ILIAS Shibboleth login link.');
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

  Future<List<Map<String, String?>>> rootLinks() async {
    await _ensureLoggedIn();
    final page = await _session.get(_base.resolve('goto.php/root/1'));
    return _parseLinks(page.body, page.uri);
  }

  Future<List<Map<String, String?>>> memberships({int limit = 40}) async {
    await _ensureLoggedIn();
    final page = await _session
        .get(_base.resolve('ilias.php?baseClass=ilmembershipoverviewgui'));
    return _parseStandardItems(page.body, page.uri, limit);
  }

  Future<List<Map<String, String?>>> tasks({int limit = 40}) async {
    await _ensureLoggedIn();
    final page = await _session
        .get(_base.resolve('ilias.php?baseClass=ilderivedtasksgui'));
    return _parseStandardItems(page.body, page.uri, limit);
  }

  Future<List<Map<String, String?>>> content(String target,
      {int limit = 80}) async {
    await _ensureLoggedIn();
    final page = await _session.get(_normalizeTarget(target));
    return _parseStandardItems(page.body, page.uri, limit);
  }

  Future<List<Map<String, String?>>> forumTopics(String target,
      {int limit = 80}) {
    return content(target, limit: limit);
  }

  Future<List<Map<String, String?>>> exerciseAssignments(String target,
      {int limit = 80}) {
    return content(target, limit: limit);
  }

  Future<String> search(String term, {int page = 1}) async {
    await _ensureLoggedIn();
    final uri = _base.resolve('ilias.php').replace(queryParameters: {
      'baseClass': 'ilSearchController',
      'cmd': 'post',
      'searchterm': term,
      'page': '$page',
    });
    return (await _session.get(uri)).body;
  }

  Future<String> info(String target) async {
    await _ensureLoggedIn();
    return (await _session.get(_normalizeTarget(target))).body;
  }

  Future<void> _completeSaml(NativeResponse response) async {
    var current = response;
    for (var attempt = 0; attempt < 6; attempt++) {
      final html = current.body;
      if (current.uri.host == 'ovidius.uni-tuebingen.de' &&
          !current.uri.path.contains('login')) {
        return;
      }
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
    throw StateError('Could not complete the ILIAS SAML handoff.');
  }

  List<Map<String, String?>> _parseLinks(String html, Uri uri) {
    final document = parseHtml(html, uri);
    final links = <Map<String, String?>>[];
    for (final link in document.querySelectorAll('a[href]')) {
      final label = cleanText(link);
      if (label.isEmpty) {
        continue;
      }
      links.add({
        'label': label,
        'url': uri.resolve(link.attributes['href'] ?? '').toString(),
      });
    }
    return links;
  }

  List<Map<String, String?>> _parseStandardItems(
      String html, Uri uri, int limit) {
    final document = parseHtml(html, uri);
    final items = <Map<String, String?>>[];
    for (final item in document.querySelectorAll(
        'div.il-item.il-std-item, div.ilContainerListItemOuter')) {
      final link = item.querySelector('a[href]');
      if (link == null || (limit > 0 && items.length >= limit)) {
        continue;
      }
      items.add({
        'title': cleanText(link),
        'url': uri.resolve(link.attributes['href'] ?? '').toString(),
        'kind': item.querySelector('img[alt]')?.attributes['alt'],
      });
    }
    return items;
  }

  Uri _normalizeTarget(String target) {
    final uri = Uri.tryParse(target);
    if (uri != null && uri.hasScheme) {
      return uri;
    }
    if (target.startsWith('goto.php/')) {
      return _base.resolve(target);
    }
    return _base.resolve('goto.php/$target');
  }

  Future<void> _ensureLoggedIn() async {
    if (!_loggedIn) {
      await login();
    }
  }

  UniversityCredentials _requireCredentials() {
    final credentials = _credentials;
    if (credentials == null || !credentials.isComplete) {
      throw StateError('This ILIAS call requires university credentials.');
    }
    return credentials;
  }

  void close() {
    _session.close();
  }
}
