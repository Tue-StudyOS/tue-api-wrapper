from __future__ import annotations

from dataclasses import dataclass

from ..praxisportal_client import PraxisportalClient, build_praxisportal_subscription_query
from .credentials import UniversityCredentials


@dataclass(slots=True)
class AuthenticatedPraxisportalApi:
    credentials: UniversityCredentials
    _client: PraxisportalClient | None = None

    @property
    def client(self) -> PraxisportalClient:
        if self._client is None:
            client = PraxisportalClient()
            client.login(self.credentials.username, self.credentials.password)
            self._client = client
        return self._client

    def me(self):
        return self.client.fetch_current_user()

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

    def subscriptions(self):
        return self.client.fetch_my_subscriptions()

    def subscribe(
        self,
        *,
        text: tuple[str, ...] = (),
        project_type_ids: tuple[int, ...] = (),
        project_subtype_ids: tuple[int, ...] = (),
        industry_ids: tuple[int, ...] = (),
        postal_codes: tuple[str, ...] = (),
        subscription_type_id: int = 1,
    ):
        return self.client.create_subscription(
            query=build_praxisportal_subscription_query(
                text=text,
                project_type_ids=project_type_ids,
                project_subtype_ids=project_subtype_ids,
                industry_ids=industry_ids,
                postal_codes=postal_codes,
            ),
            subscription_type_id=subscription_type_id,
        )

    def update_subscription(self, subscription_id: int, *, active: bool):
        return self.client.update_subscription(subscription_id=subscription_id, active=active)

    def delete_subscription(self, subscription_id: int):
        return self.client.delete_subscription(subscription_id=subscription_id)
