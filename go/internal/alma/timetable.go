package alma

import (
	"fmt"
	"net/url"
	"sort"
	"strings"

	"github.com/SebastianBoehler/tue-api-wrapper/go/internal/config"
)

func (c *Client) FetchTimetableForTerm(termLabel string) (*TimetableResult, error) {
	resp, body, err := c.http.Get(config.AlmaTimetableURL)
	if err != nil {
		return nil, err
	}
	if err := expectOK(resp); err != nil {
		return nil, err
	}
	htmlInput := string(body)
	if looksLoggedOut(htmlInput) {
		return nil, fmt.Errorf("session is not authenticated; the timetable page redirected back to login")
	}

	contract, err := parseTimetableContract(htmlInput, resp.Request.URL.String())
	if err != nil {
		return nil, err
	}

	terms := map[string]string{}
	for _, option := range contract.Terms {
		terms[option.Label] = option.Value
	}

	resolvedLabel := strings.TrimSpace(termLabel)
	termID, ok := terms[resolvedLabel]
	if !ok && resolvedLabel != "" {
		for label, value := range terms {
			if value == resolvedLabel {
				resolvedLabel = label
				termID = value
				ok = true
				break
			}
		}
	}

	if !ok && len(terms) == 0 && contract.ExportURL != "" {
		if contract.SelectedTermLabel != "" && resolvedLabel == "" {
			resolvedLabel = contract.SelectedTermLabel
		}
		termID = contract.SelectedTermValue
		ok = true
	}

	if !ok {
		available := make([]string, 0, len(terms))
		for label := range terms {
			available = append(available, label)
		}
		sort.Strings(available)
		return nil, fmt.Errorf("unknown term %q. Available terms: %s", termLabel, strings.Join(available, ", "))
	}

	if contract.ExportURL == "" {
		return nil, fmt.Errorf("could not find the timetable iCalendar export field")
	}
	exportURL := contract.ExportURL
	if termID != "" {
		exportURL, err = buildTermExportURL(contract.ExportURL, termID)
		if err != nil {
			return nil, err
		}
	}

	resp, icsBytes, err := c.http.Get(exportURL)
	if err != nil {
		return nil, err
	}
	if err := expectOK(resp); err != nil {
		return nil, err
	}
	rawICS := decodeICSBytes(icsBytes)
	if !strings.Contains(rawICS, "BEGIN:VCALENDAR") {
		return nil, fmt.Errorf("expected an iCalendar export but received a different response")
	}

	parsedEvents, err := parseICSEvents(rawICS)
	if err != nil {
		return nil, err
	}

	events := make([]CalendarEvent, 0, len(parsedEvents))
	for _, event := range parsedEvents {
		events = append(events, CalendarEvent{
			Summary:        event.Summary,
			Start:          event.Start,
			End:            event.End,
			Location:       event.Location,
			Description:    event.Description,
			UID:            event.UID,
			RecurrenceRule: event.RecurrenceRule,
			ExcludedStarts: event.ExcludedStarts,
		})
	}

	occurrences, err := expandOccurrences(parsedEvents, resolvedLabel)
	if err != nil {
		return nil, err
	}

	return &TimetableResult{
		TermLabel:      resolvedLabel,
		TermID:         termID,
		ExportURL:      exportURL,
		RawICS:         rawICS,
		Events:         events,
		Occurrences:    occurrences,
		AvailableTerms: terms,
	}, nil
}

func buildTermExportURL(exportURL string, termID string) (string, error) {
	parsed, err := url.Parse(exportURL)
	if err != nil {
		return "", err
	}
	query := parsed.Query()
	query.Set("termgroup", termID)
	parsed.RawQuery = query.Encode()
	return parsed.String(), nil
}
