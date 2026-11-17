# Advising pages: discovery and topic search

The public advising reader discovers university pages and searches a local index.
It needs no login and sends no search terms to an external search engine. Start with:

```sh
tue-study advising-refresh
tue-study advising-discover
tue-study advising-search --query 'Anerkennung' --limit 10
tue-study advising-search --query 'Machine Learning' --limit 10
tue-study advising --target 'https://uni-tuebingen.de/path/to/advising-page/'
```

Python: `TuebingenPublicClient().directory.discover_advising()`,
`search_advising('Anerkennung')`, `refresh_advising()`, or `advising_page(url)`.
The individual-page reader requires an explicit page URL on every interface.
HTTP: `POST /api/people/advising/refresh`, `GET /api/people/advising/discover`,
`GET /api/people/advising/search?query=Anerkennung`, and
`GET /api/people/advising?url=...`.
MCP: `campus_advising_refresh`, `campus_advising_discover`, `campus_advising_search`, and
`campus_advising_page` in the `campus` service.

## Coverage and interpretation

Discovery starts with the university's [A–Z directory of subject advisers](https://uni-tuebingen.de/de/92),
the [topic-based advising overview](https://uni-tuebingen.de/studium/beratung-und-info/anlaufstellen-nach-thema/),
the [Informatik advising overview](https://uni-tuebingen.de/fakultaeten/mathematisch-naturwissenschaftliche-fakultaet/fachbereiche/informatik/studium/studierende/personen-und-kontakte/studienberatung/),
the [Erziehungswissenschaft FAQ](https://uni-tuebingen.de/fakultaeten/wirtschafts-und-sozialwissenschaftliche-fakultaet/faecher/fachbereich-sozialwissenschaften/erziehungswissenschaft/studium/studienberatung-faq/ansprechpartnerinnen/),
[Paul Stahl's page](https://uni-tuebingen.de/fakultaeten/mathematisch-naturwissenschaftliche-fakultaet/fachbereiche/informatik/lehrstuehle/kommunikationsnetze/staff/paul-stahl/),
and the [older Database Systems advising page](https://db.cs.uni-tuebingen.de/studienfachberatung/).
It follows advising, FAQ, topic-overview and university short links breadth first.
A refresh attempts up to 300 URLs, at most two links from the starting pages. It
attempts the first level before the second. `seed_links_discovered` and
`seed_links_attempted` show first-level coverage. `pages_skipped` counts links
within that depth that exceeded the request limit; `links_beyond_depth` counts
additional links found on the last level. `errors` lists individual failures.
These counts make incomplete coverage visible; discovery is not a complete
inventory of the university website.

The first search or discovery builds an index if one does not exist. Later calls
reuse `~/.tue-api-wrapper/advising-discovery.json`; `refreshed_at` is the UTC
time of its last refresh. Run `advising-refresh` to fetch current pages and retry
failed links. A failed primary-directory fetch leaves the previous index intact
and reports an error. Other failed pages are listed in the new index's `errors`.
The index is replaced atomically after the refresh finishes.

Search matches all query words as case-insensitive substrings in passage text or
its section heading. Results preserve the source page, section, text and links.
They may be degree-specific directory contacts, table rows, list items, or paragraphs. Explicit “can help” and
“cannot help” table rows have distinct kinds. Degree-to-person table rows and
FAQ sections retain their original context; they are not inferred assignments of
all topics to a named individual. Search is literal, not semantic: try related
German terms such as `Anerkennung` and `Anrechnung` separately.

The direct page reader supports the explicit responsibility tables on the two
individual Informatik pages. It retains contact details, guidance, referrals,
and source links, and rejects unsupported layouts. The other layouts are
available as search passages; they are not converted to a single-person record.
The older Database Systems page names a different adviser: use the page dates
and current university directory before relying on it.

Fetches are restricted to HTTPS on `uni-tuebingen.de` and
`db.cs.uni-tuebingen.de`, including redirects. Document links such as PDFs are
not indexed by this HTML reader.
