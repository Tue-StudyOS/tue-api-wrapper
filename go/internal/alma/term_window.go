package alma

import (
	"regexp"
	"strconv"
	"strings"
	"time"
)

var yearPattern = regexp.MustCompile(`\\d{4}`)

func calendarWindowForTerm(termLabel string) (time.Time, time.Time) {
	loc := berlinLocation()
	normalized := strings.ToLower(termLabel)

	var years []int
	for _, match := range yearPattern.FindAllString(termLabel, -1) {
		parsed, err := strconv.Atoi(match)
		if err == nil {
			years = append(years, parsed)
		}
	}

	if strings.Contains(normalized, "sommer") && len(years) > 0 {
		year := years[0]
		return time.Date(year, time.April, 1, 0, 0, 0, 0, loc),
			time.Date(year, time.September, 30, 23, 59, 59, 0, loc)
	}

	if strings.Contains(normalized, "winter") && len(years) > 0 {
		startYear := years[0]
		endYear := startYear + 1
		if len(years) > 1 {
			endYear = years[1]
		}
		return time.Date(startYear, time.October, 1, 0, 0, 0, 0, loc),
			time.Date(endYear, time.March, 31, 23, 59, 59, 0, loc)
	}

	if len(years) == 0 {
		years = []int{time.Now().In(loc).Year()}
	}

	minYear, maxYear := years[0], years[0]
	for _, year := range years[1:] {
		if year < minYear {
			minYear = year
		}
		if year > maxYear {
			maxYear = year
		}
	}

	return time.Date(minYear, time.January, 1, 0, 0, 0, 0, loc),
		time.Date(maxYear, time.December, 31, 23, 59, 59, 0, loc)
}
