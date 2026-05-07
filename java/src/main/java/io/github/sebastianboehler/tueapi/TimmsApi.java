package io.github.sebastianboehler.tueapi;

import java.io.IOException;

public final class TimmsApi {
    private static final String BASE = "https://timms.uni-tuebingen.de";
    private final HttpTransport http;

    TimmsApi(HttpTransport http) {
        this.http = http;
    }

    public String search(String query, int offset, int limit) throws IOException, TueApiException {
        String path = offset > 0 || limit != 20 ? "/Search/ListTimecode" : "/Search/_QueryControl";
        return http.get(BASE + path, new QueryParams()
            .add("InputQueryString", query)
            .add("Offset", offset)
            .add("FetchNext", limit)
            .add("Hits", 0)
            .add("ShowLabel", "False")).text();
    }

    public String suggest(String term, int limit) throws IOException, TueApiException {
        return http.get(BASE + "/Search/AutoCompleteSearch", new QueryParams().add("term", term)).text();
    }

    public String item(String itemId) throws IOException, TueApiException {
        return http.get(BASE + "/tp/" + QueryParams.encode(itemId)).text();
    }

    public String streams(String itemId) throws IOException, TueApiException {
        return http.get(BASE + "/Player/EPlayer", new QueryParams().add("id", itemId).add("t", "0.0")).text();
    }

    public String tree(String nodeId, String nodePath) throws IOException, TueApiException {
        if (nodeId != null && !nodeId.isEmpty() && nodePath != null && !nodePath.isEmpty()) {
            return http.get(BASE + "/List/OpenNode", new QueryParams().add("nodeid", nodeId).add("nodepath", nodePath)).text();
        }
        return http.get(BASE + "/List/Browse").text();
    }
}
