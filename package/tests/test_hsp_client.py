from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tue_api_wrapper.hsp_html import hsp_offer_path, parse_hsp_course_search_data, parse_hsp_offer_page


class HspContractTests(unittest.TestCase):
    def test_parse_hsp_course_search_data_maps_bookable_courses(self) -> None:
        javascript = """
        const data={"orte":[["","",0,0],["KuF",48.528,9.076,0]],"tage":[["",0,0,0,0,0,0,0],["Mo",1,0,0,0,0,0,0]],"bereiche":["","KuF_freies Training"],"kurse":[
        [1,"7001","Kraft- und Fitnesshalle Probetraining","(einmaliger Termin)",[1,0,0,0,0],["18:00-19:00","","","",""],[1,0,0,0,0],"13.04.-<wbr /><wbr>11.10.","Dennis Murr","<span><span>entgeltfrei</span></span><div><div>entgeltfrei / free of charge</div></div>",1,1778536800,1,null,null,null,""],
        [1,"7002","Ausgebucht","",[1,0,0,0,0],["20:00-21:00","","","",""],[1,0,0,0,0],"13.04.-<wbr /><wbr>11.10.","","<span>10&nbsp;&euro;</span>",0,0,1,null,null,null,""]
        ],"conf":{"zr":36},"merkmale":{}};
        """

        result = parse_hsp_course_search_data(javascript, "https://buchung.hsp.uni-tuebingen.de/angebote/aktueller_zeitraum/kurssuche.js", query="probetraining")

        self.assertEqual(result.total_hits, 1)
        course = result.items[0]
        self.assertEqual(course.id, "7001")
        self.assertEqual(course.subtitle, "(einmaliger Termin)")
        self.assertEqual(course.area, "KuF_freies Training")
        self.assertEqual(course.schedules[0].day, "Mo")
        self.assertEqual(course.schedules[0].location.name, "KuF")
        self.assertEqual(course.price_summary, "entgeltfrei")
        self.assertTrue(course.is_bookable)
        self.assertTrue(course.detail_url.endswith("/_Kraft-_und_Fitnesshalle_Probetraining.html#K7001"))

    def test_parse_hsp_offer_page_extracts_booking_contract(self) -> None:
        html = """
        <html><body>
        <form action="https://buchung.hsp.uni-tuebingen.de/cgi/anmeldung.fcgi" method="post">
          <input type="hidden" name="BS_Code" value="server-issued-code">
          <div class="bs_head">Kraft- und Fitnesshalle Zehnerkarte Kletterkarte</div>
          <div class="bs_verantw">verantwortlich: Dennis Murr</div>
          <div class="bs_angblock" id="T70032">
            <table><tr>
              <td class="bs_sknr"><span>70032</span></td>
              <td class="bs_sdet"><span>Kletterkarte</span><div><div class="bs_tr">70032</div><div class="bs_tr">Kraft- und Fitnesshalle Zehnerkarte Kletterkarte</div></div></td>
              <td class="bs_sort"><a href="/cgi/webpage.cgi?spid=abc">KuF</a></td>
              <td class="bs_szr"><span><a href="/cgi/webpage.cgi?kursinfo=def">13.04.-11.10.</a></span></td>
              <td class="bs_skl"><span>Dennis Murr</span></td>
              <td class="bs_spreis"><span>20/ 30&nbsp;&euro;</span><div><div class="bs_tr"><div class="bs_tt1">20&nbsp;&euro;</div><div class="bs_tt2">für Studierende</div></div></div></td>
              <td class="bs_sbuch"><input class="bs_btn_buchen" name="BS_Kursid_58039" type="submit" value="buchen"></td>
            </tr></table>
          </div>
        </form>
        </body></html>
        """

        page = parse_hsp_offer_page(html, "https://buchung.hsp.uni-tuebingen.de/angebote/aktueller_zeitraum/_Ticket.html")

        self.assertEqual(page.booking_code, "server-issued-code")
        self.assertEqual(page.responsible, "Dennis Murr")
        option = page.items[0]
        self.assertEqual(option.course_id, "70032")
        self.assertEqual(option.booking_submit_name, "BS_Kursid_58039")
        self.assertEqual(option.prices[0].audience, "für Studierende")
        self.assertTrue(option.location_url.endswith("/cgi/webpage.cgi?spid=abc"))

    def test_hsp_offer_path_matches_booking_system_slug(self) -> None:
        self.assertEqual(hsp_offer_path("Kraft- und Fitnesshalle Probetraining"), "_Kraft-_und_Fitnesshalle_Probetraining.html")


if __name__ == "__main__":
    unittest.main()
