from __future__ import annotations

from email.utils import decode_rfc2231
from itertools import product
import re
from urllib.parse import parse_qsl, quote, unquote, urlparse

from bs4 import BeautifulSoup
import requests

from .alma_studyservice_client import (
    fetch_studyservice_contract,
    fetch_studyservice_documents_contract,
)
from .alma_studyservice_models import AlmaStudyServicePage
from .alma_academics_html import (
    extract_advanced_module_search_form,
    extract_module_search_form,
    parse_exam_overview,
    parse_module_search_page,
    parse_module_search_results,
    parse_module_search_results_page,
)
from .alma_catalog_tree_html import parse_course_catalog_page
from .alma_detail_client import fetch_public_module_detail
from .config import (
    AlmaLoginError,
    AlmaParseError,
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT_SECONDS,
    START_PAGE_PATH,
    STUDYSERVICE_PATH,
    TIMETABLE_PATH,
)
from .alma_timetable_html import parse_timetable_contract
from .alma_timetable_rooms import (
    enrich_calendar_events,
    enrich_calendar_occurrences,
    extract_timetable_room_entries,
)
from .html_contract import (
    build_term_export_url,
    extract_login_form,
)
from .ics import expand_ics_events, parse_ics_events
from .models import (
    AlmaCourseCatalogNode,
    AlmaDownloadedDocument,
    AlmaDocumentReport,
    AlmaEnrollmentPage,
    AlmaExamNode,
    AlmaModuleDetail,
    AlmaModuleSearchFilters,
    AlmaModuleSearchPage,
    AlmaModuleSearchResponse,
    TimetableResult,
)


class AlmaClient:
    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.session.headers.setdefault(
            "User-Agent",
            "tue-api-wrapper/0.1 (+https://alma.uni-tuebingen.de/)",
        )

    @property
    def start_page_url(self) -> str:
        return f"{self.base_url}{START_PAGE_PATH}"

    @property
    def timetable_url(self) -> str:
        return f"{self.base_url}{TIMETABLE_PATH}"

    @property
    def studyservice_url(self) -> str:
        return f"{self.base_url}{STUDYSERVICE_PATH}"

    def login(self, username: str, password: str) -> str:
        response = self.session.get(self.start_page_url, timeout=self.timeout_seconds)
        response.raise_for_status()

        login_form = extract_login_form(response.text, response.url)
        payload = dict(login_form.payload)
        payload["asdf"] = username
        payload["fdsa"] = password
        payload.setdefault("submit", "")

        login_response = self.session.post(
            login_form.action_url,
            data=payload,
            timeout=self.timeout_seconds,
            allow_redirects=True,
        )
        login_response.raise_for_status()

        if self._looks_logged_out(login_response.text):
            error_message = self._extract_login_error(login_response.text)
            if error_message:
                raise AlmaLoginError(error_message)
            raise AlmaLoginError("Alma login did not reach an authenticated page.")
        return login_response.text

    def fetch_timetable_page(self) -> str:
        response = self.session.get(self.timetable_url, timeout=self.timeout_seconds)
        response.raise_for_status()
        if self._looks_logged_out(response.text):
            raise AlmaLoginError("Session is not authenticated; the timetable page redirected back to login.")
        return response.text

    def fetch_timetable_for_term(self, term_label: str) -> TimetableResult:
        timetable_html = self.fetch_timetable_page()
        contract = parse_timetable_contract(timetable_html, self.timetable_url)
        terms = {option.label: option.value for option in contract.terms}
        resolved_term_label = term_label
        term_id = terms.get(term_label)
        if term_id is None:
            for label, value in terms.items():
                if value == term_label:
                    resolved_term_label = label
                    term_id = value
                    break
        if term_id is None and not terms and contract.export_url:
            resolved_term_label = contract.selected_term_label or term_label
            term_id = contract.selected_term_value or ""
        if term_id is None:
            available = ", ".join(sorted(terms))
            raise AlmaParseError(f"Unknown term '{term_label}'. Available terms: {available}")

        if contract.export_url is None:
            raise AlmaParseError("Could not find the timetable iCalendar export field.")
        export_url = build_term_export_url(contract.export_url, term_id) if term_id else contract.export_url
        calendar_response = self.session.get(export_url, timeout=self.timeout_seconds)
        calendar_response.raise_for_status()
        raw_ics = self._decode_calendar_response(calendar_response)
        if "BEGIN:VCALENDAR" not in raw_ics:
            raise AlmaParseError("Expected an iCalendar export but received a different response.")

        room_entries = extract_timetable_room_entries(timetable_html, self.timetable_url)
        events = enrich_calendar_events(parse_ics_events(raw_ics), room_entries)
        occurrences = enrich_calendar_occurrences(expand_ics_events(events, resolved_term_label), room_entries)
        return TimetableResult(
            term_label=resolved_term_label,
            term_id=term_id,
            export_url=export_url,
            raw_ics=raw_ics,
            events=events,
            occurrences=occurrences,
            available_terms=terms,
        )

    def fetch_studyservice_page(self) -> str:
        response = self.session.get(self.studyservice_url, timeout=self.timeout_seconds)
        response.raise_for_status()
        if self._looks_logged_out(response.text):
            raise AlmaLoginError("Session is not authenticated; the study service page redirected back to login.")
        return response.text

    def fetch_enrollment_page(self, *, term: str | None = None) -> AlmaEnrollmentPage:
        from .alma_enrollment_client import fetch_enrollment_page

        return fetch_enrollment_page(self, term=term)

    def fetch_exam_overview(self) -> tuple[AlmaExamNode, ...]:
        response = self.session.get(
            f"{self.base_url}/alma/pages/sul/examAssessment/personExamsReadonly.xhtml?_flowId=examsOverviewForPerson-flow"
            "&navigationPosition=hisinoneMeinStudium%2CexamAssessmentForStudent&recordRequest=true",
            timeout=self.timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()
        if self._looks_logged_out(response.text):
            raise AlmaLoginError("Session is not authenticated; the exam overview page redirected back to login.")
        return parse_exam_overview(response.text)

    def fetch_course_catalog(self) -> tuple[AlmaCourseCatalogNode, ...]:
        response = self.session.get(
            f"{self.base_url}/alma/pages/cm/exa/coursecatalog/showCourseCatalog.xhtml?_flowId=showCourseCatalog-flow"
            "&navigationPosition=studiesOffered%2CcourseoverviewShow&recordRequest=true",
            timeout=self.timeout_seconds,
            allow_redirects=True,
        )
        response.raise_for_status()
        if self._looks_logged_out(response.text):
            raise AlmaLoginError("Session is not authenticated; the course catalog page redirected back to login.")
        return parse_course_catalog_page(response.text)

    def fetch_study_planner(self):
        from .alma_planner_client import fetch_study_planner

        return fetch_study_planner(self)

    @property
    def public_module_search_url(self) -> str:
        return (
            f"{self.base_url}/alma/pages/cm/exa/curricula/moduleDescriptionSearch.xhtml"
            "?_flowId=searchElementsInModuleDescription-flow"
            "&navigationPosition=studiesOffered%2CmoduleDescriptions%2CsearchElementsInModuleDescription"
            "&recordRequest=true"
        )

    def search_module_descriptions(self, query: str) -> AlmaModuleSearchPage:
        query = query.strip()
        if not query:
            raise AlmaParseError("A non-empty module search query is required.")

        response = self.session.get(self.public_module_search_url, timeout=self.timeout_seconds, allow_redirects=True)
        response.raise_for_status()

        form = extract_module_search_form(response.text, response.url)
        payload = dict(form.payload)
        payload[form.query_field_name] = query
        payload["activePageElementId"] = "genericSearchMask:buttonsBottom:search"
        payload["genericSearchMask:buttonsBottom:search"] = "Suchen"

        response = self.session.post(form.action_url, data=payload, timeout=self.timeout_seconds, allow_redirects=True)
        response.raise_for_status()
        return AlmaModuleSearchPage(form=form, results=parse_module_search_results(response.text))

    def fetch_public_module_search_filters(self) -> AlmaModuleSearchFilters:
        contract = self._fetch_advanced_public_module_search_contract()
        return contract.filters

    def fetch_public_module_detail(self, detail_url: str) -> AlmaModuleDetail:
        return fetch_public_module_detail(self, detail_url)

    def search_public_module_descriptions(
        self,
        *,
        query: str = "",
        title: str = "",
        number: str = "",
        element_types: tuple[str, ...] = (),
        languages: tuple[str, ...] = (),
        degrees: tuple[str, ...] = (),
        subjects: tuple[str, ...] = (),
        faculties: tuple[str, ...] = (),
        max_results: int = 100,
    ) -> AlmaModuleSearchResponse:
        query = query.strip()
        title = title.strip()
        number = number.strip()
        element_types = tuple(dict.fromkeys(value.strip() for value in element_types if value.strip()))
        languages = tuple(dict.fromkeys(value.strip() for value in languages if value.strip()))
        degrees = tuple(dict.fromkeys(value.strip() for value in degrees if value.strip()))
        subjects = tuple(dict.fromkeys(value.strip() for value in subjects if value.strip()))
        faculties = tuple(dict.fromkeys(value.strip() for value in faculties if value.strip()))
        max_results = max(1, min(max_results, 300))

        if not any([query, title, number, element_types, languages, degrees, subjects, faculties]):
            raise AlmaParseError("At least one public module-search filter must be provided.")

        dimensions = [values or ("",) for values in (element_types, languages, degrees, subjects, faculties)]
        combinations = list(product(*dimensions))
        if len(combinations) > 24:
            raise AlmaParseError("Too many filter combinations requested at once.")

        unique_results: list = []
        seen_keys: set[tuple[str | None, str, str | None]] = set()
        total_results: int | None = 0 if len(combinations) == 1 else None
        total_pages: int | None = 0 if len(combinations) == 1 else None
        truncated = False

        for combo in combinations:
            response = self._search_public_module_descriptions_once(
                query=query,
                title=title,
                number=number,
                element_type=combo[0],
                language=combo[1],
                degree=combo[2],
                subject=combo[3],
                faculty=combo[4],
                max_results=max_results,
            )
            if total_results is not None:
                total_results = response.total_results
            if total_pages is not None:
                total_pages = response.total_pages
            truncated = truncated or response.truncated

            for result in response.results:
                key = (result.detail_url, result.title, result.element_type)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                unique_results.append(result)
                if len(unique_results) >= max_results:
                    truncated = True
                    break
            if len(unique_results) >= max_results:
                break

        return AlmaModuleSearchResponse(
            results=tuple(unique_results[:max_results]),
            total_results=total_results,
            returned_results=min(len(unique_results), max_results),
            total_pages=total_pages,
            truncated=truncated,
        )

    def _fetch_advanced_public_module_search_contract(self):
        response = self.session.get(self.public_module_search_url, timeout=self.timeout_seconds, allow_redirects=True)
        response.raise_for_status()

        contract = extract_advanced_module_search_form(response.text, response.url)
        if contract.fields.degree is not None:
            return contract

        if contract.toggle_advanced_button_name is None:
            raise AlmaParseError("Could not reveal Alma advanced module-search criteria.")

        payload = dict(contract.payload)
        payload["activePageElementId"] = contract.toggle_advanced_button_name
        payload[contract.toggle_advanced_button_name] = "Erweiterte Suche"
        response = self.session.post(contract.action_url, data=payload, timeout=self.timeout_seconds, allow_redirects=True)
        response.raise_for_status()
        return extract_advanced_module_search_form(response.text, response.url)

    def _search_public_module_descriptions_once(
        self,
        *,
        query: str,
        title: str,
        number: str,
        element_type: str,
        language: str,
        degree: str,
        subject: str,
        faculty: str,
        max_results: int,
    ) -> AlmaModuleSearchResponse:
        contract = self._fetch_advanced_public_module_search_contract()
        payload = dict(contract.payload)
        payload[contract.query_field_name] = query
        if contract.fields.title is not None:
            payload[contract.fields.title] = title
        if contract.fields.number is not None:
            payload[contract.fields.number] = number
        if contract.fields.element_type is not None:
            payload[contract.fields.element_type] = element_type
        if contract.fields.language is not None:
            payload[contract.fields.language] = language
        if contract.fields.degree is not None:
            payload[contract.fields.degree] = degree
        if contract.fields.subject is not None:
            payload[contract.fields.subject] = subject
        if contract.fields.faculty is not None:
            payload[contract.fields.faculty] = faculty
        payload["activePageElementId"] = contract.search_button_name
        payload[contract.search_button_name] = "Suchen"

        response = self.session.post(contract.action_url, data=payload, timeout=self.timeout_seconds, allow_redirects=True)
        response.raise_for_status()

        results_page = parse_module_search_results_page(response.text, response.url)
        if (
            results_page.action_url is not None
            and results_page.rows_input_name is not None
            and results_page.rows_refresh_name is not None
            and max_results > len(results_page.results)
        ):
            refresh_payload = dict(results_page.payload)
            refresh_payload[results_page.rows_input_name] = str(max_results)
            refresh_payload["activePageElementId"] = results_page.rows_refresh_name
            refresh_payload[results_page.rows_refresh_name] = ""
            response = self.session.post(
                results_page.action_url,
                data=refresh_payload,
                timeout=self.timeout_seconds,
                allow_redirects=True,
            )
            response.raise_for_status()
            results_page = parse_module_search_results_page(response.text, response.url)

        total_results = results_page.total_results
        returned_results = min(len(results_page.results), max_results)
        truncated = (total_results is not None and total_results > returned_results) or returned_results >= max_results
        return AlmaModuleSearchResponse(
            results=results_page.results[:max_results],
            total_results=total_results,
            returned_results=returned_results,
            total_pages=results_page.total_pages,
            truncated=truncated,
        )

    def fetch_studyservice_contract(self) -> AlmaStudyServicePage:
        return fetch_studyservice_documents_contract(self)

    def fetch_studyservice_tab(self, label: str) -> AlmaStudyServicePage:
        return fetch_studyservice_contract(self, tab_label=label)

    def list_studyservice_reports(self) -> tuple[AlmaDocumentReport, ...]:
        return self.fetch_studyservice_contract().reports

    def download_current_studyservice_document(self) -> AlmaDownloadedDocument:
        contract = self.fetch_studyservice_contract()
        if contract.latest_download_url is None:
            raise AlmaParseError("The study service page does not currently expose a document download link.")
        return self._download_document(contract.latest_download_url)

    def download_document_by_id(self, doc_id: str) -> AlmaDownloadedDocument:
        doc_id = doc_id.strip()
        if not doc_id:
            raise AlmaParseError("A non-empty Alma document id is required.")
        download_url = f"{self.base_url}/alma/rds?state=docdownload&docId={quote(doc_id)}"
        return self._download_document(download_url)

    def list_enrollment_reports(self) -> tuple[AlmaDocumentReport, ...]:
        from .alma_enrollment_client import list_enrollment_reports

        return list_enrollment_reports(self)

    def download_enrollment_report(
        self,
        *,
        trigger_name: str | None = None,
        term: str | None = None,
    ) -> AlmaDownloadedDocument:
        from .alma_enrollment_client import download_enrollment_report

        return download_enrollment_report(self, trigger_name=trigger_name, term=term)

    @staticmethod
    def _extract_login_error(html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)
        match = re.search(r"Fehler:\s*(.+?)\s*(Studierende, die aktuell|$)", text, flags=re.DOTALL)
        if not match:
            return None
        return re.sub(r"\s+", " ", match.group(1)).strip()

    @staticmethod
    def _looks_logged_out(html: str) -> bool:
        soup = BeautifulSoup(html, "html.parser")
        body = soup.find("body")
        classes = set(body.get("class", [])) if body else set()
        if "notloggedin" in classes:
            return True
        return soup.find("form", id="loginForm") is not None

    def _download_document(self, download_url: str) -> AlmaDownloadedDocument:
        response = self.session.get(download_url, timeout=self.timeout_seconds, allow_redirects=True)
        response.raise_for_status()
        if not (
            response.headers.get("content-type", "").startswith("application/pdf")
            or response.content.startswith(b"%PDF-")
        ):
            snippet = response.text[:200].strip() if response.text else ""
            raise AlmaParseError(f"Expected a PDF document but received a different response: {snippet}")
        return AlmaDownloadedDocument(
            source_url=download_url,
            final_url=response.url,
            filename=self._extract_download_filename(response, download_url),
            content_type=response.headers.get("content-type"),
            data=response.content,
        )

    @staticmethod
    def _decode_calendar_response(response: requests.Response) -> str:
        for encoding in ("utf-8", response.encoding, response.apparent_encoding, "latin-1"):
            if not encoding:
                continue
            try:
                return response.content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return response.content.decode("utf-8", errors="replace")

    @staticmethod
    def _extract_download_filename(response: requests.Response, fallback_url: str) -> str:
        content_disposition = response.headers.get("content-disposition", "")
        encoded_match = re.search(r"filename\*=([^;]+)", content_disposition, flags=re.IGNORECASE)
        if encoded_match:
            charset, _, encoded_value = decode_rfc2231(encoded_match.group(1).strip())
            if encoded_value:
                return unquote(encoded_value, encoding=charset or "utf-8")

        plain_match = re.search(r'filename="([^"]+)"', content_disposition, flags=re.IGNORECASE)
        if plain_match:
            return plain_match.group(1)

        parsed = urlparse(response.url or fallback_url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        doc_name = query.get("docName")
        if doc_name:
            return doc_name
        return "alma-document.pdf"
