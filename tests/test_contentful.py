"""Tests for ContentfulClient."""

from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses

from aera.contentful import (
    CONTENTFUL_BASE_URL,
    ContentfulClient,
    FragranceInfo,
)


def _contentful_url(skip: int = 0, limit: int = 100) -> str:
    return f"{CONTENTFUL_BASE_URL}/entries?content_type=fragrance&limit={limit}&skip={skip}"


def _make_entry(
    name: str = "Ocean Mist",
    fid: str | None = "OM001",
    qr: str | None = "QR-OM001",
    firmware: str | None = "ocean_mist",
    color: str | None = "#3A7BD5",
    mini_fill: float | None = 8.0,
    mini_output: float | None = 0.05,
) -> dict:
    fields = {"fragranceName": name}
    if fid is not None:
        fields["fragranceId"] = fid
    if qr is not None:
        fields["fragranceQr"] = qr
    if firmware is not None:
        fields["firmwareName"] = firmware
    if color is not None:
        fields["color"] = color
    if mini_fill is not None:
        fields["miniFill"] = mini_fill
    if mini_output is not None:
        fields["miniOutput"] = mini_output
    return {"fields": fields}


ENTRIES_RESPONSE = {
    "items": [
        _make_entry("Ocean Mist", "OM001", "QR-OM001", "ocean_mist", "#3A7BD5", 8.0, 0.05),
        _make_entry(
            "Lavender Fields", "LF002", "QR-LF002", "lavender_fields", "#9B59B6", 7.0, 0.04
        ),
        _make_entry("Classic Vanilla", None, None, "classic_vanilla", "#F5E6CC", None, None),
    ],
    "total": 3,
}


class TestContentfulClientLoad:
    async def test_load_fragrances(self):
        async with aiohttp.ClientSession() as session:
            client = ContentfulClient(session)
            with aioresponses() as m:
                m.get(_contentful_url(), payload=ENTRIES_RESPONSE)
                result = await client.load_fragrances()

            assert len(result) == 3
            assert client.is_loaded is True
            assert result[0].fragrance_name == "Ocean Mist"
            assert result[0].fragrance_id == "OM001"
            assert result[1].fragrance_name == "Lavender Fields"
            assert result[2].mini_fill is None

    async def test_load_fragrances_pagination(self):
        page1 = {
            "items": [_make_entry("Frag1", "F1")],
            "total": 101,
        }
        page2 = {
            "items": [_make_entry("Frag2", "F2")],
            "total": 101,
        }
        async with aiohttp.ClientSession() as session:
            client = ContentfulClient(session)
            with aioresponses() as m:
                m.get(_contentful_url(skip=0), payload=page1)
                m.get(_contentful_url(skip=100), payload=page2)
                result = await client.load_fragrances()

            assert len(result) == 2
            assert result[0].fragrance_name == "Frag1"
            assert result[1].fragrance_name == "Frag2"

    async def test_load_fragrances_api_error(self):
        async with aiohttp.ClientSession() as session:
            client = ContentfulClient(session)
            with aioresponses() as m:
                m.get(_contentful_url(), status=500)
                result = await client.load_fragrances()

            assert result == []
            assert client.is_loaded is True

    async def test_is_loaded_initially_false(self):
        client = ContentfulClient()
        assert client.is_loaded is False
        await client.close()


class TestContentfulClientLookup:
    @pytest.fixture
    def loaded_client(self) -> ContentfulClient:
        client = ContentfulClient()
        client._fragrances = [
            FragranceInfo("OM001", "QR-OM001", "Ocean Mist", "ocean_mist", "#3A7BD5", 8.0, 0.05),
            FragranceInfo(
                "LF002", "QR-LF002", "Lavender Fields", "lavender_fields", "#9B59B6", 7.0, 0.04
            ),
            FragranceInfo(None, None, "Classic Vanilla", "classic_vanilla", "#F5E6CC", None, None),
        ]
        client._loaded = True
        return client

    def test_get_fragrance_by_id(self, loaded_client):
        result = loaded_client.get_fragrance_by_id("OM001")
        assert result is not None
        assert result.fragrance_name == "Ocean Mist"

    def test_get_fragrance_by_id_case_insensitive(self, loaded_client):
        result = loaded_client.get_fragrance_by_id("om001")
        assert result is not None
        assert result.fragrance_name == "Ocean Mist"

    def test_get_fragrance_by_id_not_found(self, loaded_client):
        assert loaded_client.get_fragrance_by_id("NOPE") is None

    def test_get_fragrance_by_name(self, loaded_client):
        result = loaded_client.get_fragrance_by_name("Ocean Mist")
        assert result is not None
        assert result.fragrance_id == "OM001"

    def test_get_fragrance_by_name_case_insensitive(self, loaded_client):
        result = loaded_client.get_fragrance_by_name("ocean mist")
        assert result is not None

    def test_get_fragrance_by_firmware_name(self, loaded_client):
        result = loaded_client.get_fragrance_by_name("classic_vanilla")
        assert result is not None
        assert result.fragrance_name == "Classic Vanilla"

    def test_get_fragrance_by_name_not_found(self, loaded_client):
        assert loaded_client.get_fragrance_by_name("Nonexistent") is None

    def test_get_fragrance_by_qr(self, loaded_client):
        result = loaded_client.get_fragrance_by_qr("QR-OM001")
        assert result is not None
        assert result.fragrance_name == "Ocean Mist"

    def test_get_fragrance_by_qr_case_insensitive(self, loaded_client):
        result = loaded_client.get_fragrance_by_qr("qr-om001")
        assert result is not None

    def test_get_fragrance_by_qr_not_found(self, loaded_client):
        assert loaded_client.get_fragrance_by_qr("QR-NOPE") is None

    def test_get_mini_fragrances(self, loaded_client):
        minis = loaded_client.get_mini_fragrances()
        assert len(minis) == 2
        assert all(f.fragrance_id is not None for f in minis)

    def test_resolve_fragrance_mini_by_id(self, loaded_client):
        result = loaded_client.resolve_fragrance("OM001", is_mini=True)
        assert result is not None
        assert result.fragrance_name == "Ocean Mist"

    def test_resolve_fragrance_mini_falls_back_to_name(self, loaded_client):
        result = loaded_client.resolve_fragrance("Classic Vanilla", is_mini=True)
        assert result is not None
        assert result.fragrance_name == "Classic Vanilla"

    def test_resolve_fragrance_full_size_by_name(self, loaded_client):
        result = loaded_client.resolve_fragrance("Lavender Fields", is_mini=False)
        assert result is not None
        assert result.fragrance_id == "LF002"

    def test_resolve_fragrance_full_size_ignores_id(self, loaded_client):
        result = loaded_client.resolve_fragrance("OM001", is_mini=False)
        assert result is None

    def test_resolve_fragrance_not_found(self, loaded_client):
        assert loaded_client.resolve_fragrance("Nothing", is_mini=False) is None


class TestContentfulClientSession:
    async def test_creates_own_session_when_none(self):
        client = ContentfulClient(session=None)
        session = await client._get_session()
        assert session is not None
        assert not session.closed
        await client.close()

    async def test_close_does_not_close_external_session(self):
        async with aiohttp.ClientSession() as session:
            client = ContentfulClient(session=session)
            await client.close()
            assert not session.closed
