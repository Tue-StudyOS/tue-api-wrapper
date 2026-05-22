package alma

import (
	"strings"
	"time"
	"unicode/utf8"
)

func parseICSDatetime(raw string, params map[string]string) (time.Time, error) {
	loc := berlinLocation()
	if tzid := params["TZID"]; tzid != "" {
		if loaded, err := time.LoadLocation(tzid); err == nil {
			loc = loaded
		}
	}

	raw = strings.TrimSpace(raw)
	if params["VALUE"] == "DATE" || icsDatePattern.MatchString(raw) {
		t, err := time.ParseInLocation("20060102", raw, loc)
		if err != nil {
			return time.Time{}, err
		}
		return time.Date(t.Year(), t.Month(), t.Day(), 0, 0, 0, 0, loc), nil
	}

	if strings.HasSuffix(raw, "Z") {
		parsed, err := time.Parse("20060102T150405Z", raw)
		if err != nil {
			return time.Time{}, err
		}
		return parsed.In(loc), nil
	}

	return time.ParseInLocation("20060102T150405", raw, loc)
}

func berlinLocation() *time.Location {
	loc, err := time.LoadLocation("Europe/Berlin")
	if err != nil {
		return time.Local
	}
	return loc
}

func decodeICSBytes(body []byte) string {
	if utf8.Valid(body) {
		return string(body)
	}
	runes := make([]rune, 0, len(body))
	for _, b := range body {
		runes = append(runes, rune(b))
	}
	return string(runes)
}
