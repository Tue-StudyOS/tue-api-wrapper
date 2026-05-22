package alma

import (
	"fmt"
	"strconv"
	"strings"
	"time"
)

type rruleSpec struct {
	Freq     string
	Interval int
	Until    *time.Time
	Count    *int
	ByDay    []time.Weekday
}

func parseRRULE(rule string, dtstart time.Time) (*rruleSpec, error) {
	spec := &rruleSpec{Interval: 1}
	for _, part := range strings.Split(rule, ";") {
		key, value, ok := strings.Cut(part, "=")
		if !ok {
			continue
		}
		key = strings.ToUpper(strings.TrimSpace(key))
		value = strings.TrimSpace(value)
		switch key {
		case "FREQ":
			spec.Freq = strings.ToUpper(value)
		case "INTERVAL":
			parsed, err := strconv.Atoi(value)
			if err != nil || parsed <= 0 {
				return nil, fmt.Errorf("unsupported RRULE INTERVAL=%q", value)
			}
			spec.Interval = parsed
		case "UNTIL":
			parsed, err := parseICSDatetime(value, map[string]string{})
			if err != nil {
				return nil, err
			}
			if dtstart.Location() != nil && !strings.HasSuffix(value, "Z") && len(value) == len("20060102T150405") {
				parsed = time.Date(parsed.Year(), parsed.Month(), parsed.Day(), parsed.Hour(), parsed.Minute(), parsed.Second(), 0, dtstart.Location())
			}
			spec.Until = &parsed
		case "COUNT":
			parsed, err := strconv.Atoi(value)
			if err != nil || parsed <= 0 {
				return nil, fmt.Errorf("unsupported RRULE COUNT=%q", value)
			}
			spec.Count = &parsed
		case "BYDAY":
			spec.ByDay = parseByDay(value)
		}
	}
	if spec.Freq == "" {
		return nil, fmt.Errorf("RRULE missing FREQ")
	}
	return spec, nil
}

func parseByDay(value string) []time.Weekday {
	var days []time.Weekday
	for _, item := range strings.Split(value, ",") {
		item = strings.TrimSpace(item)
		switch item {
		case "MO":
			days = append(days, time.Monday)
		case "TU":
			days = append(days, time.Tuesday)
		case "WE":
			days = append(days, time.Wednesday)
		case "TH":
			days = append(days, time.Thursday)
		case "FR":
			days = append(days, time.Friday)
		case "SA":
			days = append(days, time.Saturday)
		case "SU":
			days = append(days, time.Sunday)
		}
	}
	return days
}

func shouldStop(spec *rruleSpec, start time.Time, emitted int) bool {
	if spec.Count != nil && emitted >= *spec.Count {
		return true
	}
	if spec.Until != nil && start.After(*spec.Until) {
		return true
	}
	return false
}
