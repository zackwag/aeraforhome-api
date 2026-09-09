"""Shared fixtures for Aera API tests."""

from __future__ import annotations

from typing import Any

import pytest
import aiohttp
from aioresponses import aioresponses

from aera.const import DEVICE_SERVICE_URL, USER_SERVICE_URL
from aera.api import AeraApi
from aera.device import AeraDevice
from aera.contentful import FragranceInfo


FAKE_EMAIL = "test@example.com"
FAKE_PASSWORD = "password123"

LOGIN_RESPONSE = {
    "access_token": "fake-access-token",
    "refresh_token": "fake-refresh-token",
}

DEVICE_DATA: dict[str, Any] = {
    "dsn": "AC000W123456789",
    "key": 12345,
    "product_name": "Aera 3.0",
    "device_name": "Living Room",
    "oem_model": "aera3",
    "model": "AY001MUS1",
    "sw_version": "2.5.0",
    "mac": "00:11:22:33:44:55",
    "lan_ip": "192.168.1.100",
    "connected_at": "2024-01-01T00:00:00Z",
    "connection_status": "Online",
}

MINI_DEVICE_DATA: dict[str, Any] = {
    "dsn": "AC000W999888777",
    "key": 99999,
    "product_name": "Aera Mini",
    "device_name": "Bedroom",
    "oem_model": "aeraMini",
    "model": "AY001MINI",
    "sw_version": "1.0.0",
    "mac": "AA:BB:CC:DD:EE:FF",
    "lan_ip": "192.168.1.101",
    "connected_at": "2024-06-01T00:00:00Z",
    "connection_status": "Online",
}

SAMPLE_PROPERTIES: dict[str, Any] = {
    "power_state": 1,
    "intensity_state": 5,
    "cartridge_usage": 30,
    "cartridge_present": 1,
    "fragrance_name": "Ocean Mist",
    "error_condition": 0,
    "session_state": 0,
    "session_time_left": 0,
    "set_fragrance_identifier": "Ocean Mist",
    "device_fw_version": "2.5.0",
}


@pytest.fixture
def mock_aiohttp():
    with aioresponses() as m:
        yield m


@pytest.fixture
def device() -> AeraDevice:
    return AeraDevice(DEVICE_DATA)


@pytest.fixture
def device_with_props() -> AeraDevice:
    return AeraDevice(DEVICE_DATA, properties=SAMPLE_PROPERTIES)


@pytest.fixture
def mini_device() -> AeraDevice:
    return AeraDevice(MINI_DEVICE_DATA)


@pytest.fixture
def sample_fragrance() -> FragranceInfo:
    return FragranceInfo(
        fragrance_id="OM001",
        fragrance_qr="QR-OM001",
        fragrance_name="Ocean Mist",
        firmware_name="ocean_mist",
        color="#3A7BD5",
        mini_fill=8.0,
        mini_output=0.05,
    )


@pytest.fixture
async def api(mock_aiohttp) -> AeraApi:
    session = aiohttp.ClientSession()
    client = AeraApi(FAKE_EMAIL, FAKE_PASSWORD, session=session)
    yield client
    await client.close()
    await session.close()


@pytest.fixture
async def authenticated_api(api, mock_aiohttp) -> AeraApi:
    mock_aiohttp.post(
        f"{USER_SERVICE_URL}/users/sign_in.json",
        payload=LOGIN_RESPONSE,
    )
    await api.login()
    return api
