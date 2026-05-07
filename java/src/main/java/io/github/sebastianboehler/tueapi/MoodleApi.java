package io.github.sebastianboehler.tueapi;

import java.io.IOException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;

public final class MoodleApi {
    private static final String BASE = "https://moodle.zdv.uni-tuebingen.de";
    private static final Pattern SESSKEY = Pattern.compile("\"sesskey\"\\s*:\\s*\"([^\"]+)\"");
    private static final String SAML_RESPONSE = "SAML" + "Response";
    private static final String RELAY_STATE = "Relay" + "State";
    private static final String EVENT_PROCEED = "_eventId_" + "proceed";
    private static final String USER_FIELD = "j_" + "username";
    private static final String PASSWORD_FIELD = "j_" + "password";
    private final HttpTransport http;
    private final UniversityCredentials credentials;
    private boolean loggedIn;

    MoodleApi(HttpTransport http, UniversityCredentials credentials) {
        this.http = http;
        this.credentials = credentials;
    }

    public void login() throws IOException, TueApiException {
        UniversityCredentials creds = requireCredentials();
        HttpResponseData page = http.get(BASE + "/login/index.php");
        Document document = HtmlSupport.parse(page.text(), page.url);
        Element shib = document.selectFirst("a[href*=shibboleth], a[href*=Shibboleth]");
        if (shib == null) {
            throw new TueApiException("Could not find Moodle Shibboleth login link.");
        }
        HttpResponseData idp = http.get(HtmlSupport.resolve(page.url, shib.attr("href")));
        HtmlForm form = HtmlSupport.formWithInput(idp.text(), idp.url, PASSWORD_FIELD);
        form.payload.set(USER_FIELD, creds.username()).set(PASSWORD_FIELD, creds.password());
        form.payload.set(EVENT_PROCEED, form.payload.value(EVENT_PROCEED));
        completeSaml(http.postForm(form.actionUrl, form.payload));
        loggedIn = true;
    }

    public String dashboard(int eventLimit, int courseLimit, int recentLimit) throws IOException, TueApiException {
        String page = authenticatedPage(BASE + "/my/");
        String sesskey = sesskey(page);
        String events = ajax(sesskey, "core_calendar_get_action_events_by_timesort", "{\"limitnum\":" + eventLimit + "}", BASE + "/my/");
        String courses = ajax(sesskey, "core_course_get_enrolled_courses_by_timeline_classification", "{\"offset\":0,\"limit\":"
            + courseLimit + ",\"classification\":\"all\",\"sort\":\"fullname\"}", BASE + "/my/");
        String recent = ajax(sesskey, "block_recentlyaccesseditems_get_recent_items", "{\"limit\":" + recentLimit + "}", BASE + "/my/");
        return "{\"events\":" + JsonSupport.quote(events) + ",\"courses\":" + JsonSupport.quote(courses)
            + ",\"recent\":" + JsonSupport.quote(recent) + "}";
    }

    public String calendar(int days, int limit) throws IOException, TueApiException {
        String page = authenticatedPage(BASE + "/my/");
        return ajax(sesskey(page), "core_calendar_get_action_events_by_timesort", "{\"limitnum\":" + limit + "}", BASE + "/my/");
    }

    public String courses(String classification, int limit, int offset) throws IOException, TueApiException {
        String page = authenticatedPage(BASE + "/my/courses.php");
        String args = "{\"offset\":" + offset + ",\"limit\":" + limit + ",\"classification\":"
            + JsonSupport.quote(classification) + ",\"sort\":\"fullname\"}";
        return ajax(sesskey(page), "core_course_get_enrolled_courses_by_timeline_classification", args, BASE + "/my/courses.php");
    }

    public String categories() throws IOException, TueApiException {
        return authenticatedPage(BASE + "/course/index.php");
    }

    public String category(int categoryId) throws IOException, TueApiException {
        return authenticatedPage(BASE + "/course/index.php?categoryid=" + categoryId);
    }

    public String course(int courseId) throws IOException, TueApiException {
        return authenticatedPage(BASE + "/enrol/index.php?id=" + courseId);
    }

    public String grades(int limit) throws IOException, TueApiException {
        return authenticatedPage(BASE + "/grade/report/overview/index.php");
    }

    public String messages(int limit) throws IOException, TueApiException {
        return authenticatedPage(BASE + "/message/index.php");
    }

    public String notifications(int limit) throws IOException, TueApiException {
        return authenticatedPage(BASE + "/message/output/popup/notifications.php");
    }

    private String authenticatedPage(String url) throws IOException, TueApiException {
        ensureLoggedIn();
        HttpResponseData response = http.get(url);
        if (response.url.contains("/login/")) {
            throw new TueApiException("Moodle redirected back to login.");
        }
        return response.text();
    }

    private String ajax(String sesskey, String method, String args, String referer) throws IOException, TueApiException {
        String payload = "[{\"index\":0,\"methodname\":\"" + method + "\",\"args\":" + args + "}]";
        String url = HttpTransport.appendQuery(BASE + "/lib/ajax/service.php", new QueryParams().add("sesskey", sesskey).add("info", method));
        return http.postJson(url, payload, referer).text();
    }

    private void completeSaml(HttpResponseData response) throws IOException, TueApiException {
        HttpResponseData current = response;
        for (int attempt = 0; attempt < 6; attempt++) {
            if (current.url.startsWith(BASE) && !current.url.contains("/login/index.php")) {
                return;
            }
            if (current.text().contains(SAML_RESPONSE) && current.text().contains(RELAY_STATE)) {
                HtmlForm form = HtmlSupport.hiddenFormWithFields(current.text(), current.url, SAML_RESPONSE, RELAY_STATE);
                current = http.postForm(form.actionUrl, form.payload);
                continue;
            }
            if (current.url.contains("idp.uni-tuebingen.de") && current.text().contains(EVENT_PROCEED)) {
                HtmlForm form = HtmlSupport.hiddenFormWithFields(current.text(), current.url, EVENT_PROCEED);
                current = http.postForm(form.actionUrl, form.payload);
                continue;
            }
            break;
        }
        throw new TueApiException("Could not complete the Moodle SAML handoff.");
    }

    private String sesskey(String html) throws TueApiException {
        Matcher matcher = SESSKEY.matcher(html);
        if (!matcher.find()) {
            throw new TueApiException("Moodle page did not expose a sesskey.");
        }
        return matcher.group(1);
    }

    private void ensureLoggedIn() throws IOException, TueApiException {
        if (!loggedIn) {
            login();
        }
    }

    private UniversityCredentials requireCredentials() throws TueApiException {
        if (credentials == null) {
            throw new TueApiException("This Moodle call requires UniversityCredentials.");
        }
        return credentials;
    }
}
