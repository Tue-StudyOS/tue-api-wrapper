package talks

type TalkTag struct {
	ID            int     `json:"id"`
	Name          string  `json:"name"`
	Description   *string `json:"description"`
	TotalTalks    *int    `json:"total_talks"`
	HasSubscribed *bool   `json:"has_subscribed"`
}

type Talk struct {
	ID          int       `json:"id"`
	Title       string    `json:"title"`
	Timestamp   string    `json:"timestamp"`
	Description *string   `json:"description"`
	Location    *string   `json:"location"`
	SpeakerName *string   `json:"speaker_name"`
	SpeakerBio  *string   `json:"speaker_bio"`
	Disabled    bool      `json:"disabled"`
	SourceURL   string    `json:"source_url"`
	Tags        []TalkTag `json:"tags"`
}

type TalksResponse struct {
	Scope         string    `json:"scope"`
	Query         string    `json:"query"`
	TagIDs        []int     `json:"tag_ids"`
	TotalHits     int       `json:"total_hits"`
	ReturnedHits  int       `json:"returned_hits"`
	SourceURL     string    `json:"source_url"`
	Items         []Talk    `json:"items"`
	AvailableTags []TalkTag `json:"available_tags"`
}
