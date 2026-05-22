from __future__ import annotations

from functools import lru_cache

import requests

from .praxisportal_dates import iso_from_timestamp
from .praxisportal_models import CareerSubscription, CareerSubscriptionQuery, CareerSubscriptionType
from .praxisportal_subscriptions import map_praxisportal_subscription, map_praxisportal_subscription_type

PRAXISPORTAL_BASE_URL = "https://www.praxisportal.uni-tuebingen.de"


class PraxisportalSubscriptionMixin:
    timeout: int
    session: requests.Session

    @lru_cache(maxsize=1)
    def fetch_subscription_types(self) -> list[CareerSubscriptionType]:
        response = self.session.get(f"{PRAXISPORTAL_BASE_URL}/1/subscription/types", timeout=self.timeout)
        response.raise_for_status()
        return [map_praxisportal_subscription_type(item) for item in response.json()]

    def create_subscription(
        self,
        *,
        query: CareerSubscriptionQuery,
        subscription_type_id: int,
        access_token: str | None = None,
    ) -> CareerSubscription:
        if access_token:
            self.sync_user(access_token)
        response = self.session.post(
            f"{PRAXISPORTAL_BASE_URL}/1/subscription/create",
            json={"query": query.create_payload(), "subscription_type_id": subscription_type_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json().get("subscription", {})
        return CareerSubscription(
            id=int(payload["id"]),
            user_id=int(payload.get("user_id", 0)),
            query_id=int(payload.get("query_id", 0)),
            subscription_type_id=int(payload.get("subscription_type_id", subscription_type_id)),
            active=True,
            query=query,
            subscription_type=self._subscription_type_by_id(subscription_type_id),
            created_at=iso_from_timestamp(payload.get("created_at"), milliseconds=True),
            updated_at=iso_from_timestamp(payload.get("updated_at"), milliseconds=True),
        )

    def fetch_user_subscriptions(self, *, user_id: int, access_token: str) -> list[CareerSubscription]:
        response = self.session.get(
            f"{PRAXISPORTAL_BASE_URL}/1/subscription/user/{user_id}",
            params={"access_token": access_token},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return [map_praxisportal_subscription(item) for item in response.json().get("subscriptions", [])]

    def update_subscription(self, *, subscription_id: int, active: bool, access_token: str | None = None) -> bool:
        data = {"active": "1" if active else "0"}
        if access_token:
            data["access_token"] = access_token
        response = self.session.post(
            f"{PRAXISPORTAL_BASE_URL}/1/subscription/{subscription_id}/update",
            data=data,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return bool(response.json().get("success"))

    def delete_subscription(self, *, subscription_id: int, access_token: str | None = None) -> bool:
        data = {"access_token": access_token} if access_token else {}
        response = self.session.post(
            f"{PRAXISPORTAL_BASE_URL}/1/subscription/{subscription_id}/delete",
            data=data,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return bool(response.json().get("success"))

    def sync_user(self, access_token: str) -> None:
        response = self.session.post(
            f"{PRAXISPORTAL_BASE_URL}/1/user",
            data={"language": "de", "access_token": access_token},
            timeout=self.timeout,
        )
        response.raise_for_status()

    def _subscription_type_by_id(self, subscription_type_id: int) -> CareerSubscriptionType:
        return next(item for item in self.fetch_subscription_types() if item.id == subscription_type_id)
