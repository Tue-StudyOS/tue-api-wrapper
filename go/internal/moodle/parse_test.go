package moodle

import "testing"

func TestParseGradesPageExtractsRows(t *testing.T) {
	html := `
	<html><body>
	  <table class="generaltable">
	    <thead><tr><th>Kurs</th><th>Bewertung</th><th>Prozent</th><th>Bereich</th></tr></thead>
	    <tbody>
	      <tr>
	        <td><a href="/course/view.php?id=1559">Introduction to Neural Networks</a></td>
	        <td>1,3</td>
	        <td>92 %</td>
	        <td>0-100</td>
	      </tr>
	    </tbody>
	  </table>
	</body></html>`

	page, err := parseGradesPage(html, "https://moodle.example/grade/report/overview/index.php", 50)
	if err != nil {
		t.Fatalf("parseGradesPage returned error: %v", err)
	}
	if len(page.Items) != 1 {
		t.Fatalf("items = %d", len(page.Items))
	}
	item := page.Items[0]
	if item.CourseTitle != "Introduction to Neural Networks" {
		t.Fatalf("CourseTitle = %q", item.CourseTitle)
	}
	if item.Grade == nil || *item.Grade != "1,3" {
		t.Fatalf("Grade = %v", item.Grade)
	}
	if item.Percentage == nil || *item.Percentage != "92 %" {
		t.Fatalf("Percentage = %v", item.Percentage)
	}
}

func TestExtractShibLoginURL(t *testing.T) {
	got, err := extractShibLoginURL(
		`<a href="/auth/shibboleth/index.php">Login</a>`,
		"https://moodle.example/login/index.php",
	)
	if err != nil {
		t.Fatalf("extractShibLoginURL returned error: %v", err)
	}
	if got != "https://moodle.example/auth/shibboleth/index.php" {
		t.Fatalf("url = %q", got)
	}
}
