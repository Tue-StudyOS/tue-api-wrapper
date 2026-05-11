package alma

import "testing"

func TestParseTimetableContractExtractsTermsAndExportURL(t *testing.T) {
	html := `
	<form id="plan" action="/alma/pages/plan/individualTimetable.xhtml">
	  <select name="plan:scheduleConfiguration:anzeigeoptionen:changeTerm_input">
	    <option value="TERM-1">Sommer 2026</option>
	    <option value="TERM-2" selected>Winter 2026/27</option>
	  </select>
	  <textarea name="plan:scheduleConfiguration:anzeigeoptionen:ical:cal_add">https://alma.example/export.ics?x=1</textarea>
	</form>
	`

	contract, err := parseTimetableContract(html, "https://alma.example/page")
	if err != nil {
		t.Fatalf("parseTimetableContract returned error: %v", err)
	}

	if got := contract.SelectedTermLabel; got != "Winter 2026/27" {
		t.Fatalf("unexpected selected term label: %q", got)
	}
	if got := contract.SelectedTermValue; got != "TERM-2" {
		t.Fatalf("unexpected selected term value: %q", got)
	}
	if got := contract.ExportURL; got != "https://alma.example/export.ics?x=1" {
		t.Fatalf("unexpected export URL: %q", got)
	}
	if len(contract.Terms) != 2 {
		t.Fatalf("unexpected term count: %d", len(contract.Terms))
	}
}

func TestBuildTermExportURLAddsTermGroup(t *testing.T) {
	url, err := buildTermExportURL("https://alma.example/export.ics?x=1", "TERM-9")
	if err != nil {
		t.Fatalf("buildTermExportURL returned error: %v", err)
	}
	if url != "https://alma.example/export.ics?termgroup=TERM-9&x=1" && url != "https://alma.example/export.ics?x=1&termgroup=TERM-9" {
		t.Fatalf("unexpected URL: %s", url)
	}
}

func TestParseICSEventsAndExpandOccurrencesHonorsWeeklyRules(t *testing.T) {
	raw := "BEGIN:VCALENDAR\nBEGIN:VEVENT\nSUMMARY:Computer Graphics\nDTSTART;TZID=Europe/Berlin:20260413T090000\nDTEND;TZID=Europe/Berlin:20260413T110000\nRRULE:FREQ=WEEKLY;BYDAY=MO;UNTIL=20260501T000000Z\nEXDATE;TZID=Europe/Berlin:20260420T090000\nEND:VEVENT\nEND:VCALENDAR\n"

	events, err := parseICSEvents(raw)
	if err != nil {
		t.Fatalf("parseICSEvents returned error: %v", err)
	}
	if len(events) != 1 {
		t.Fatalf("unexpected event count: %d", len(events))
	}
	if events[0].Summary != "Computer Graphics" {
		t.Fatalf("unexpected summary: %q", events[0].Summary)
	}

	occurrences, err := expandOccurrences(events, "Sommer 2026")
	if err != nil {
		t.Fatalf("expandOccurrences returned error: %v", err)
	}
	if len(occurrences) < 2 {
		t.Fatalf("unexpected occurrence count: %d", len(occurrences))
	}
	if got := occurrences[0].Start.Format("2006-01-02 15:04"); got != "2026-04-13 09:00" {
		t.Fatalf("unexpected first occurrence: %s", got)
	}
	if got := occurrences[1].Start.Format("2006-01-02 15:04"); got != "2026-04-27 09:00" {
		t.Fatalf("unexpected second occurrence: %s", got)
	}
}
