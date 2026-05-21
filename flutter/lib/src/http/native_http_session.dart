import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

class NativeHttpSession {
  NativeHttpSession(
      {http.Client? client, this.timeout = const Duration(seconds: 30)})
      : _client = client ?? http.Client();

  final http.Client _client;
  final Duration timeout;
  final Map<String, String> _cookies = {};

  Future<NativeResponse> get(Uri uri, {Map<String, String>? headers}) {
    return _request('GET', uri, headers: headers);
  }

  Future<NativeResponse> postForm(
    Uri uri,
    Map<String, String> fields, {
    Map<String, String>? headers,
  }) {
    return _request(
      'POST',
      uri,
      headers: {
        'content-type': 'application/x-www-form-urlencoded; charset=utf-8',
        ...?headers,
      },
      body: Uri(queryParameters: fields).query,
    );
  }

  Future<NativeResponse> postJson(
    Uri uri,
    Object payload, {
    String? referer,
  }) {
    return _request(
      'POST',
      uri,
      headers: {
        'accept': 'application/json',
        'content-type': 'application/json',
        if (referer != null) 'referer': referer,
      },
      body: jsonEncode(payload),
    );
  }

  Future<NativeResponse> _request(
    String method,
    Uri uri, {
    Map<String, String>? headers,
    String? body,
  }) async {
    var currentMethod = method;
    var currentUri = uri;
    var currentBody = body;
    var currentHeaders = headers ?? const <String, String>{};

    for (var redirect = 0; redirect < 8; redirect++) {
      final request = http.Request(currentMethod, currentUri);
      request.followRedirects = false;
      request.headers.addAll({
        'accept': '*/*',
        'user-agent': 'tue-api-flutter/0.1',
        if (_cookies.isNotEmpty) 'cookie': _cookieHeader(),
        ...currentHeaders,
      });
      if (currentBody != null) {
        request.body = currentBody;
      }

      final streamed = await _client.send(request).timeout(timeout);
      final response = await http.Response.fromStream(streamed);
      _storeCookies(response.headers['set-cookie']);

      if (_isRedirect(response.statusCode)) {
        final location = response.headers['location'];
        if (location == null || location.isEmpty) {
          return _checked(response, currentUri);
        }
        currentUri = currentUri.resolve(location);
        if (response.statusCode == 303 ||
            (currentMethod == 'POST' &&
                (response.statusCode == 301 || response.statusCode == 302))) {
          currentMethod = 'GET';
          currentBody = null;
          currentHeaders = const <String, String>{};
        }
        continue;
      }
      return _checked(response, currentUri);
    }
    throw NativeRequestException(
        message: 'Too many redirects while requesting $uri.');
  }

  NativeResponse _checked(http.Response response, Uri uri) {
    final result = NativeResponse(
      statusCode: response.statusCode,
      uri: uri,
      headers: response.headers,
      bytes: response.bodyBytes,
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw NativeRequestException(
        statusCode: response.statusCode,
        uri: uri,
        message: result.body,
      );
    }
    return result;
  }

  void _storeCookies(String? header) {
    if (header == null || header.isEmpty) {
      return;
    }
    for (final cookie in header.split(RegExp(r',(?=\s*[^;,]+=)'))) {
      final pair = cookie.split(';').first.trim();
      final separator = pair.indexOf('=');
      if (separator <= 0) {
        continue;
      }
      _cookies[pair.substring(0, separator)] = pair.substring(separator + 1);
    }
  }

  String _cookieHeader() {
    return _cookies.entries
        .map((entry) => '${entry.key}=${entry.value}')
        .join('; ');
  }

  static bool _isRedirect(int status) => status >= 300 && status < 400;

  void close() {
    _client.close();
  }
}

class NativeResponse {
  const NativeResponse({
    required this.statusCode,
    required this.uri,
    required this.headers,
    required this.bytes,
  });

  final int statusCode;
  final Uri uri;
  final Map<String, String> headers;
  final Uint8List bytes;

  String get body => utf8.decode(bytes, allowMalformed: true);
}

class NativeRequestException implements Exception {
  const NativeRequestException(
      {this.statusCode, this.uri, required this.message});

  final int? statusCode;
  final Uri? uri;
  final String message;

  @override
  String toString() {
    final prefix =
        statusCode == null ? 'Native request failed' : 'HTTP $statusCode';
    return uri == null ? '$prefix: $message' : '$prefix for $uri: $message';
  }
}
