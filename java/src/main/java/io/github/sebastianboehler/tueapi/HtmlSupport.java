package io.github.sebastianboehler.tueapi;

import java.net.MalformedURLException;
import java.net.URL;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

final class HtmlSupport {
    private HtmlSupport() {}

    static Document parse(String html, String url) {
        return Jsoup.parse(html, url);
    }

    static HtmlForm formById(String html, String pageUrl, String id) throws TueApiException {
        Document document = parse(html, pageUrl);
        Element form = document.selectFirst("form#" + id);
        if (form == null) {
            throw new TueApiException("Could not find form #" + id);
        }
        return form(form, pageUrl);
    }

    static HtmlForm formWithInput(String html, String pageUrl, String inputName) throws TueApiException {
        Document document = parse(html, pageUrl);
        for (Element form : document.select("form")) {
            if (hasField(form, inputName)) {
                return form(form, pageUrl);
            }
        }
        throw new TueApiException("Could not find form with input " + inputName);
    }

    static HtmlForm hiddenFormWithFields(String html, String pageUrl, String... fields) throws TueApiException {
        Document document = parse(html, pageUrl);
        for (Element form : document.select("form")) {
            boolean matches = true;
            for (String field : fields) {
                matches = matches && hasField(form, field);
            }
            if (matches) {
                return form(form, pageUrl);
            }
        }
        throw new TueApiException("Could not find hidden handoff form");
    }

    private static boolean hasField(Element form, String name) {
        for (Element field : form.select("[name]")) {
            if (name.equals(field.attr("name"))) {
                return true;
            }
        }
        return false;
    }

    static HtmlForm form(Element form, String pageUrl) {
        QueryParams payload = new QueryParams();
        Elements fields = form.select("input[name], select[name], textarea[name]");
        for (Element field : fields) {
            String tag = field.tagName();
            String type = field.attr("type");
            if ("button".equals(type) || "file".equals(type) || "image".equals(type) || "reset".equals(type)) {
                continue;
            }
            if ("checkbox".equals(type) && !field.hasAttr("checked")) {
                continue;
            }
            if ("select".equals(tag)) {
                Element selected = field.selectFirst("option[selected]");
                payload.add(field.attr("name"), selected == null ? "" : selected.attr("value"));
            } else {
                payload.add(field.attr("name"), field.attr("value"));
            }
        }
        return new HtmlForm(resolve(pageUrl, form.attr("action")), payload);
    }

    static String resolve(String pageUrl, String href) {
        try {
            return new URL(new URL(pageUrl), href).toString();
        } catch (MalformedURLException error) {
            return href;
        }
    }
}
