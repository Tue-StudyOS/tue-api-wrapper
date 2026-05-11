package alma

import (
	"net/url"
	"time"
)

type CurrentLecturesForm struct {
	ActionURL       string
	Payload         url.Values
	DateFieldName   string
	SearchButton    string
	FilterFieldName string
	FilterValues    []string
}

type CurrentLecture struct {
	Title               string  `json:"title"`
	DetailURL           *string `json:"detail_url"`
	Start               *string `json:"start"`
	End                 *string `json:"end"`
	Number              *string `json:"number"`
	ParallelGroup       *string `json:"parallel_group"`
	EventType           *string `json:"event_type"`
	ResponsibleLecturer *string `json:"responsible_lecturer"`
	Lecturer            *string `json:"lecturer"`
	Building            *string `json:"building"`
	Room                *string `json:"room"`
	Semester            *string `json:"semester"`
	Remark              *string `json:"remark"`
}

type CurrentLecturesPage struct {
	PageURL      string           `json:"page_url"`
	SelectedDate *string          `json:"selected_date"`
	Results      []CurrentLecture `json:"results"`
}

type ExamNode struct {
	Level       int     `json:"level"`
	Kind        *string `json:"kind"`
	Title       string  `json:"title"`
	Number      *string `json:"number"`
	Attempt     *string `json:"attempt"`
	Grade       *string `json:"grade"`
	CP          *string `json:"cp"`
	Malus       *string `json:"malus"`
	Status      *string `json:"status"`
	FreeTrial   *string `json:"free_trial"`
	Remark      *string `json:"remark"`
	Exception   *string `json:"exception"`
	ReleaseDate *string `json:"release_date"`
}

type TimetableResult struct {
	TermLabel      string               `json:"term_label"`
	TermID         string               `json:"term_id"`
	ExportURL      string               `json:"export_url"`
	RawICS         string               `json:"raw_ics"`
	Events         []CalendarEvent      `json:"events"`
	Occurrences    []CalendarOccurrence `json:"occurrences"`
	AvailableTerms map[string]string    `json:"available_terms"`
}

type CalendarEvent struct {
	Summary        string      `json:"summary"`
	Start          time.Time   `json:"start"`
	End            *time.Time  `json:"end"`
	Location       *string     `json:"location"`
	Description    *string     `json:"description"`
	UID            *string     `json:"uid"`
	RecurrenceRule *string     `json:"recurrence_rule"`
	ExcludedStarts []time.Time `json:"excluded_starts"`
}

type CalendarOccurrence struct {
	Summary     string     `json:"summary"`
	Start       time.Time  `json:"start"`
	End         *time.Time `json:"end"`
	Location    *string    `json:"location"`
	Description *string    `json:"description"`
}
