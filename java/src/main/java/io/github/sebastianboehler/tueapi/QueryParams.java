package io.github.sebastianboehler.tueapi;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.List;

public final class QueryParams {
    private final List<String[]> pairs = new ArrayList<>();

    public QueryParams add(String name, String value) {
        if (value != null) {
            pairs.add(new String[] {name, value});
        }
        return this;
    }

    public QueryParams set(String name, String value) {
        remove(name);
        return add(name, value);
    }

    public QueryParams remove(String name) {
        for (int i = pairs.size() - 1; i >= 0; i--) {
            if (pairs.get(i)[0].equals(name)) {
                pairs.remove(i);
            }
        }
        return this;
    }

    public String value(String name) {
        for (String[] pair : pairs) {
            if (pair[0].equals(name)) {
                return pair[1];
            }
        }
        return "";
    }

    public QueryParams add(String name, int value) {
        pairs.add(new String[] {name, Integer.toString(value)});
        return this;
    }

    public QueryParams add(String name, boolean value) {
        pairs.add(new String[] {name, Boolean.toString(value)});
        return this;
    }

    public String toQueryString() {
        if (pairs.isEmpty()) {
            return "";
        }
        StringBuilder builder = new StringBuilder();
        for (String[] pair : pairs) {
            if (builder.length() > 0) {
                builder.append('&');
            }
            builder.append(encode(pair[0])).append('=').append(encode(pair[1]));
        }
        return builder.toString();
    }

    static String encode(String value) {
        try {
            return URLEncoder.encode(value, "UTF-8").replace("+", "%20");
        } catch (UnsupportedEncodingException error) {
            throw new IllegalStateException("UTF-8 encoding is not available", error);
        }
    }
}
