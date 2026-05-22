from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.campus_client import (
    parse_building_detail_page,
    parse_building_directory_page,
    parse_canteen_page,
)
from tue_api_wrapper.event_calendar_client import parse_university_events_feed
from tue_api_wrapper.fitness_client import (
    parse_kuf_occupancy_page,
    parse_kuf_training_count_image,
)
from tue_api_wrapper.praxisportal_client import (
    build_praxisportal_filter_expression,
    build_praxisportal_filter_options,
    build_praxisportal_subscription_query,
    map_praxisportal_subscription,
    map_praxisportal_detail,
)
from tue_api_wrapper.timms_client import parse_timms_item_page, parse_timms_player_page, parse_timms_tree_page
from tue_api_wrapper.talks_client import build_talks_response, map_talk


class PublicProductContractTests(unittest.TestCase):
    def test_parse_timms_item_page_extracts_metadata_and_citations(self) -> None:
        html = """
        <html><body>
          <div class="creator">Lensch, Hendrik (2013)</div>
          <div class="title">Vorlesung Informatik II, 32. Stunde</div>
          <iframe src="/Player/EPlayer?id=UT_20130620_002_info2b_0001&t=0.0"></iframe>
          <a class="citedown" href="/api/Cite?id=UT_20130620_002_info2b_0001&format=bibtex">bibtex</a>
          <table>
            <tr><td class="md-name">title:</td><td class="md-val">Vorlesung Informatik II, 32. Stunde</td></tr>
            <tr><td class="md-name">language:</td><td class="md-val">ger</td></tr>
            <tr><td class="md-name">rights:</td><td class="md-val">Url: <a href="https://timmsstatic.uni-tuebingen.de/rights">rights</a></td></tr>
          </table>
        </body></html>
        """

        detail = parse_timms_item_page(html, "https://timms.uni-tuebingen.de/tp/UT_20130620_002_info2b_0001")

        self.assertEqual(detail.item_id, "UT_20130620_002_info2b_0001")
        self.assertEqual(detail.title, "Vorlesung Informatik II, 32. Stunde")
        self.assertEqual(detail.creator, "Lensch, Hendrik (2013)")
        self.assertTrue(detail.player_url.endswith("/Player/EPlayer?id=UT_20130620_002_info2b_0001&t=0.0"))
        self.assertIn("bibtex", detail.citation_downloads)
        self.assertEqual(detail.metadata[1].label, "language")
        self.assertEqual(detail.metadata[1].value, "ger")
        self.assertEqual(detail.metadata[2].url, "https://timmsstatic.uni-tuebingen.de/rights")

    def test_parse_timms_player_page_decodes_stream_variants(self) -> None:
        payload = base64.b64encode(
            json.dumps(
                [
                    {
                        "Width": 512,
                        "Height": 288,
                        "Bitrate": 364,
                        "Url": "https://timms-ms09.uni-tuebingen.de/sample.512x288b0364.mp4",
                        "Provider": "https",
                        "Streamer": "timms-ms09.uni-tuebingen.de",
                    },
                    {
                        "Width": 640,
                        "Height": 360,
                        "Bitrate": 564,
                        "Url": "https://timms-ms09.uni-tuebingen.de/sample.640x360b0564.mp4",
                        "Provider": "https",
                        "Streamer": "timms-ms09.uni-tuebingen.de",
                    },
                ]
            ).encode("utf-8")
        ).decode("ascii")
        html = f"<html><script>var mytok = '{payload}';</script></html>"

        streams = parse_timms_player_page(html)

        self.assertEqual(len(streams), 2)
        self.assertEqual(streams[0].height, 288)
        self.assertEqual(streams[1].bitrate, 564)
        self.assertTrue(streams[1].url.endswith("sample.640x360b0564.mp4"))

    def test_parse_timms_tree_page_merges_preview_and_title_links(self) -> None:
        html = """
        <html><body><div id="content">
          <div class="opennodecontainer">
            <div class="opennode"><a href="/List/OpenNode?nodepath=/A&nodeid=n1">A</a></div>
            <table class="leavecontainer">
              <tr>
                <td><a href="/tp/UT_20200421_001_theoinf_0001"><img alt="preview" src="/prev.jpg" /></a></td>
                <td><a class="uniblue" href="/tp/UT_20200421_001_theoinf_0001">Vorlesung Theoretische Informatik, 1. Stunde</a><br />00:34:22</td>
              </tr>
            </table>
          </div>
        </div></body></html>
        """

        page = parse_timms_tree_page(html, "https://timms.uni-tuebingen.de/List/Browse")

        self.assertEqual(len(page.items), 1)
        self.assertEqual(page.items[0].item_id, "UT_20200421_001_theoinf_0001")
        self.assertEqual(page.items[0].title, "Vorlesung Theoretische Informatik, 1. Stunde")

    def test_map_praxisportal_detail_and_filter_options(self) -> None:
        detail = map_praxisportal_detail(
            {
                "id": 55953,
                "title": "Cyber-Sicherheit",
                "job_description": "Build and secure distributed systems.",
                "requirements": "Python and networking.",
                "location": "Köln / München",
                "created_at": 1751355723000,
                "start_date": 1798761600,
                "end_date": None,
                "project_type": [{"id": 1, "name": "Internship"}],
                "industry": [{"id": 35, "title": "Informationsmanagement, -technologie"}],
                "organization": [{"id": 1320, "name": "Bundesamt für Verfassungsschutz", "logo": "https://example/logo.png"}],
            }
        )
        options = build_praxisportal_filter_options({"35": 3479, "47": 1948}, {35: "Informationsmanagement, -technologie", 47: "Technik, Technologie"})

        self.assertEqual(detail.id, 55953)
        self.assertEqual(detail.project_types, ["Internship"])
        self.assertEqual(detail.organizations[0].name, "Bundesamt für Verfassungsschutz")
        self.assertEqual([option.label for option in options], ["Informationsmanagement, -technologie", "Technik, Technologie"])

    def test_build_praxisportal_filter_expression_matches_har_facets(self) -> None:
        expression = build_praxisportal_filter_expression(
            project_type_ids=(1, 3),
            project_subtype_ids=(2,),
            industry_ids=(29, 31),
            postal_codes=("70794",),
            organization_ids=(338,),
        )

        self.assertIn("(project_type.id:1 OR project_type.id:3 OR subproject_type.id:2)", expression)
        self.assertIn("(industry.id:29 OR industry.id:31)", expression)
        self.assertIn("(postal_code:70794)", expression)
        self.assertIn("(organization.id:338)", expression)
        self.assertIn("blocked<1", expression)

    def test_build_praxisportal_subscription_query_matches_har_payload(self) -> None:
        query = build_praxisportal_subscription_query(
            text=("machine learning",),
            project_type_ids=(1, 3),
            project_subtype_ids=(2,),
            industry_ids=(29, 31),
            postal_codes=("70794",),
        )

        self.assertEqual(
            query.create_payload(),
            {
                "in_english": False,
                "start_date": "",
                "end_date": "",
                "text": ["machine learning"],
                "industries": ["29", "31"],
                "project_subtypes": ["2"],
                "postal_code": ["70794"],
                "project_type_id": ["1", "3"],
                "version": "2.0",
            },
        )

    def test_map_praxisportal_subscription_decodes_keyword_query(self) -> None:
        subscription = map_praxisportal_subscription(
            {
                "id": 13964,
                "user_id": 52548,
                "query_id": 13999,
                "subscription_type_id": 1,
                "created_at": 1778236180000,
                "updated_at": 1778236180000,
                "active": 1,
                "keyword": {
                    "id": 13999,
                    "query": (
                        '{"in_english":false,"start_date":null,"end_date":null,"text":[],'
                        '"industries":["29","31"],"project_subtypes":["2"],'
                        '"postal_code":["70794"],"project_type_id":["1","3"],"version":"2.0"}'
                    ),
                },
                "subscription_type": {
                    "id": 1,
                    "title": "Erhalte sofort eine Email wenn ein passendes Projekt veröffentlicht wird.",
                    "short_name": "1_hour",
                },
            }
        )

        self.assertTrue(subscription.active)
        self.assertEqual(subscription.query.postal_code, ["70794"])
        self.assertEqual(subscription.query.project_type_id, ["1", "3"])
        self.assertEqual(subscription.subscription_type.short_name, "1_hour")

    def test_parse_campus_pages_extract_directory_and_detail(self) -> None:
        directory_html = """
        <html><body>
          <table class="ut-table--striped"><tr><td><a href="/universitaet/standort-und-anfahrt/lageplaene/adressenliste/#c1">A B C</a></td></tr></table>
          <a href="/universitaet/standort-und-anfahrt/lageplaene/karte-a-morgenstelle/">Karte A: Morgenstelle</a>
          <table class="ut-table--striped">
            <tr><td><a class="internal-link" href="/universitaet/standort-und-anfahrt/lageplaene/karte-a-morgenstelle/auf-der-morgenstelle-26/">Auf der Morgenstelle 26</a></td></tr>
            <tr><td><a class="internal-link" href="/universitaet/standort-und-anfahrt/lageplaene/karte-d-altstadt/alte-aula/">Alte Aula</a></td></tr>
          </table>
        </body></html>
        """
        building_html = """
        <html><body>
          <main id="ut-identifier--main-content">
            <h1>Lagepläne - Karte A</h1>
            <ul class="ut-list"><li><strong>Mensa II Morgenstelle und Cafeteria</strong></li></ul>
            <div class="column-count-0"><p>Auf der Morgenstelle 26<br/>72076 Tübingen</p></div>
            <table class="ut-table--striped">
              <tr><td>Auf der Morgenstelle 26</td><td><strong>Nr. 14</strong></td></tr>
              <tr><td>Übersichtsplan</td><td><strong>Karte A</strong></td></tr>
            </table>
            <div data-osm-markerurl="/markers.json"></div>
            <picture><source srcset="/image.jpg" /></picture>
          </main>
        </body></html>
        """
        canteen_html = """
        <html><body>
          <main><h1>Mensa Wilhelmstraße</h1></main>
          <a href="https://www.google.com/maps/search/?api=1&query=Wilhelmstraße%2013%2072074%20Tübingen">Map</a>
        </body></html>
        """

        directory = parse_building_directory_page(directory_html, "https://uni-tuebingen.de/adressenliste/")
        detail = parse_building_detail_page(
            building_html,
            "https://uni-tuebingen.de/auf-der-morgenstelle-26/",
            marker_payload={"markers": [{"markertitle": "14", "markerdescription": "Mensa II", "latitude": 48.535164, "longitude": 9.03604}]},
        )
        title, address, map_url = parse_canteen_page(canteen_html, "https://www.my-stuwe.de/mensa/mensa-wilhelmstrasse-tuebingen/")

        self.assertEqual(directory.area_links[0].label, "Karte A: Morgenstelle")
        self.assertEqual(directory.buildings[0].area_label, "Karte A")
        self.assertEqual(detail.title, "Mensa II Morgenstelle und Cafeteria")
        self.assertEqual(detail.address_lines, ["Auf der Morgenstelle 26", "72076 Tübingen"])
        self.assertEqual(detail.latitude, 48.535164)
        self.assertEqual(title, "Mensa Wilhelmstraße")
        self.assertEqual(address, "Wilhelmstraße 13 72074 Tübingen")
        self.assertIn("google.com/maps/search", map_url or "")

    def test_parse_kuf_occupancy_page_and_count_image(self) -> None:
        html = """
        <html><body>
          <div class="bs_head">Anzahl der Trainierenden in der KuF</div>
          <img alt="Auslastung aktuell" src="/cgi/studio.cgi?size=70">
        </body></html>
        """
        image = base64.b64decode(
            "R0lGODlhOwAoALMAAP///wAAAN/f35+fn19fXx8fH7+/vz8/P39/fwAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAAAALAAAAAA7ACgAAAT+EMhJq7046827/5cwEEURlMQggNoQvAdIvHT9EitbCXXcCSab8GTQUQ69X3A4LBoRNt9mCVMBBIZZrZADGYTSjKs2uBioBBYQzKGWMd8aC8nW8GiFjfb17ozrGXEvCBt/AYQ/ZEthZjWIgTVpHYsAlBqChxuYjxp7XJU0jBZ3L3mdZByGTpYadHwZpC8ca4MTrJCoo1ScGK5htxlQPQY5WVEcwi9doDAehkw0kpe5tqEfAslMBE5T0RbAGghUQwW8F54X4Gbj0ERiNdwU6hWYN8RXBuI2fRSx5hLzJsQKcGAZhT0v4knwlSHgwiSn8FTIZlCeNVg2KlpwFaAPJn6F3y5iyPbPAiYftAJIw+CQo8KGcgA8a9fO1ASOHziumEmTiU2AMTsg3Nmz6E8AOj3glFm051GEL1nG5Nl0y8RIiUSCcDhQYwWEID04RAoxWEYjYwd+upAtE1qtI4WkWIFFX1kdYyUgLCpqK9x3TVe+beZBwF4wUVnk3TGiRKkDCBLj/SshAgA7"
        )

        occupancy = parse_kuf_occupancy_page(html, "https://buchung.hsp.uni-tuebingen.de/angebote/aktueller_zeitraum/_Anzahl_der_Trainierenden_in_der_KuF.html")
        count = parse_kuf_training_count_image(image)

        self.assertEqual(occupancy.facility_name, "Anzahl der Trainierenden in der KuF")
        self.assertEqual(occupancy.image_url, "https://buchung.hsp.uni-tuebingen.de/cgi/studio.cgi?size=70")
        self.assertEqual(count, 84)

    def test_parse_university_events_feed_extracts_namespaced_fields(self) -> None:
        feed = """<?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0"
          xmlns:content="http://purl.org/rss/1.0/modules/content/"
          xmlns:utevent="http://uni-tuebingen.de/ns/event/">
          <channel>
            <title>Veranstaltungskalender</title>
            <link>https://uni-tuebingen.de/universitaet/campusleben/veranstaltungen/veranstaltungskalender/</link>
            <item>
              <guid isPermaLink="false">news-129066</guid>
              <pubDate>Mon, 20 Apr 2026 18:15:00 +0200</pubDate>
              <title>Wirtschaftswachstum, Produktivität und KI</title>
              <utevent:speaker>Prof. Dr. Dominik Papies</utevent:speaker>
              <utevent:location>Hörsaal 21, Kupferbau</utevent:location>
              <link>https://uni-tuebingen.de/event-one/</link>
              <description>Intro</description>
              <content:encoded><![CDATA[<p>Public lecture.</p>]]></content:encoded>
              <category>Studium Generale</category>
              <category>Top Termine Startseite</category>
            </item>
            <item>
              <guid isPermaLink="false">news-129102</guid>
              <pubDate>Tue, 21 Apr 2026 18:15:00 +0200</pubDate>
              <title>Medien und Miteinander</title>
              <utevent:location>Kupferbau</utevent:location>
              <link>https://uni-tuebingen.de/event-two/</link>
              <category>Termine</category>
            </item>
          </channel>
        </rss>
        """

        response = parse_university_events_feed(feed, query="KI", limit=5)

        self.assertEqual(response.total_hits, 1)
        self.assertEqual(response.items[0].id, "news-129066")
        self.assertEqual(response.items[0].speaker, "Prof. Dr. Dominik Papies")
        self.assertEqual(response.items[0].location, "Hörsaal 21, Kupferbau")
        self.assertEqual(response.items[0].starts_at, "2026-04-20T18:15:00+02:00")
        self.assertEqual(response.items[0].categories, ["Studium Generale", "Top Termine Startseite"])

    def test_map_talks_payload_and_filter_response(self) -> None:
        talk = map_talk(
            {
                "id": 958,
                "title": "Multimodal interaction across languages",
                "timestamp": "2026-05-05T10:15:00",
                "description": "Abstract: tba",
                "location": "Lecture Hall 23, Kupferbau",
                "speaker_name": "Dr. Paula Rubio-Fernandez",
                "speaker_bio": "",
                "disabled": False,
                "tags": [{"id": 42, "name": "Guest speaker"}],
            }
        )
        hidden = map_talk(
            {
                "id": 949,
                "title": "Hidden talk",
                "timestamp": "2026-05-12T12:30:00",
                "disabled": True,
                "tags": [{"id": 41, "name": "Group meeting"}],
            }
        )

        response = build_talks_response(
            [talk, hidden],
            scope="upcoming",
            query="rubio",
            tag_ids=[42],
            limit=10,
        )

        self.assertEqual(response.total_hits, 1)
        self.assertEqual(response.items[0].id, 958)
        self.assertEqual(response.items[0].source_url, "https://talks.tuebingen.ai/talks/talk/id=958")
        self.assertEqual([tag.name for tag in response.available_tags], ["Guest speaker"])


if __name__ == "__main__":
    unittest.main()
