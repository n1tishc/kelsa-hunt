"""Owner-triggered private role snapshots, isolated from the public scanner."""

from __future__ import annotations

import hashlib
import html.parser
import re
import time
import urllib.parse
import urllib.request
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Protocol


class PublicRecordReference(Protocol):
    uid: str
    title: str
    source_url: str | None


class DescriptionFetcher(Protocol):
    """Fetch a description only after an owner has selected one Record."""

    def fetch(self, reference: PublicRecordReference) -> str: ...


class ProfileContextSelector(Protocol):
    """Choose and explain a bounded role-specific subset of profile revisions."""

    def select(
        self,
        reference: PublicRecordReference,
        snapshot: "SelectedRoleSnapshot",
        profile_items: tuple["ProfileItemRevision", ...],
        maximum: int,
    ) -> tuple["ProfileContextSelection", ...]: ...


@dataclass(frozen=True)
class ProfileItemRevision:
    """An owner-controlled profile revision used for one bounded role context."""

    id: str
    category: str
    text: str


@dataclass(frozen=True)
class ProfileContextSelection:
    item: ProfileItemRevision
    rationale: str


@dataclass(frozen=True)
class SelectedRoleSnapshot:
    """Immutable, provenance-bearing evidence capture for one selected Record."""

    id: str
    record_uid: str
    source_url: str
    captured_at: int
    description: str
    description_digest: str


@dataclass(frozen=True)
class RelevantProfileContext:
    """The explicit, bounded profile revisions shown to the owner for a snapshot."""

    id: str
    snapshot_id: str
    profile_item_ids: tuple[str, ...]
    profile_item_digests: tuple[str, ...]
    selection_rationales: tuple[str, ...]
    items: tuple[ProfileItemRevision, ...]


@dataclass(frozen=True)
class RoleWorkspacePacket:
    snapshot: SelectedRoleSnapshot
    profile_context: RelevantProfileContext
    shortlisted: bool


class RoleWorkspace(Protocol):
    def select(self, reference: PublicRecordReference, action: str) -> RoleWorkspacePacket: ...

    def packet_for(self, snapshot_id: str) -> RoleWorkspacePacket | None: ...


class DescriptionUnavailable(Exception):
    """The owner-selected source could not provide a safe description capture."""


class HttpDescriptionFetcher:
    """Bounded direct retrieval used only by an explicit owner action."""

    def __init__(self, timeout_seconds: float = 10, max_bytes: int = 256_000):
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes

    def fetch(self, reference: PublicRecordReference) -> str:
        source_url = reference.source_url
        if not _safe_https_url(source_url):
            raise DescriptionUnavailable
        try:
            request = urllib.request.Request(
                source_url,
                headers={"User-Agent": "kelsa-role-snapshot/1.0"},
            )
            opener = urllib.request.build_opener(_NoRedirectHandler())
            with opener.open(request, timeout=self.timeout_seconds) as response:
                content = response.read(self.max_bytes + 1)
        except OSError as error:
            raise DescriptionUnavailable from error
        if len(content) > self.max_bytes:
            raise DescriptionUnavailable
        description = _html_to_text(content.decode("utf-8", errors="replace"))
        if not description:
            raise DescriptionUnavailable
        return description[:12_000]


class InMemoryRoleWorkspace:
    """Test/preview implementation; production storage remains admission-gated."""

    def __init__(
        self,
        description_fetcher: DescriptionFetcher,
        profile_items: Iterable[ProfileItemRevision] = (),
        profile_context_selector: ProfileContextSelector | None = None,
        now: Callable[[], float] = time.time,
        max_profile_items: int = 3,
    ):
        self.description_fetcher = description_fetcher
        self.profile_items = tuple(profile_items)
        self.profile_context_selector = profile_context_selector or KeywordProfileContextSelector()
        self.now = now
        self.max_profile_items = max_profile_items
        self._snapshots_by_record: dict[str, SelectedRoleSnapshot] = {}
        self._packets_by_snapshot: dict[str, RoleWorkspacePacket] = {}

    def select(self, reference: PublicRecordReference, action: str) -> RoleWorkspacePacket:
        if action not in {"open", "shortlist"}:
            raise ValueError("unknown owner selection action")
        snapshot = self._snapshots_by_record.get(reference.uid)
        if snapshot is None:
            if not _safe_https_url(reference.source_url):
                raise DescriptionUnavailable
            description = self.description_fetcher.fetch(reference)
            snapshot = SelectedRoleSnapshot(
                id=f"snapshot_{uuid.uuid4().hex}",
                record_uid=reference.uid,
                source_url=reference.source_url,
                captured_at=int(self.now()),
                description=description,
                description_digest=hashlib.sha256(description.encode()).hexdigest(),
            )
            self._snapshots_by_record[reference.uid] = snapshot
        existing = self._packets_by_snapshot.get(snapshot.id)
        selections = self.profile_context_selector.select(
            reference,
            snapshot,
            self.profile_items,
            self.max_profile_items,
        )
        packet = RoleWorkspacePacket(
            snapshot=snapshot,
            profile_context=(
                existing.profile_context
                if existing is not None
                else RelevantProfileContext(
                    id=f"context_{uuid.uuid4().hex}",
                    snapshot_id=snapshot.id,
                    profile_item_ids=tuple(selection.item.id for selection in selections),
                    profile_item_digests=tuple(
                        hashlib.sha256(selection.item.text.encode()).hexdigest()
                        for selection in selections
                    ),
                    selection_rationales=tuple(selection.rationale for selection in selections),
                    items=tuple(selection.item for selection in selections),
                )
            ),
            shortlisted=(action == "shortlist") or (existing.shortlisted if existing else False),
        )
        self._packets_by_snapshot[snapshot.id] = packet
        return packet

    def packet_for(self, snapshot_id: str) -> RoleWorkspacePacket | None:
        return self._packets_by_snapshot.get(snapshot_id)

    def snapshot_for(self, record_uid: str) -> SelectedRoleSnapshot | None:
        return self._snapshots_by_record.get(record_uid)

    def is_shortlisted(self, record_uid: str) -> bool:
        snapshot = self.snapshot_for(record_uid)
        return bool(snapshot and self._packets_by_snapshot[snapshot.id].shortlisted)


class _TextExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data):
        if not self._ignored_depth:
            self.parts.append(data)


def _html_to_text(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(value)
    return " ".join(" ".join(parser.parts).split())


class KeywordProfileContextSelector:
    """Small deterministic selector; it never asks a model for profile facts."""

    def select(self, reference, snapshot, profile_items, maximum):
        role_terms = _terms(f"{reference.title} {snapshot.description}")
        ranked = []
        for index, item in enumerate(profile_items):
            shared = sorted(role_terms & _terms(item.text))
            if shared:
                ranked.append((-len(shared), index, item, shared))
        ranked.sort()
        return tuple(
            ProfileContextSelection(
                item=item,
                rationale=f"Shared role terms: {', '.join(shared)}.",
            )
            for _, _, item, shared in ranked[:maximum]
        )


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise DescriptionUnavailable


def _terms(value: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z0-9]+", value) if len(token) >= 4}


def _safe_https_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urllib.parse.urlsplit(value)
    return parsed.scheme == "https" and bool(parsed.netloc)
