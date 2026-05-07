package io.github.sebastianboehler.tueapi;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.CookieHandler;
import java.net.CookieManager;
import java.net.CookiePolicy;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

final class HttpTransport {
    private final int timeoutMillis;

    HttpTransport(int timeoutMillis) {
        this.timeoutMillis = timeoutMillis;
        CookieHandler.setDefault(new CookieManager(null, CookiePolicy.ACCEPT_ALL));
    }

    HttpResponseData get(String url) throws IOException, TueApiException {
        return request("GET", url, null, null, "*/*");
    }

    HttpResponseData get(String url, QueryParams params) throws IOException, TueApiException {
        return get(appendQuery(url, params));
    }

    HttpResponseData postForm(String url, QueryParams form) throws IOException, TueApiException {
        byte[] body = form.toQueryString().getBytes(StandardCharsets.UTF_8);
        return request("POST", url, body, "application/x-www-form-urlencoded; charset=utf-8", "*/*");
    }

    HttpResponseData postJson(String url, String json, String referer) throws IOException, TueApiException {
        return request("POST", url, json.getBytes(StandardCharsets.UTF_8), "application/json", "application/json", referer);
    }

    private HttpResponseData request(
        String method,
        String url,
        byte[] body,
        String contentType,
        String accept
    ) throws IOException, TueApiException {
        return request(method, url, body, contentType, accept, null);
    }

    private HttpResponseData request(
        String method,
        String url,
        byte[] body,
        String contentType,
        String accept,
        String referer
    ) throws IOException, TueApiException {
        HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
        connection.setRequestMethod(method);
        connection.setConnectTimeout(timeoutMillis);
        connection.setReadTimeout(timeoutMillis);
        connection.setInstanceFollowRedirects(true);
        connection.setRequestProperty("Accept", accept);
        connection.setRequestProperty("User-Agent", "tue-api-wrapper-java/0.2");
        if (referer != null && !referer.isEmpty()) {
            connection.setRequestProperty("Referer", referer);
        }
        if (body != null) {
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", contentType);
            connection.getOutputStream().write(body);
        }
        int status = connection.getResponseCode();
        byte[] response = readFully(status >= 400 ? connection.getErrorStream() : connection.getInputStream());
        if (status < 200 || status >= 300) {
            throw new TueApiException(status, new String(response, StandardCharsets.UTF_8));
        }
        return new HttpResponseData(status, connection.getURL().toString(), response);
    }

    static String appendQuery(String url, QueryParams params) {
        String query = params == null ? "" : params.toQueryString();
        if (query.isEmpty()) {
            return url;
        }
        return url + (url.contains("?") ? "&" : "?") + query;
    }

    private static byte[] readFully(InputStream input) throws IOException {
        if (input == null) {
            return new byte[0];
        }
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int read;
        while ((read = input.read(buffer)) != -1) {
            output.write(buffer, 0, read);
        }
        return output.toByteArray();
    }
}
