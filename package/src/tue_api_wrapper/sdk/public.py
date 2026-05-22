from __future__ import annotations

from dataclasses import dataclass, field

from ..alma_feature_client import fetch_current_lectures
from ..campus_client import CampusClient
from ..client import AlmaClient
from ..directory_client import UniversityDirectoryClient
from ..event_calendar_client import EventCalendarClient
from ..fitness_client import FitnessClient
from ..hsp_client import HspClient
from ..praxisportal_client import PraxisportalClient
from ..seatfinder_client import SeatfinderClient
from ..talks_client import TalksClient
from ..timms_client import TimmsClient
from .discovery import CourseDiscoveryApi


@dataclass(slots=True)
class PublicAlmaApi:
    client: AlmaClient = field(default_factory=AlmaClient)

    def search_modules(self, query: str, *, max_results: int = 20):
        return self.client.search_public_module_descriptions(query=query, max_results=max_results)

    def module_search_filters(self):
        return self.client.fetch_public_module_search_filters()

    def module_detail(self, detail_url: str):
        return self.client.fetch_public_module_detail(detail_url)

    def current_lectures(self, *, date: str | None = None, limit: int | None = 20):
        return fetch_current_lectures(self.client, date=date, limit=limit)


@dataclass(slots=True)
class PublicCampusApi:
    campus_client: CampusClient = field(default_factory=CampusClient)
    event_client: EventCalendarClient = field(default_factory=EventCalendarClient)
    fitness_client: FitnessClient = field(default_factory=FitnessClient)
    hsp_client: HspClient = field(default_factory=HspClient)
    seatfinder_client: SeatfinderClient = field(default_factory=SeatfinderClient)

    def canteens(self, *, menu_date: str | None = None):
        return self.campus_client.fetch_tuebingen_canteens(menu_date=menu_date)

    def canteen(self, canteen_id: int, *, menu_date: str | None = None):
        return self.campus_client.fetch_canteen(canteen_id, menu_date=menu_date)

    def buildings(self):
        return self.campus_client.fetch_buildings()

    def building_detail(self, path: str):
        return self.campus_client.fetch_building_detail(path)

    def events(self, *, query: str = "", limit: int = 24):
        return self.event_client.fetch_events(query=query, limit=limit)

    def kuf_occupancy(self):
        return self.fitness_client.fetch_kuf_training_occupancy()

    def gym_occupancy(self):
        return self.kuf_occupancy()

    def fitness_courses(
        self,
        *,
        query: str = "",
        area: str | None = None,
        include_unavailable: bool = False,
        limit: int = 50,
    ):
        return self.hsp_client.search_courses(
            query=query,
            area=area,
            include_unavailable=include_unavailable,
            limit=limit,
        )

    def fitness_offer(self, title: str):
        return self.hsp_client.fetch_offer(title)

    def seat_availability(self):
        return self.seatfinder_client.fetch_availability()


@dataclass(slots=True)
class PublicDirectoryApi:
    client: UniversityDirectoryClient = field(default_factory=UniversityDirectoryClient)

    def search(self, query: str):
        return self.client.search(query)


@dataclass(slots=True)
class PublicTimmsApi:
    client: TimmsClient = field(default_factory=TimmsClient)

    def suggest(self, term: str, *, limit: int = 8):
        return self.client.suggest(term, limit=limit)

    def search(self, query: str, *, offset: int = 0, limit: int = 20):
        return self.client.search(query, offset=offset, limit=limit)

    def item(self, item_id: str):
        return self.client.fetch_item(item_id)

    def streams(self, item_id: str):
        return self.client.fetch_streams(item_id)

    def tree(self, *, node_id: str | None = None, node_path: str | None = None):
        return self.client.fetch_tree(node_id=node_id, node_path=node_path)


@dataclass(slots=True)
class PublicTalksApi:
    client: TalksClient = field(default_factory=TalksClient)

    def search(self, *, query: str = "", limit: int = 16):
        return self.client.fetch_talks(query=query, limit=limit)

    def item(self, talk_id: int):
        return self.client.fetch_talk(talk_id)


@dataclass(slots=True)
class PublicPraxisportalApi:
    client: PraxisportalClient = field(default_factory=PraxisportalClient)

    def filters(self):
        return self.client.fetch_filter_options()

    def search(
        self,
        *,
        query: str = "",
        project_type_ids: tuple[int, ...] = (),
        project_subtype_ids: tuple[int, ...] = (),
        industry_ids: tuple[int, ...] = (),
        postal_codes: tuple[str, ...] = (),
        organization_ids: tuple[int, ...] = (),
        page: int = 0,
        per_page: int = 20,
        sort: str = "newest",
    ):
        return self.client.search_projects(
            query=query,
            project_type_ids=project_type_ids,
            project_subtype_ids=project_subtype_ids,
            industry_ids=industry_ids,
            postal_codes=postal_codes,
            organization_ids=organization_ids,
            page=page,
            per_page=per_page,
            sort=sort,
        )

    def project(self, project_id: int):
        return self.client.fetch_project(project_id)

    def subscription_types(self):
        return self.client.fetch_subscription_types()

    def create_subscription(self, *, query, subscription_type_id: int = 1, access_token: str | None = None):
        return self.client.create_subscription(
            query=query,
            subscription_type_id=subscription_type_id,
            access_token=access_token,
        )


class TuebingenPublicClient:
    def __init__(
        self,
        *,
        alma: PublicAlmaApi | None = None,
        campus: PublicCampusApi | None = None,
        directory: PublicDirectoryApi | None = None,
        discovery: CourseDiscoveryApi | None = None,
        praxisportal: PublicPraxisportalApi | None = None,
        talks: PublicTalksApi | None = None,
        timms: PublicTimmsApi | None = None,
    ) -> None:
        self.alma = alma or PublicAlmaApi()
        self.campus = campus or PublicCampusApi()
        self.directory = directory or PublicDirectoryApi()
        self.discovery = discovery or CourseDiscoveryApi()
        self.praxisportal = praxisportal or PublicPraxisportalApi()
        self.talks = talks or PublicTalksApi()
        self.timms = timms or PublicTimmsApi()
