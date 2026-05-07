package io.github.sebastianboehler.tueapi;

import java.io.IOException;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

public final class AlmaApi {
    private static final String BASE = "https://alma.uni-tuebingen.de";
    private static final String START = BASE + "/alma/pages/cs/sys/portal/hisinoneStartPage.faces";
    private static final String CURRENT = BASE + "/alma/pages/cm/exa/timetable/currentLectures.xhtml"
        + "?_flowId=showEventsAndExaminationsOnDate-flow&navigationPosition=studiesOffered,currentLecturesGeneric&recordRequest=true";
    private static final String EXAMS = BASE + "/alma/pages/sul/examAssessment/personExamsReadonly.xhtml"
        + "?_flowId=examsOverviewForPerson-flow&navigationPosition=hisinoneMeinStudium%2CexamAssessmentForStudent&recordRequest=true";

    private final HttpTransport http;
    private final UniversityCredentials credentials;
    private boolean loggedIn;

    AlmaApi(HttpTransport http, UniversityCredentials credentials) {
        this.http = http;
        this.credentials = credentials;
    }

    public void login() throws IOException, TueApiException {
        UniversityCredentials creds = requireCredentials();
        HttpResponseData page = http.get(START);
        HtmlForm form;
        try {
            form = HtmlSupport.formById(page.text(), page.url, "loginForm");
        } catch (TueApiException error) {
            form = HtmlSupport.formById(page.text(), page.url, "mobileLoginForm");
        }
        form.payload.set("asdf", creds.username()).set("fdsa", creds.password()).set("submit", "");
        HttpResponseData response = http.postForm(form.actionUrl, form.payload);
        if (looksLoggedOut(response.text())) {
            throw new TueApiException("Alma login did not reach an authenticated page.");
        }
        loggedIn = true;
    }

    public String currentLectures(String date, int limit) throws IOException, TueApiException {
        HttpResponseData response = http.get(CURRENT);
        if (date != null && !date.trim().isEmpty()) {
            HtmlForm form = HtmlSupport.formById(response.text(), response.url, "showEventsAndExaminationsOnDateForm");
            Document document = HtmlSupport.parse(response.text(), response.url);
            Element dateField = document.selectFirst("input[name$=':date']");
            Element search = document.selectFirst("button[name$=':searchButtonId']");
            if (dateField == null || search == null) {
                throw new TueApiException("Could not identify Alma current-lectures form fields.");
            }
            form.payload.set(dateField.attr("name"), date);
            form.payload.set("activePageElementId", search.attr("name"));
            form.payload.set(search.attr("name"), "Suchen");
            response = http.postForm(form.actionUrl, form.payload);
        }
        return parseCurrentLectures(response.text(), response.url, limit);
    }

    public String exams(int limit) throws IOException, TueApiException {
        ensureLoggedIn();
        return parseExams(http.get(EXAMS).text(), limit);
    }

    public String timetable(String term) throws IOException, TueApiException {
        ensureLoggedIn();
        return http.get(BASE + "/alma/pages/cm/exa/timetable/studentTimetable.xhtml"
            + "?_flowId=studentSchedule-flow&navigationPosition=hisinoneMeinStudium%2CstudentSchedule").text();
    }

    public String enrollments() throws IOException, TueApiException {
        ensureLoggedIn();
        return http.get(BASE + "/alma/pages/cm/exa/enrollment/info/start.xhtml"
            + "?_flowId=searchOwnEnrollmentInfo-flow&navigationPosition=hisinoneMeinStudium%2ChisinoneOwnEnrollmentList&recordRequest=true").text();
    }

    public String studyservice() throws IOException, TueApiException {
        ensureLoggedIn();
        return http.get(BASE + "/alma/pages/cs/sys/portal/subMenu.faces?navigationPosition=hisinoneMeinStudium%2Cstudyservice").text();
    }

    public String moduleSearch(String query, int maxResults) throws IOException, TueApiException {
        String url = BASE + "/alma/pages/cm/exa/curricula/moduleDescriptionSearch.xhtml"
            + "?_flowId=searchElementsInModuleDescription-flow&navigationPosition=studiesOffered%2CmoduleDescriptions%2CsearchElementsInModuleDescription&recordRequest=true";
        HttpResponseData page = http.get(url);
        if (query == null || query.trim().isEmpty()) {
            return page.text();
        }
        Document document = HtmlSupport.parse(page.text(), page.url);
        Element formNode = document.selectFirst("form");
        Element textInput = document.selectFirst("input[type=text][name]");
        Element search = document.selectFirst("button[name$=':search'], input[type=submit][name]");
        if (formNode == null || textInput == null || search == null) {
            throw new TueApiException("Could not identify Alma module-search fields.");
        }
        HtmlForm form = HtmlSupport.form(formNode, page.url);
        form.payload.set(textInput.attr("name"), query);
        form.payload.set("activePageElementId", search.attr("name"));
        form.payload.set(search.attr("name"), "Suchen");
        return http.postForm(form.actionUrl, form.payload).text();
    }

    public String moduleDetail(String url) throws IOException, TueApiException {
        return http.get(url).text();
    }

    public String catalog(String term, int limit) throws IOException, TueApiException {
        ensureLoggedIn();
        return http.get(BASE + "/alma/pages/cm/exa/coursecatalog/showCourseCatalog.xhtml"
            + "?_flowId=showCourseCatalog-flow&navigationPosition=studiesOffered%2CcourseoverviewShow&recordRequest=true").text();
    }

    private void ensureLoggedIn() throws IOException, TueApiException {
        if (!loggedIn) {
            login();
        }
    }

    private UniversityCredentials requireCredentials() throws TueApiException {
        if (credentials == null || credentials.username() == null || credentials.password() == null) {
            throw new TueApiException("This Alma call requires UniversityCredentials.");
        }
        return credentials;
    }

    private static boolean looksLoggedOut(String html) {
        Document document = HtmlSupport.parse(html, START);
        return document.selectFirst("body.notloggedin") != null || document.selectFirst("form#loginForm") != null;
    }

    private static String parseCurrentLectures(String html, String pageUrl, int limit) {
        Document document = HtmlSupport.parse(html, pageUrl);
        Element date = document.selectFirst("input[name$=':date']");
        Element table = document.selectFirst("table[id$=coursesAndExaminationsOnDateListTableTable]");
        StringBuilder json = new StringBuilder("{");
        json.append(JsonSupport.pair("page_url", pageUrl)).append(",");
        json.append(JsonSupport.pair("selected_date", date == null ? null : date.attr("value"))).append(",\"results\":[");
        if (table != null) {
            int count = 0;
            for (Element row : table.select("tr")) {
                Elements cells = row.select("td");
                if (cells.size() < 13 || (limit > 0 && count >= limit)) {
                    continue;
                }
                if (count++ > 0) {
                    json.append(",");
                }
                json.append("{")
                    .append(JsonSupport.pair("title", text(cells.get(1)))).append(",")
                    .append(JsonSupport.pair("start", text(cells.get(2)))).append(",")
                    .append(JsonSupport.pair("end", text(cells.get(3)))).append(",")
                    .append(JsonSupport.pair("number", text(cells.get(4)))).append(",")
                    .append(JsonSupport.pair("event_type", text(cells.get(6)))).append(",")
                    .append(JsonSupport.pair("lecturer", text(cells.get(8)))).append(",")
                    .append(JsonSupport.pair("building", text(cells.get(9)))).append(",")
                    .append(JsonSupport.pair("room", text(cells.get(10))))
                    .append("}");
            }
        }
        return json.append("]}").toString();
    }

    private static String parseExams(String html, int limit) {
        Document document = HtmlSupport.parse(html, EXAMS);
        StringBuilder json = new StringBuilder("[");
        int count = 0;
        for (Element row : document.select("table.treeTableWithIcons tr")) {
            Element title = row.selectFirst("[id$=':defaulttext'], [id$=':unDeftxt']");
            if (title == null || (limit > 0 && count >= limit)) {
                continue;
            }
            if (count++ > 0) {
                json.append(",");
            }
            json.append("{")
                .append("\"level\":").append(level(row)).append(",")
                .append(JsonSupport.pair("title", title.text())).append(",")
                .append(JsonSupport.pair("number", field(row, "elementnr"))).append(",")
                .append(JsonSupport.pair("attempt", field(row, "attempt"))).append(",")
                .append(JsonSupport.pair("grade", field(row, "grade"))).append(",")
                .append(JsonSupport.pair("cp", field(row, "bonus"))).append(",")
                .append(JsonSupport.pair("status", field(row, "workstatus")))
                .append("}");
        }
        return json.append("]").toString();
    }

    private static int level(Element row) {
        for (String name : row.classNames()) {
            if (name.startsWith("treeTableCellLevel")) {
                return Integer.parseInt(name.substring("treeTableCellLevel".length()));
            }
        }
        return 0;
    }

    private static String field(Element row, String suffix) {
        Element element = row.selectFirst("[id$=':" + suffix + "']");
        return element == null ? null : text(element);
    }

    private static String text(Element element) {
        String value = element.text().replaceAll("\\s+", " ").trim();
        return value.isEmpty() ? null : value;
    }
}
