package config

import "time"

const (
	DefaultTimeoutSeconds = 30
	AlmaBaseURL           = "https://alma.uni-tuebingen.de"
	AlmaStartPageURL      = "https://alma.uni-tuebingen.de/alma/pages/cs/sys/portal/hisinoneStartPage.faces"
	AlmaCurrentLectures   = "https://alma.uni-tuebingen.de/alma/pages/cm/exa/timetable/currentLectures.xhtml?_flowId=showEventsAndExaminationsOnDate-flow&navigationPosition=studiesOffered,currentLecturesGeneric&recordRequest=true"
	AlmaTimetableURL      = "https://alma.uni-tuebingen.de/alma/pages/plan/individualTimetable.xhtml?_flowId=individualTimetableSchedule-flow&navigationPosition=hisinoneMeinStudium%2CindividualTimetableSchedule&recordRequest=true"
	IliasLoginURL         = "https://ovidius.uni-tuebingen.de/login.php?cmd=force_login"
	IliasSearchURL        = "https://ovidius.uni-tuebingen.de/ilias.php?baseClass=ilSearchControllerGUI"
)

func DefaultTimeout() time.Duration {
	return DefaultTimeoutSeconds * time.Second
}
