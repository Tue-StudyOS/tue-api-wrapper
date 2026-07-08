from zoneinfo import ZoneInfo

DEFAULT_BASE_URL = "https://alma.uni-tuebingen.de"
START_PAGE_PATH = "/alma/pages/cs/sys/portal/hisinoneStartPage.faces"
TIMETABLE_PATH = (
    "/alma/pages/plan/individualTimetable.xhtml"
    "?_flowId=individualTimetableSchedule-flow"
    "&navigationPosition=hisinoneMeinStudium%2CindividualTimetableSchedule"
    "&recordRequest=true"
)
STUDYSERVICE_PATH = (
    "/alma/pages/cm/exa/enrollment/info/start.xhtml"
    "?_flowId=studyservice-flow"
    "&navigationPosition=hisinoneMeinStudium%2ChisinoneStudyservice"
    "&recordRequest=true"
)
DEFAULT_TIMEOUT_SECONDS = 30
GERMAN_TIMEZONE = ZoneInfo("Europe/Berlin")


class AlmaError(RuntimeError):
    pass


class AlmaLoginError(AlmaError):
    pass


class AlmaServiceUnavailableError(AlmaError):
    pass


class AlmaParseError(AlmaError):
    pass


class MailError(AlmaError):
    pass


class MailLoginError(MailError):
    pass
