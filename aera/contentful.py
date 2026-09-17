"""Contentful CMS client for fetching Aera fragrance metadata."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import aiohttp

_LOGGER = logging.getLogger(__name__)

CONTENTFUL_SPACE = "bsswjwaepi0w"
CONTENTFUL_TOKEN = "UC4IVgBwitvaugwTZQLSvO28UcUdUumEvpOy4MejPUg"
CONTENTFUL_BASE_URL = f"https://cdn.contentful.com/spaces/{CONTENTFUL_SPACE}"


@dataclass
class FragranceInfo:
    """Fragrance metadata from Contentful."""

    fragrance_id: str | None
    fragrance_qr: str | None
    fragrance_name: str | None
    firmware_name: str | None
    color: str | None
    mini_fill: float | None
    mini_output: float | None


class ContentfulClient:
    """Fetches fragrance data from the Aera Contentful CMS."""

    def __init__(self, session: aiohttp.ClientSession | None = None):
        self._session = session
        self._owns_session = session is None
        self._fragrances: list[FragranceInfo] = []
        self._loaded = False

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def load_fragrances(self) -> list[FragranceInfo]:
        """Fetch all fragrances from Contentful."""
        session = await self._get_session()
        headers = {"Authorization": f"Bearer {CONTENTFUL_TOKEN}"}
        fragrances: list[FragranceInfo] = []
        skip = 0
        limit = 100

        while True:
            url = f"{CONTENTFUL_BASE_URL}/entries?content_type=fragrance&limit={limit}&skip={skip}"
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    _LOGGER.error("Contentful API error: %s", resp.status)
                    break
                data = await resp.json()

            items = data.get("items", [])
            for item in items:
                fields = item.get("fields", {})
                fragrances.append(
                    FragranceInfo(
                        fragrance_id=fields.get("fragranceId"),
                        fragrance_qr=fields.get("fragranceQr"),
                        fragrance_name=fields.get("fragranceName"),
                        firmware_name=fields.get("firmwareName"),
                        color=fields.get("color"),
                        mini_fill=fields.get("miniFill"),
                        mini_output=fields.get("miniOutput"),
                    )
                )

            total = data.get("total", 0)
            skip += limit
            if skip >= total:
                break

        self._fragrances = fragrances
        self._loaded = True
        _LOGGER.debug("Loaded %d fragrances from Contentful", len(fragrances))
        return fragrances

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def get_fragrance_by_id(self, identifier: str) -> FragranceInfo | None:
        """Look up fragrance by fragranceId (used by Mini devices)."""
        identifier_lower = identifier.lower()
        for f in self._fragrances:
            if f.fragrance_id and f.fragrance_id.lower() == identifier_lower:
                return f
        return None

    def get_fragrance_by_name(self, name: str) -> FragranceInfo | None:
        """Look up fragrance by fragranceName, then firmwareName (used by full-size)."""
        name_lower = name.lower()
        for f in self._fragrances:
            if f.fragrance_name and f.fragrance_name.lower() == name_lower:
                return f
        for f in self._fragrances:
            if f.firmware_name and f.firmware_name.lower() == name_lower:
                return f
        return None

    def get_fragrance_by_qr(self, qr_id: str) -> FragranceInfo | None:
        """Look up fragrance by fragranceQr code."""
        qr_lower = qr_id.lower()
        for f in self._fragrances:
            if f.fragrance_qr and f.fragrance_qr.lower() == qr_lower:
                return f
        return None

    def get_mini_fragrances(self) -> list[FragranceInfo]:
        """Return all fragrances compatible with Aera Mini (those with a fragrance_id)."""
        return [f for f in self._fragrances if f.fragrance_id]

    def resolve_fragrance(self, identifier: str, is_mini: bool) -> FragranceInfo | None:
        """Resolve a fragrance identifier using the app's matching logic.

        For Mini: try fragranceId first, then fragranceName/firmwareName.
        For full-size: try fragranceName/firmwareName only.
        """
        if is_mini:
            result = self.get_fragrance_by_id(identifier)
            if result:
                return result
        return self.get_fragrance_by_name(identifier)

    async def close(self) -> None:
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()
