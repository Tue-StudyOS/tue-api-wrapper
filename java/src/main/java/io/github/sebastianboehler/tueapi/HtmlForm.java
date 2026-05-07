package io.github.sebastianboehler.tueapi;

final class HtmlForm {
    final String actionUrl;
    final QueryParams payload;

    HtmlForm(String actionUrl, QueryParams payload) {
        this.actionUrl = actionUrl;
        this.payload = payload;
    }
}
