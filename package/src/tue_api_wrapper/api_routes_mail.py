from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from .api_errors import translate_alma_error
from .config import AlmaError
from .portal_service import PortalService, serialize

router = APIRouter()
portal_service = PortalService()


class MoveMessageRequest(BaseModel):
    mailbox: str = "INBOX"
    destination: str


def _mail_client():
    return portal_service._mail_client()


def _translate_error(error: AlmaError):
    return translate_alma_error(error)


@router.get("/api/mail/mailboxes")
def mail_mailboxes() -> list[object]:
    try:
        client = _mail_client()
        try:
            return serialize(client.list_mailboxes())
        finally:
            client.close()
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/mail/inbox")
def mail_inbox(
    mailbox: str = Query("INBOX"),
    limit: int = Query(12, ge=1, le=50),
    unread_only: bool = False,
    query: str = "",
    sender: str = "",
) -> dict[str, object]:
    try:
        client = _mail_client()
        try:
            return serialize(
                client.fetch_mailbox_summary(
                    mailbox=mailbox,
                    limit=limit,
                    unread_only=unread_only,
                    query=query,
                    sender=sender,
                )
            )
        finally:
            client.close()
    except AlmaError as error:
        raise _translate_error(error) from error


@router.get("/api/mail/messages/{uid}")
def mail_message(uid: str, mailbox: str = Query("INBOX")) -> dict[str, object]:
    try:
        client = _mail_client()
        try:
            return serialize(client.fetch_message_detail(uid, mailbox=mailbox))
        finally:
            client.close()
    except AlmaError as error:
        raise _translate_error(error) from error


@router.post("/api/mail/messages/{uid}/move")
def mail_move_message(uid: str, request: MoveMessageRequest) -> dict[str, object]:
    try:
        client = _mail_client()
        try:
            result = serialize(client.move_message(uid, mailbox=request.mailbox, destination=request.destination))
        finally:
            client.close()
        portal_service.invalidate_portal_cache()
        return result
    except AlmaError as error:
        raise _translate_error(error) from error
