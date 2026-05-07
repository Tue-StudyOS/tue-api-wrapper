package io.github.sebastianboehler.tueapi;

import java.io.IOException;

public final class ProductApi {
    private static final String TALKS = "https://talks.tuebingen.ai/api";
    private static final String PEOPLE = "https://epv-welt.uni-tuebingen.de/RestrictedPages/StartSearch.aspx";
    private final HttpTransport http;

    ProductApi(HttpTransport http) {
        this.http = http;
    }

    public String peopleSearch(String query) throws IOException, TueApiException {
        HttpResponseData page = http.get(PEOPLE);
        HtmlForm form = HtmlSupport.formWithInput(page.text(), page.url, "ctl00$ContentPlaceHolder1$NameTextBox");
        form.payload.set("ctl00$ContentPlaceHolder1$NameTextBox", query);
        form.payload.set("ctl00$ContentPlaceHolder1$SearchButton", "Suchen");
        return http.postForm(form.actionUrl, form.payload).text();
    }

    public String talks(String query, int limit) throws IOException, TueApiException {
        return http.get(TALKS + "/talks?").text();
    }

    public String talk(int talkId) throws IOException, TueApiException {
        return http.get(TALKS + "/talks/" + talkId).text();
    }

    public String praxisportalFilters() throws TueApiException {
        throw new TueApiException("Native Praxisportal Algolia filters are not ported in Java yet.");
    }

    public String praxisportalSearch(String query, int page, int perPage) throws TueApiException {
        throw new TueApiException("Native Praxisportal Algolia search is not ported in Java yet.");
    }

    public String praxisportalProject(int projectId) throws TueApiException {
        throw new TueApiException("Native Praxisportal project detail is not ported in Java yet.");
    }
}
