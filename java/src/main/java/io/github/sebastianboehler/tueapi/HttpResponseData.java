package io.github.sebastianboehler.tueapi;

import java.nio.charset.StandardCharsets;

final class HttpResponseData {
    final int statusCode;
    final String url;
    final byte[] body;

    HttpResponseData(int statusCode, String url, byte[] body) {
        this.statusCode = statusCode;
        this.url = url;
        this.body = body == null ? new byte[0] : body;
    }

    String text() {
        return new String(body, StandardCharsets.UTF_8);
    }
}
