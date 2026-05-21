import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../auth/university_credentials.dart';
import '../tue_client.dart';
import 'dashboard_controls.dart';
import 'dashboard_sections.dart';
import 'login_screen.dart';
import 'load_result.dart';
import 'private_sections.dart';
import 'schedule_timetable.dart';
class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}
class _DashboardScreenState extends State<DashboardScreen> {
  static const _storage = FlutterSecureStorage();
  static const _webPrivateDataMessage =
      'Private university login cannot run in Flutter Web because Chrome blocks the direct Alma, ILIAS, and Moodle SSO requests with CORS/cookie policy. Use the iOS or Android build for credentialed data.';

  final _username = TextEditingController();
  final _password = TextEditingController();
  final _date = TextEditingController();
  final _timms = TextEditingController(text: 'machine learning');

  bool _credentialsLoaded = false;
  bool _hasCredentials = false;
  int _selectedTab = 0;
  String? _error;
  String? _loading;
  Map<String, Object?>? _privateSchedule;
  Map<String, Object?>? _publicLectures;
  List<Map<String, String?>> _events = const [];
  List<Map<String, Object?>> _exams = const [];
  List<Map<String, String?>> _iliasTasks = const [];
  Map<String, Object?>? _moodleDashboard;
  Object? _canteens;
  Map<String, Object?>? _timmsResults;
  Map<String, Object?>? _timmsTree;
  Map<String, String> _privateWarnings = const {};

  @override
  void initState() {
    super.initState();
    _loadStoredCredentials();
  }

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    _date.dispose();
    _timms.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final busy = _loading != null;
    if (!_credentialsLoaded) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (!_hasCredentials) {
      return LoginScreen(
        username: _username,
        password: _password,
        busy: busy,
        error: _error,
        onSignIn: _signIn,
      );
    }
    return Scaffold(
      appBar: AppBar(
        title: Text(_title),
        actions: [
          IconButton(
            tooltip: 'Refresh',
            onPressed: busy ? null : _refreshCurrentTab,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (_error != null) ErrorBanner(_error!),
          if (_loading != null) ...[
            const LinearProgressIndicator(minHeight: 3),
            const SizedBox(height: 16),
          ],
          ..._pageChildren(busy),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedTab,
        onDestinationSelected: (index) => setState(() => _selectedTab = index),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.sunny), label: 'Today'),
          NavigationDestination(
              icon: Icon(Icons.calendar_today_outlined), label: 'Schedule'),
          NavigationDestination(
              icon: Icon(Icons.school_outlined), label: 'Study'),
          NavigationDestination(
              icon: Icon(Icons.travel_explore), label: 'Discover'),
          NavigationDestination(
              icon: Icon(Icons.video_library_outlined), label: 'TIMMS'),
        ],
      ),
    );
  }

  String get _title {
    const titles = ['Today', 'Schedule', 'Study', 'Discover', 'TIMMS'];
    return titles[_selectedTab];
  }

  List<Widget> _pageChildren(bool busy) {
    switch (_selectedTab) {
      case 0:
        return [
          TodaySummarySection(
            schedule: _privateSchedule,
            tasks: _iliasTasks,
            moodle: _moodleDashboard,
            warnings: _privateWarnings,
          ),
        ];
      case 1:
        return [
          PrivateScheduleSection(schedule: _privateSchedule),
        ];
      case 2:
        return [
          MoodleSection(
              dashboard: _moodleDashboard, warning: _privateWarnings['Moodle']),
          IliasSection(tasks: _iliasTasks),
          AlmaPrivateSection(exams: _exams),
        ];
      case 3:
        return [
          PublicPanel(date: _date, busy: busy, onSubmit: _loadPublic),
          PublicLecturesSection(lectures: _publicLectures),
          CampusSection(canteens: _canteens, events: _events),
        ];
      default:
        return [
          TimmsSection(
            results: _timmsResults,
            tree: _timmsTree,
            search: _timms,
            busy: busy,
            onSearch: _loadPublic,
            onNodeSelected: _loadTimmsNode,
          ),
        ];
    }
  }

  Future<void> _loadStoredCredentials() async {
    _username.text = await _storage.read(key: 'uni_username') ?? '';
    _password.text = await _storage.read(key: 'uni_password') ?? '';
    final hasCredentials =
        _username.text.trim().isNotEmpty && _password.text.isNotEmpty;
    if (!mounted) {
      return;
    }
    setState(() {
      _credentialsLoaded = true;
      _hasCredentials = hasCredentials;
    });
    if (hasCredentials) {
      await _refreshAll();
    }
  }

  Future<void> _signIn() async {
    if (_username.text.trim().isEmpty || _password.text.isEmpty) {
      setState(() => _error = 'Enter both username and password.');
      return;
    }
    await _storage.write(key: 'uni_username', value: _username.text.trim());
    await _storage.write(key: 'uni_password', value: _password.text);
    if (!mounted) {
      return;
    }
    setState(() {
      _hasCredentials = true;
      _error = null;
    });
    await _refreshAll();
  }

  Future<void> _loadPublic() async {
    final client = TuebingenFlutterClient();
    await _run('public data', () async {
      final lectures =
          await client.alma.currentLectures(date: _date.text.trim(), limit: 8);
      final canteens = await client.campus.canteens();
      final events = await client.campus.events(limit: 6);
      final timms =
          await client.timms.searchResults(_timms.text.trim(), limit: 5);
      final timmsTree = await client.timms.treePage();
      if (!mounted) {
        return;
      }
      setState(() {
        _publicLectures = lectures;
        _canteens = canteens;
        _events = events;
        _timmsResults = timms;
        _timmsTree = timmsTree;
      });
    });
    client.close();
  }

  Future<void> _loadTimmsNode(Map<String, Object?> node) async {
    final nodeId = node['node_id']?.toString();
    final nodePath = node['node_path']?.toString();
    final client = TuebingenFlutterClient();
    await _run('TIMMS archive', () async {
      final tree =
          await client.timms.treePage(nodeId: nodeId, nodePath: nodePath);
      if (mounted) {
        setState(() => _timmsTree = tree);
      }
    });
    client.close();
  }

  Future<void> _loadPrivate() async {
    if (kIsWeb) {
      setState(() => _error = _webPrivateDataMessage);
      return;
    }
    final credentials = UniversityCredentials(
        username: _username.text.trim(), password: _password.text);
    final client = TuebingenFlutterClient(credentials: credentials);
    await _run('private data', () async {
      final schedule = await captureLoad(
          'Alma timetable', () => client.alma.upcomingLectures(limit: 32));
      final exams =
          await captureLoad('Alma exams', () => client.alma.exams(limit: 50));
      final tasks =
          await captureLoad('ILIAS', () => client.ilias.tasks(limit: 20));
      final moodle = await captureLoad(
          'Moodle',
          () => client.moodle
              .dashboard(eventLimit: 12, courseLimit: 20, recentLimit: 6));
      if (!mounted) {
        return;
      }
      setState(() {
        _privateSchedule = schedule.value ?? _privateSchedule;
        _exams = exams.value ?? _exams;
        _iliasTasks = tasks.value ?? _iliasTasks;
        _moodleDashboard = moodle.value ?? _moodleDashboard;
        _privateWarnings = {
          for (final result in [schedule, exams, tasks, moodle])
            if (result.warning != null) result.label: result.warning!,
        };
      });
    });
    client.close();
  }

  void _refreshCurrentTab() {
    if (_selectedTab == 3 || _selectedTab == 4) {
      _loadPublic();
      return;
    }
    _loadPrivate();
  }

  Future<void> _refreshAll() async {
    await _loadPrivate();
    await _loadPublic();
  }

  Future<void> _run(String label, Future<void> Function() action) async {
    setState(() {
      _loading = label;
      _error = null;
    });
    try {
      await action();
    } catch (error) {
      if (mounted) {
        setState(() => _error = error.toString());
      }
    } finally {
      if (mounted) {
        setState(() => _loading = null);
      }
    }
  }
}
