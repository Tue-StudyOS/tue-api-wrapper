from __future__ import annotations

from .alma_course_search_html import (
    COURSE_SEARCH_URL,
    _parse_course_search_results,
    extract_course_search_form,
    parse_course_search_page,
    validate_course_search_response,
)
from .alma_course_search_models import AlmaCourseSearchPage
from .client import AlmaClient
from .config import AlmaParseError


def search_courses(
    client: AlmaClient,
    *,
    query: str = "",
    term: str | None = None,
    limit: int | None = None,
) -> AlmaCourseSearchPage:
    response = client.session.get(
        COURSE_SEARCH_URL,
        timeout=client.timeout_seconds,
        allow_redirects=True,
    )
    response.raise_for_status()

    normalized_query = query.strip()
    if normalized_query or term is not None:
        form = extract_course_search_form(response.text, response.url)
        if term is not None and term not in {option.value for option in form.term_options}:
            raise AlmaParseError("Invalid Alma search term; use a value from term_options, not a timetable period ID.")
        payload = dict(form.payload)
        payload[form.query_field_name] = normalized_query
        if term is not None:
            payload[form.term_field_name] = term
        payload["activePageElementId"] = form.search_button_name
        payload[form.search_button_name] = "Suchen"
        response = client.session.post(
            form.action_url,
            data=payload,
            timeout=client.timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()
        validate_course_search_response(response.text)
        selected_term = next(
            (option for option in form.term_options if option.value == (term or "")),
            next((option for option in form.term_options if option.is_selected), None),
        )
        page = AlmaCourseSearchPage(
            page_url=response.url,
            query=normalized_query,
            selected_term_value=selected_term.value if selected_term is not None else None,
            selected_term_label=selected_term.label if selected_term is not None else None,
            term_options=form.term_options,
            results=_parse_course_search_results(response.text, response.url),
        )
    else:
        page = parse_course_search_page(response.text, response.url, query=normalized_query)

    if limit is None:
        return page

    bounded_limit = max(1, limit)
    return AlmaCourseSearchPage(
        page_url=page.page_url,
        query=page.query,
        selected_term_value=page.selected_term_value,
        selected_term_label=page.selected_term_label,
        term_options=page.term_options,
        results=page.results[:bounded_limit],
    )
