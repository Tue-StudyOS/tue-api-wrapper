package ilias

import "net/url"

type SearchForm struct {
	ActionURL    string
	Payload      url.Values
	TermField    string
	SearchButton string
}

type SearchResult struct {
	Title             string   `json:"title"`
	URL               *string  `json:"url"`
	Description       *string  `json:"description"`
	InfoURL           *string  `json:"info_url"`
	AddToFavoritesURL *string  `json:"add_to_favorites_url"`
	Breadcrumbs       []string `json:"breadcrumbs"`
	Properties        []string `json:"properties"`
	ItemType          *string  `json:"item_type"`
}

type SearchPage struct {
	PageURL         string         `json:"page_url"`
	Query           string         `json:"query"`
	PageNumber      int            `json:"page_number"`
	PreviousPageURL *string        `json:"previous_page_url"`
	NextPageURL     *string        `json:"next_page_url"`
	Results         []SearchResult `json:"results"`
}

type InfoField struct {
	Label *string `json:"label"`
	Value string  `json:"value"`
}

type InfoSection struct {
	Title  string      `json:"title"`
	Fields []InfoField `json:"fields"`
}

type InfoPage struct {
	Title    string        `json:"title"`
	PageURL  string        `json:"page_url"`
	Sections []InfoSection `json:"sections"`
}

type Link struct {
	Label string `json:"label"`
	URL   string `json:"url"`
}

type RootPage struct {
	Title         string `json:"title"`
	MainbarLinks  []Link `json:"mainbar_links"`
	TopCategories []Link `json:"top_categories"`
}

type ContentItem struct {
	Label      string   `json:"label"`
	URL        string   `json:"url"`
	Kind       *string  `json:"kind"`
	Properties []string `json:"properties"`
}

type ContentSection struct {
	Label string        `json:"label"`
	Items []ContentItem `json:"items"`
}

type ContentPage struct {
	Title    string           `json:"title"`
	PageURL  string           `json:"page_url"`
	Sections []ContentSection `json:"sections"`
}

type MembershipItem struct {
	Title       string   `json:"title"`
	URL         string   `json:"url"`
	Kind        *string  `json:"kind"`
	Description *string  `json:"description"`
	InfoURL     *string  `json:"info_url"`
	Properties  []string `json:"properties"`
}

type TaskItem struct {
	Title    string  `json:"title"`
	URL      string  `json:"url"`
	ItemType *string `json:"item_type"`
	Start    *string `json:"start"`
	End      *string `json:"end"`
}

type ForumTopic struct {
	Title    string  `json:"title"`
	URL      string  `json:"url"`
	Author   *string `json:"author"`
	Posts    *string `json:"posts"`
	LastPost *string `json:"last_post"`
	Visits   *string `json:"visits"`
}

type ExerciseAssignment struct {
	Title          string  `json:"title"`
	URL            string  `json:"url"`
	DueHint        *string `json:"due_hint"`
	DueAt          *string `json:"due_at"`
	Requirement    *string `json:"requirement"`
	LastSubmission *string `json:"last_submission"`
	SubmissionType *string `json:"submission_type"`
	Status         *string `json:"status"`
	TeamActionURL  *string `json:"team_action_url"`
}
