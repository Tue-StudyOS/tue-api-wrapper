package alma

import (
	"fmt"
	"sort"
	"strings"
	"time"
)

func expandOccurrences(events []parsedICSEvent, termLabel string) ([]CalendarOccurrence, error) {
	windowStart, windowEnd := calendarWindowForTerm(termLabel)
	var occurrences []CalendarOccurrence

	for _, event := range events {
		duration := time.Duration(0)
		if event.End != nil {
			duration = event.End.Sub(event.Start)
		}

		excluded := map[int64]struct{}{}
		for _, ex := range event.ExcludedStarts {
			excluded[ex.Unix()] = struct{}{}
		}

		if event.RecurrenceRule == nil {
			if event.Start.Before(windowStart) || event.Start.After(windowEnd) {
				continue
			}
			occurrences = append(occurrences, CalendarOccurrence{
				Summary:     event.Summary,
				Start:       event.Start,
				End:         addDurationPtr(event.Start, duration, event.End != nil),
				Location:    event.Location,
				Description: event.Description,
			})
			continue
		}

		spec, err := parseRRULE(*event.RecurrenceRule, event.Start)
		if err != nil {
			return nil, err
		}
		emitted := 0
		add := func(start time.Time) {
			if start.Before(windowStart) || start.After(windowEnd) {
				return
			}
			if _, ok := excluded[start.Unix()]; ok {
				return
			}
			occurrences = append(occurrences, CalendarOccurrence{
				Summary:     event.Summary,
				Start:       start,
				End:         addDurationPtr(start, duration, event.End != nil),
				Location:    event.Location,
				Description: event.Description,
			})
			emitted++
		}

		switch spec.Freq {
		case "DAILY":
			for start := event.Start; !shouldStop(spec, start, emitted); start = start.AddDate(0, 0, spec.Interval) {
				add(start)
			}
		case "WEEKLY":
			for base := event.Start; !shouldStop(spec, base, emitted); base = base.AddDate(0, 0, 7*spec.Interval) {
				if len(spec.ByDay) == 0 {
					add(base)
					continue
				}
				for _, day := range spec.ByDay {
					offset := (int(day) - int(base.Weekday()) + 7) % 7
					candidate := base.AddDate(0, 0, offset)
					candidate = time.Date(candidate.Year(), candidate.Month(), candidate.Day(), base.Hour(), base.Minute(), base.Second(), 0, base.Location())
					add(candidate)
					if spec.Count != nil && emitted >= *spec.Count {
						break
					}
				}
			}
		default:
			return nil, fmt.Errorf("unsupported RRULE FREQ=%s", spec.Freq)
		}
	}

	sort.Slice(occurrences, func(i, j int) bool {
		if !occurrences[i].Start.Equal(occurrences[j].Start) {
			return occurrences[i].Start.Before(occurrences[j].Start)
		}
		return strings.ToLower(occurrences[i].Summary) < strings.ToLower(occurrences[j].Summary)
	})
	return occurrences, nil
}

func addDurationPtr(start time.Time, duration time.Duration, enabled bool) *time.Time {
	if !enabled {
		return nil
	}
	value := start.Add(duration)
	return &value
}
