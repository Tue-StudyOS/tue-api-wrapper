package talks

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"
)

const (
	baseURL   = "https://talks.tuebingen.ai"
	userAgent = "tue-api-wrapper-go/0.2 (+https://talks.tuebingen.ai/)"
)

type Client struct {
	http *http.Client
}

func New(timeout time.Duration) *Client {
	return &Client{
		http: &http.Client{Timeout: timeout},
	}
}

func (c *Client) FetchTalk(talkID int) (*Talk, error) {
	target := fmt.Sprintf("%s/api/talks/%d", baseURL, talkID)
	req, err := http.NewRequest(http.MethodGet, target, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "application/json, text/plain, */*")
	req.Header.Set("User-Agent", userAgent)

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("talks request failed with HTTP %d", resp.StatusCode)
	}

	var payload map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		return nil, err
	}
	mapped, err := mapTalk(payload)
	if err != nil {
		return nil, err
	}
	return &mapped, nil
}

func (c *Client) FetchTalks(scope string) ([]Talk, error) {
	listURL, err := talksListURL(scope)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest(http.MethodGet, listURL, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "application/json, text/plain, */*")
	req.Header.Set("User-Agent", userAgent)

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("talks list request failed with HTTP %d", resp.StatusCode)
	}

	var payload map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		return nil, err
	}
	rawTalks, ok := payload["talks"].([]any)
	if !ok {
		return nil, fmt.Errorf("talks list endpoint did not return a talks array")
	}

	talks := make([]Talk, 0, len(rawTalks))
	for _, item := range rawTalks {
		entry, ok := item.(map[string]any)
		if !ok {
			continue
		}
		mapped, err := mapTalk(entry)
		if err != nil {
			return nil, err
		}
		talks = append(talks, mapped)
	}
	return talks, nil
}

func talksListURL(scope string) (string, error) {
	switch strings.TrimSpace(scope) {
	case "", "upcoming":
		return baseURL + "/api/talks?", nil
	case "previous":
		return baseURL + "/api/talks?previous", nil
	default:
		return "", fmt.Errorf("unsupported talks scope: %s", scope)
	}
}

func absoluteURL(path string) string {
	target, err := url.JoinPath(baseURL, strings.TrimLeft(path, "/"))
	if err != nil {
		return baseURL + "/" + strings.TrimLeft(path, "/")
	}
	return target
}

func safeInt(value any) (int, error) {
	switch typed := value.(type) {
	case float64:
		return int(typed), nil
	case int:
		return typed, nil
	case string:
		parsed, err := strconv.Atoi(strings.TrimSpace(typed))
		if err != nil {
			return 0, err
		}
		return parsed, nil
	default:
		return 0, fmt.Errorf("invalid integer: %v", value)
	}
}

func cleanText(value any) *string {
	if value == nil {
		return nil
	}
	text := strings.TrimSpace(fmt.Sprintf("%v", value))
	if text == "" {
		return nil
	}
	return &text
}

func mapTalkTag(payload map[string]any) (TalkTag, error) {
	id, err := safeInt(payload["id"])
	if err != nil {
		return TalkTag{}, err
	}
	name := cleanText(payload["name"])
	if name == nil {
		fallback := "Untitled tag"
		name = &fallback
	}
	var totalTalks *int
	if payload["total_talks"] != nil {
		if parsed, err := safeInt(payload["total_talks"]); err == nil {
			totalTalks = &parsed
		}
	}
	var hasSubscribed *bool
	if payload["has_subscribed"] != nil {
		value := payload["has_subscribed"]
		parsed := false
		switch typed := value.(type) {
		case bool:
			parsed = typed
			hasSubscribed = &parsed
		}
	}
	return TalkTag{
		ID:            id,
		Name:          *name,
		Description:   cleanText(payload["description"]),
		TotalTalks:    totalTalks,
		HasSubscribed: hasSubscribed,
	}, nil
}

func mapTalk(payload map[string]any) (Talk, error) {
	id, err := safeInt(payload["id"])
	if err != nil {
		return Talk{}, err
	}

	title := cleanText(payload["title"])
	if title == nil {
		fallback := "Untitled talk"
		title = &fallback
	}
	timestamp := cleanText(payload["timestamp"])
	if timestamp == nil {
		empty := ""
		timestamp = &empty
	}

	tags := []TalkTag{}
	if rawTags, ok := payload["tags"].([]any); ok {
		for _, item := range rawTags {
			entry, ok := item.(map[string]any)
			if !ok {
				continue
			}
			tag, err := mapTalkTag(entry)
			if err != nil {
				return Talk{}, err
			}
			tags = append(tags, tag)
		}
	}

	source := absoluteURL(fmt.Sprintf("talks/talk/id=%d", id))
	disabled := false
	if rawDisabled, ok := payload["disabled"].(bool); ok {
		disabled = rawDisabled
	}

	return Talk{
		ID:          id,
		Title:       *title,
		Timestamp:   *timestamp,
		Description: cleanText(payload["description"]),
		Location:    cleanText(payload["location"]),
		SpeakerName: cleanText(payload["speaker_name"]),
		SpeakerBio:  cleanText(payload["speaker_bio"]),
		Disabled:    disabled,
		SourceURL:   source,
		Tags:        tags,
	}, nil
}
