import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:tue_api_flutter/src/http/native_http_session.dart';
import 'package:tue_api_flutter/src/timms/timms_client.dart';

void main() {
  test('searchResults parses TIMMS result rows', () async {
    final client = TimmsClient(
      session: NativeHttpSession(
        client: MockClient((request) async {
          return http.Response('''
            <div id="content">
              <h1>1 Treffer</h1>
              <h2><a href="/tp/item-1">Machine Learning</a></h2>
              <div>
                <table>
                  <tr><td>01:02:03</td></tr>
                  <tr>
                    <td class="infoitem">00:00:10</td>
                    <td class="infoitemcontent"><a href="/Player/EPlayer?id=item-1&amp;starttime=10">Intro</a></td>
                  </tr>
                </table>
              </div>
            </div>
          ''', 200, request: request);
        }),
      ),
    );

    final page = await client.searchResults('machine learning', limit: 5);
    final results = (page['results'] as List).cast<Map<String, Object?>>();

    expect(page['total_hits'], 1);
    expect(results.single['title'], 'Machine Learning');
    expect(results.single['duration'], '01:02:03');
    expect((results.single['chapters'] as List).single,
        containsPair('title', 'Intro'));
  });

  test('treePage parses TIMMS archive nodes and visible videos', () async {
    final client = TimmsClient(
      session: NativeHttpSession(
        client: MockClient((request) async {
          return http.Response('''
            <div id="content">
              <div class="opennodecontainer">
                <div class="opennode"><a href="/List/OpenNode?nodeid=root&amp;nodepath=/">Root</a></div>
                <div class="closednode"><a href="/List/OpenNode?nodeid=ml&amp;nodepath=/ml">Machine Learning</a></div>
              </div>
              <a href="/tp/video-1">Lecture 1</a>
            </div>
          ''', 200, request: request);
        }),
      ),
    );

    final tree = await client.treePage();
    final nodes = (tree['nodes'] as List).cast<Map<String, Object?>>();
    final items = (tree['items'] as List).cast<Map<String, Object?>>();

    expect(nodes.first['label'], 'Root');
    expect(nodes.last['node_id'], 'ml');
    expect(items.single['title'], 'Lecture 1');
  });
}
