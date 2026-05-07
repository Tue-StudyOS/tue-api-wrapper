package alma

import "net/url"

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
