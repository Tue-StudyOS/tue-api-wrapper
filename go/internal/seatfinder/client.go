package seatfinder

import (
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

const apiURL = "https://seatfinder.bibliothek.kit.edu/tuebingen/getdata.php"

var defaultLocations = []string{
	"UBH1",
	"UBB2",
	"UBB2HLS",
	"UBA3A",
	"UBA3C",
	"UBA4A",
	"UBA4B",
	"UBA4C",
	"UBA5A",
	"UBA5B",
	"UBA5C",
	"UBA6A",
	"UBA6B",
	"UBA6C",
	"UBCEG",
	"UBCUG",
	"UBLZN",
	"UBNEG",
	"UBWZA",
	"UBWZB",
}

type Client struct {
	http *http.Client
}

func New(timeout time.Duration) *Client {
	return &Client{http: &http.Client{Timeout: timeout}}
}

func DefaultLocations() []string {
	out := make([]string, len(defaultLocations))
	copy(out, defaultLocations)
	return out
}

func (c *Client) FetchAvailability(locations []string) (*SeatAvailabilityResponse, error) {
	locationCSV := buildLocationCSV(locations)
	if locationCSV == "" {
		return nil, fmt.Errorf("at least one seatfinder location id is required")
	}

	params := seatfinderParams(locationCSV)
	target := apiURL + "?" + params.Encode()

	req, err := http.NewRequest(http.MethodGet, target, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "application/json, text/javascript;q=0.9, */*;q=0.8")

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("seatfinder request failed with HTTP %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	payload, err := parsePayload(string(body))
	if err != nil {
		return nil, err
	}

	retrievedAt := time.Now().In(germanLocation()).Format(time.RFC3339)
	return ParseAvailabilityPayload(payload, target, retrievedAt)
}

func buildLocationCSV(locations []string) string {
	clean := make([]string, 0, len(locations))
	for _, loc := range locations {
		loc = strings.TrimSpace(loc)
		if loc == "" {
			continue
		}
		clean = append(clean, loc)
	}
	return strings.Join(clean, ",")
}

func seatfinderParams(locationCSV string) url.Values {
	values := url.Values{}
	values.Set("location[0]", locationCSV)
	values.Set("values[0]", "seatestimate,manualcount")
	values.Set("after[0]", "-10800seconds")
	values.Set("before[0]", "now")
	values.Set("limit[0]", "-17")
	values.Set("location[1]", locationCSV)
	values.Set("values[1]", "location")
	values.Set("after[1]", "")
	values.Set("before[1]", "now")
	values.Set("limit[1]", "1")
	return values
}
