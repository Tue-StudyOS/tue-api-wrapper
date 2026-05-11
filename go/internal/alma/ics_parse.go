package alma

import (
	"regexp"
	"strings"
	"time"
)

var icsDatePattern = regexp.MustCompile(`^\\d{8}$`)

func decodeICSText(value string) string {
	replacer := strings.NewReplacer(
		"\\n", "\n",
		"\\N", "\n",
		"\\,", ",",
		"\\;", ";",
		"\\\\", "\\",
	)
	return replacer.Replace(value)
}

type icsValue struct {
	Value  string
	Params map[string]string
}

type parsedICSEvent struct {
	Summary        string
	Start          time.Time
	End            *time.Time
	Location       *string
	Description    *string
	UID            *string
	RecurrenceRule *string
	ExcludedStarts []time.Time
}

func parseICSEvents(raw string) ([]parsedICSEvent, error) {
	lines := unfoldICSLines(raw)
	var current map[string][]icsValue
	var events []parsedICSEvent

	for _, line := range lines {
		switch line {
		case "BEGIN:VEVENT":
			current = map[string][]icsValue{}
			continue
		case "END:VEVENT":
			if current == nil {
				continue
			}
			event, ok, err := buildICSEvent(current)
			if err != nil {
				return nil, err
			}
			if ok {
				events = append(events, event)
			}
			current = nil
			continue
		}

		if current == nil {
			continue
		}
		keyPart, valuePart, ok := strings.Cut(line, ":")
		if !ok {
			continue
		}
		key, params := parseICSParams(keyPart)
		current[key] = append(current[key], icsValue{Value: valuePart, Params: params})
	}

	return events, nil
}

func unfoldICSLines(raw string) []string {
	input := strings.ReplaceAll(raw, "\r\n", "\n")
	input = strings.ReplaceAll(input, "\r", "\n")
	lines := strings.Split(input, "\n")

	var unfolded []string
	for _, line := range lines {
		if line == "" {
			continue
		}
		if strings.HasPrefix(line, " ") || strings.HasPrefix(line, "\t") {
			if len(unfolded) > 0 {
				unfolded[len(unfolded)-1] += line[1:]
			}
			continue
		}
		unfolded = append(unfolded, line)
	}
	return unfolded
}

func parseICSParams(rawKey string) (string, map[string]string) {
	parts := strings.Split(rawKey, ";")
	key := strings.ToUpper(parts[0])
	params := map[string]string{}
	for _, part := range parts[1:] {
		name, value, ok := strings.Cut(part, "=")
		if !ok {
			continue
		}
		name = strings.ToUpper(strings.TrimSpace(name))
		if name == "" {
			continue
		}
		params[name] = strings.TrimSpace(value)
	}
	return key, params
}

func buildICSEvent(values map[string][]icsValue) (parsedICSEvent, bool, error) {
	first := func(name string) *icsValue {
		items := values[name]
		if len(items) == 0 {
			return nil
		}
		return &items[0]
	}

	dtstart := first("DTSTART")
	if dtstart == nil {
		return parsedICSEvent{}, false, nil
	}
	start, err := parseICSDatetime(dtstart.Value, dtstart.Params)
	if err != nil {
		return parsedICSEvent{}, false, err
	}

	var end *time.Time
	if dtend := first("DTEND"); dtend != nil {
		parsedEnd, err := parseICSDatetime(dtend.Value, dtend.Params)
		if err != nil {
			return parsedICSEvent{}, false, err
		}
		end = &parsedEnd
	}

	summary := ""
	if raw := first("SUMMARY"); raw != nil {
		summary = decodeICSText(raw.Value)
	}

	location := optionalDecoded(first("LOCATION"))
	description := optionalDecoded(first("DESCRIPTION"))
	uid := optionalDecoded(first("UID"))

	var rrule *string
	if raw := first("RRULE"); raw != nil {
		text := strings.TrimSpace(raw.Value)
		if text != "" {
			rrule = &text
		}
	}

	excluded, err := parseICSExcludedDates(values["EXDATE"])
	if err != nil {
		return parsedICSEvent{}, false, err
	}

	return parsedICSEvent{
		Summary:        summary,
		Start:          start,
		End:            end,
		Location:       location,
		Description:    description,
		UID:            uid,
		RecurrenceRule: rrule,
		ExcludedStarts: excluded,
	}, true, nil
}

func optionalDecoded(value *icsValue) *string {
	if value == nil {
		return nil
	}
	text := strings.TrimSpace(decodeICSText(value.Value))
	if text == "" {
		return nil
	}
	return &text
}

func parseICSExcludedDates(values []icsValue) ([]time.Time, error) {
	var excluded []time.Time
	for _, item := range values {
		for _, raw := range strings.Split(item.Value, ",") {
			raw = strings.TrimSpace(raw)
			if raw == "" {
				continue
			}
			parsed, err := parseICSDatetime(raw, item.Params)
			if err != nil {
				return nil, err
			}
			excluded = append(excluded, parsed)
		}
	}
	return excluded, nil
}
