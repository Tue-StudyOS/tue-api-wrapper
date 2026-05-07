package io.github.sebastianboehler.tueapi;

import java.io.IOException;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;

public final class IliasApi {
    private static final String BASE = "https://ovidius.uni-tuebingen.de/ilias3/";
    private static final String LOGIN = BASE + "login.php?cmd=force_login";
    private static final String SAML_RESPONSE = "SAML" + "Response";
    private static final String RELAY_STATE = "Relay" + "State";
    private static final String EVENT_PROCEED = "_eventId_" + "proceed";
    private static final String USER_FIELD = "j_" + "username";
    private static final String PASSWORD_FIELD = "j_" + "password";
    private final HttpTransport http;
    private final UniversityCredentials credentials;
    private boolean loggedIn;

    IliasApi(HttpTransport http, UniversityCredentials credentials) {
        this.http = http;
        this.credentials = credentials;
    }

    public void login() throws IOException, TueApiException {
        UniversityCredentials creds = requireCredentials();
        HttpResponseData page = http.get(LOGIN);
        Document login = HtmlSupport.parse(page.text(), page.url);
        Element shib = login.selectFirst("a[href*=shib_login.php]");
        if (shib == null) {
            throw new TueApiException("Could not find the ILIAS Shibboleth login link.");
        }
        HttpResponseData idp = http.get(HtmlSupport.resolve(page.url, shib.attr("href")));
        HtmlForm form = HtmlSupport.formWithInput(idp.text(), idp.url, PASSWORD_FIELD);
        form.payload.set(USER_FIELD, creds.username()).set(PASSWORD_FIELD, creds.password());
        form.payload.set(EVENT_PROCEED, form.payload.value(EVENT_PROCEED));
        HttpResponseData response = http.postForm(form.actionUrl, form.payload);
        completeSaml(response);
        loggedIn = true;
    }

    public String root() throws IOException, TueApiException {
        ensureLoggedIn();
        return parseLinks(http.get(BASE + "goto.php/root/1").text(), BASE, "root");
    }

    public String memberships(int limit) throws IOException, TueApiException {
        ensureLoggedIn();
        String html = http.get(BASE + "ilias.php?baseClass=ilmembershipoverviewgui").text();
        return parseStandardItems(html, BASE, limit);
    }

    public String tasks(int limit) throws IOException, TueApiException {
        ensureLoggedIn();
        String html = http.get(BASE + "ilias.php?baseClass=ilderivedtasksgui").text();
        return parseStandardItems(html, BASE, limit);
    }

    public String content(String target) throws IOException, TueApiException {
        ensureLoggedIn();
        return parseStandardItems(http.get(normalizeTarget(target)).text(), BASE, 0);
    }

    public String forum(String target) throws IOException, TueApiException {
        return content(target);
    }

    public String exercise(String target) throws IOException, TueApiException {
        return content(target);
    }

    public String search(String term, int page) throws IOException, TueApiException {
        ensureLoggedIn();
        return http.get(BASE + "ilias.php", new QueryParams()
            .add("baseClass", "ilSearchController")
            .add("cmd", "post")
            .add("searchterm", term)
            .add("page", page)).text();
    }

    public String info(String target) throws IOException, TueApiException {
        ensureLoggedIn();
        return http.get(normalizeTarget(target)).text();
    }

    private void completeSaml(HttpResponseData response) throws IOException, TueApiException {
        HttpResponseData current = response;
        for (int attempt = 0; attempt < 6; attempt++) {
            String html = current.text();
            if (current.url.contains("ovidius.uni-tuebingen.de") && html.contains("ILIAS Universität Tübingen")) {
                return;
            }
            if (html.contains(SAML_RESPONSE) && html.contains(RELAY_STATE)) {
                HtmlForm form = HtmlSupport.hiddenFormWithFields(html, current.url, SAML_RESPONSE, RELAY_STATE);
                current = http.postForm(form.actionUrl, form.payload);
                continue;
            }
            if (current.url.contains("idp.uni-tuebingen.de") && html.contains(EVENT_PROCEED)) {
                HtmlForm form = HtmlSupport.hiddenFormWithFields(html, current.url, EVENT_PROCEED);
                current = http.postForm(form.actionUrl, form.payload);
                continue;
            }
            break;
        }
        throw new TueApiException("Could not complete the ILIAS SAML handoff.");
    }

    private String parseLinks(String html, String pageUrl, String title) {
        Document document = HtmlSupport.parse(html, pageUrl);
        StringBuilder json = new StringBuilder("{").append(JsonSupport.pair("title", title)).append(",\"links\":[");
        int count = 0;
        for (Element link : document.select("a[href]")) {
            String label = link.text().replaceAll("\\s+", " ").trim();
            if (label.isEmpty()) {
                continue;
            }
            if (count++ > 0) {
                json.append(",");
            }
            json.append("{").append(JsonSupport.pair("label", label)).append(",")
                .append(JsonSupport.pair("url", HtmlSupport.resolve(pageUrl, link.attr("href")))).append("}");
        }
        return json.append("]}").toString();
    }

    private String parseStandardItems(String html, String pageUrl, int limit) {
        Document document = HtmlSupport.parse(html, pageUrl);
        StringBuilder json = new StringBuilder("[");
        int count = 0;
        for (Element item : document.select("div.il-item.il-std-item, div.ilContainerListItemOuter")) {
            Element link = item.selectFirst("a[href]");
            if (link == null || (limit > 0 && count >= limit)) {
                continue;
            }
            if (count++ > 0) {
                json.append(",");
            }
            json.append("{").append(JsonSupport.pair("title", link.text())).append(",")
                .append(JsonSupport.pair("url", HtmlSupport.resolve(pageUrl, link.attr("href")))).append(",")
                .append(JsonSupport.pair("kind", imageAlt(item))).append("}");
        }
        return json.append("]").toString();
    }

    private String normalizeTarget(String target) {
        if (target.startsWith("http://") || target.startsWith("https://")) {
            return target;
        }
        if (target.startsWith("goto.php/")) {
            return HtmlSupport.resolve(BASE, target);
        }
        return HtmlSupport.resolve(BASE + "goto.php/", target);
    }

    private void ensureLoggedIn() throws IOException, TueApiException {
        if (!loggedIn) {
            login();
        }
    }

    private UniversityCredentials requireCredentials() throws TueApiException {
        if (credentials == null) {
            throw new TueApiException("This ILIAS call requires UniversityCredentials.");
        }
        return credentials;
    }

    private static String imageAlt(Element item) {
        Element image = item.selectFirst("img[alt]");
        return image == null ? null : image.attr("alt");
    }
}
