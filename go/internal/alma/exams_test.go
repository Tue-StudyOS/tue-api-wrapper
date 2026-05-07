package alma

import "testing"

func TestParseExamOverviewExtractsTreeRows(t *testing.T) {
	html := `
<table class="treeTableWithIcons">
  <tr><th>Titel</th></tr>
  <tr class="treeTableCellLevel3">
    <td class="invisible">1.1.1.1</td>
    <td></td><td></td><td></td>
    <td colspan="2"><img class="submitImageTable" alt="Konto"/><span id="x:unDeftxt">Studienbegleitende Leistungen</span></td>
    <td><span id="x:elementnr">9055</span></td>
    <td><span id="x:attempt">1</span></td>
    <td></td>
    <td><span id="x:grade">1,0</span></td>
    <td><span id="x:bonus">9</span></td>
    <td><span id="x:malus">0</span></td>
    <td><span id="x:workstatus">BE</span></td>
    <td><span id="x:freeTrial">-</span></td>
    <td><span id="x:remark"></span></td>
    <td><span id="x:exceptionNein">Nein</span></td>
    <td></td>
    <td><span id="x:geplantesFreigabedatum">2026-02-01</span></td>
    <td></td>
  </tr>
</table>`

	rows, err := parseExamOverview(html)
	if err != nil {
		t.Fatal(err)
	}
	if len(rows) != 1 {
		t.Fatalf("expected one row, got %d", len(rows))
	}
	row := rows[0]
	if row.Level != 3 || row.Title != "Studienbegleitende Leistungen" {
		t.Fatalf("unexpected row: %#v", row)
	}
	if row.Number == nil || *row.Number != "9055" {
		t.Fatalf("unexpected number: %#v", row.Number)
	}
	if row.Status == nil || *row.Status != "BE" {
		t.Fatalf("unexpected status: %#v", row.Status)
	}
}
