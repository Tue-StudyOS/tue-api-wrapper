package io.github.sebastianboehler.tueapi;

import java.io.IOException;

public final class CampusApi {
    private static final String MEALPLAN = "https://www.my-stuwe.de/wp-json/mealplans/v1";
    private static final String BUILDINGS = "https://uni-tuebingen.de/universitaet/standort-und-anfahrt/lageplaene/adressenliste/";
    private static final String EVENTS = "https://uni-tuebingen.de/universitaet/campusleben/veranstaltungen/veranstaltungskalender/feed.xml";
    private static final String KUF = "https://buchung.hsp.uni-tuebingen.de/angebote/aktueller_zeitraum/_Anzahl_der_Trainierenden_in_der_KuF.html";
    private static final String SEATS = "https://seatfinder.bibliothek.kit.edu/tuebingen/getdata.php";
    private final HttpTransport http;

    CampusApi(HttpTransport http) {
        this.http = http;
    }

    public String canteens(String date) throws IOException, TueApiException {
        return http.get(MEALPLAN + "/canteens", new QueryParams().add("lang", "de")).text();
    }

    public String canteen(int canteenId, String date) throws IOException, TueApiException {
        return http.get(MEALPLAN + "/canteens/" + canteenId, new QueryParams().add("lang", "de")).text();
    }

    public String buildings() throws IOException, TueApiException {
        return http.get(BUILDINGS).text();
    }

    public String buildingDetail(String path) throws IOException, TueApiException {
        return http.get(HtmlSupport.resolve("https://uni-tuebingen.de/", path)).text();
    }

    public String events(String query, int limit) throws IOException, TueApiException {
        return http.get(EVENTS).text();
    }

    public String kufOccupancy() throws IOException, TueApiException {
        return http.get(KUF).text();
    }

    public String seatAvailability() throws IOException, TueApiException {
        return http.get(SEATS, new QueryParams()
            .add("location[0]", "UBH1,UBB2,UBB2HLS,UBA3A,UBA3C,UBA4A,UBA4B,UBA4C,UBA5A,UBA5B,UBA5C,UBA6A,UBA6B,UBA6C,UBCEG,UBCUG,UBLZN,UBNEG,UBWZA,UBWZB")
            .add("values[0]", "seatestimate,manualcount")
            .add("after[0]", "-10800seconds")
            .add("before[0]", "now")
            .add("limit[0]", "-17")
            .add("location[1]", "UBH1,UBB2,UBB2HLS,UBA3A,UBA3C,UBA4A,UBA4B,UBA4C,UBA5A,UBA5B,UBA5C,UBA6A,UBA6B,UBA6C,UBCEG,UBCUG,UBLZN,UBNEG,UBWZA,UBWZB")
            .add("values[1]", "location")
            .add("before[1]", "now")
            .add("limit[1]", "1")).text();
    }
}
