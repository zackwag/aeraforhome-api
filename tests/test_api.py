"""Tests for AeraApi."""

from __future__ import annotations

import json
from typing import Any

import pytest

from aera.api import AeraApi, AeraAuthError, AeraApiError
from aera.const import DEVICE_SERVICE_URL, USER_SERVICE_URL
from tests.conftest import (
    DEVICE_DATA,
    MINI_DEVICE_DATA,
    LOGIN_RESPONSE,
    SAMPLE_PROPERTIES,
)


class TestAuth:

    async def test_login_success(self, api, mock_aiohttp):
        mock_aiohttp.post(
            f"{USER_SERVICE_URL}/users/sign_in.json",
            payload=LOGIN_RESPONSE,
        )
        result = await api.login()
        assert result is True
        assert api.is_authenticated is True

    async def test_login_invalid_credentials(self, api, mock_aiohttp):
        mock_aiohttp.post(
            f"{USER_SERVICE_URL}/users/sign_in.json",
            status=401,
        )
        with pytest.raises(AeraAuthError, match="Invalid email or password"):
            await api.login()

    async def test_login_server_error(self, api, mock_aiohttp):
        mock_aiohttp.post(
            f"{USER_SERVICE_URL}/users/sign_in.json",
            status=500,
            body="Internal Server Error",
        )
        with pytest.raises(AeraAuthError, match="500"):
            await api.login()

    async def test_refresh_auth(self, authenticated_api, mock_aiohttp):
        new_tokens = {"access_token": "new-token", "refresh_token": "new-refresh"}
        mock_aiohttp.post(
            f"{USER_SERVICE_URL}/users/refresh_token.json",
            payload=new_tokens,
        )
        result = await authenticated_api.refresh_auth()
        assert result is True

    async def test_refresh_auth_no_token(self, api):
        with pytest.raises(AeraAuthError, match="No refresh token"):
            await api.refresh_auth()

    async def test_refresh_auth_failure(self, authenticated_api, mock_aiohttp):
        mock_aiohttp.post(
            f"{USER_SERVICE_URL}/users/refresh_token.json",
            status=401,
        )
        with pytest.raises(AeraAuthError, match="refresh failed"):
            await authenticated_api.refresh_auth()
        assert authenticated_api.is_authenticated is False

    async def test_auth_header_before_login(self, api):
        with pytest.raises(AeraAuthError, match="Not authenticated"):
            api._auth_header()

    async def test_sign_out(self, authenticated_api, mock_aiohttp):
        mock_aiohttp.post(f"{USER_SERVICE_URL}/users/sign_out.json", payload={})
        result = await authenticated_api.sign_out()
        assert result is True
        assert authenticated_api.is_authenticated is False

    async def test_sign_out_when_not_authenticated(self, api):
        result = await api.sign_out()
        assert result is True


class TestRequest:

    async def test_auto_refresh_on_401(self, authenticated_api, mock_aiohttp):
        mock_aiohttp.get(
            f"{DEVICE_SERVICE_URL}/apiv1/devices.json",
            status=401,
        )
        mock_aiohttp.post(
            f"{USER_SERVICE_URL}/users/refresh_token.json",
            payload={"access_token": "new", "refresh_token": "new-r"},
        )
        mock_aiohttp.get(
            f"{DEVICE_SERVICE_URL}/apiv1/devices.json",
            payload=[{"device": DEVICE_DATA}],
        )
        devices = await authenticated_api.get_devices()
        assert len(devices) == 1

    async def test_api_error_on_non_200(self, authenticated_api, mock_aiohttp):
        mock_aiohttp.get(
            f"{DEVICE_SERVICE_URL}/apiv1/devices.json",
            status=500,
            body="Server Error",
        )
        with pytest.raises(AeraApiError, match="500"):
            await authenticated_api.get_devices()


class TestDevices:

    async def test_get_devices(self, authenticated_api, mock_aiohttp):
        mock_aiohttp.get(
            f"{DEVICE_SERVICE_URL}/apiv1/devices.json",
            payload=[{"device": DEVICE_DATA}],
        )
        mock_aiohttp.get(
            f"{USER_SERVICE_URL}/api/v1/users/data/device_data_table.json",
            payload={"datum": {"value": "[]"}},
        )
        devices = await authenticated_api.get_devices()
        assert len(devices) == 1
        assert devices[0].dsn == "AC000W123456789"

    async def test_get_devices_with_metadata(self, authenticated_api, mock_aiohttp):
        metadata = [{"dsn": "AC000W123456789", "room_name": "Kitchen"}]
        mock_aiohttp.get(
            f"{DEVICE_SERVICE_URL}/apiv1/devices.json",
            payload=[{"device": DEVICE_DATA}],
        )
        mock_aiohttp.get(
            f"{USER_SERVICE_URL}/api/v1/users/data/device_data_table.json",
            payload={"datum": {"value": json.dumps(metadata)}},
        )
        devices = await authenticated_api.get_devices()
        assert devices[0].room_name == "Kitchen"

    async def test_get_devices_caches(self, authenticated_api, mock_aiohttp):
        mock_aiohttp.get(
            f"{DEVICE_SERVICE_URL}/apiv1/devices.json",
            payload=[{"device": DEVICE_DATA}],
        )
        mock_aiohttp.get(
            f"{USER_SERVICE_URL}/api/v1/users/data/device_data_table.json",
            payload={"datum": {"value": "[]"}},
        )
        devices1 = await authenticated_api.get_devices()

        mock_aiohttp.get(
            f"{DEVICE_SERVICE_URL}/apiv1/devices.json",
            payload=[{"device": DEVICE_DATA}],
        )
        mock_aiohttp.get(
            f"{USER_SERVICE_URL}/api/v1/users/data/device_data_table.json",
            payload={"datum": {"value": "[]"}},
        )
        devices2 = await authenticated_api.get_devices()
        assert devices1[0] is devices2[0]

    async def test_get_device_metadata_bad_json(self, authenticated_api, mock_aiohttp):
        mock_aiohttp.get(
            f"{USER_SERVICE_URL}/api/v1/users/data/device_data_table.json",
            payload={"datum": {"value": "not-json"}},
        )
        result = await authenticated_api.get_device_metadata()
        assert result == {}


class TestProperties:

    async def test_get_device_properties(self, authenticated_api, mock_aiohttp):
        mock_aiohttp.get(
            f"{DEVICE_SERVICE_URL}/apiv1/devices.json",
            payload=[{"device": DEVICE_DATA}],
        )
        mock_aiohttp.get(
            f"{USER_SERVICE_URL}/api/v1/users/data/device_data_table.json",
            payload={"datum": {"value": "[]"}},
        )
        devices = await authenticated_api.get_devices()

        mock_aiohttp.get(
            f"{DEVICE_SERVICE_URL}/apiv1/dsns/AC000W123456789/properties.json",
            payload=[
                {"property": {"name": "power_state", "value": 1}},
                {"property": {"name": "intensity_state", "value": 7}},
            ],
        )
        props = await authenticated_api.get_device_properties(devices[0])
        assert props["power_state"] == 1
        assert props["intensity_state"] == 7
        assert devices[0].is_power_on is True

    async def test_set_property(self, authenticated_api, mock_aiohttp):
        mock_aiohttp.post(
            f"{DEVICE_SERVICE_URL}/apiv1/dsns/AC000W123456789/properties/set_power_state/datapoints.json",
            payload={"datapoint": {"value": 1}},
            status=201,
        )
        result = await authenticated_api.set_property("AC000W123456789", "set_power_state", 1)
        assert result is True

    async def test_set_power_on(self, authenticated_api, mock_aiohttp):
        mock_aiohttp.post(
            f"{DEVICE_SERVICE_URL}/apiv1/dsns/AC000W123456789/properties/set_power_state/datapoints.json",
            payload={},
            status=201,
        )
        result = await authenticated_api.set_power("AC000W123456789", True)
        assert result is True

    async def test_set_intensity_clamped(self, authenticated_api, mock_aiohttp):
        mock_aiohttp.get(
            f"{DEVICE_SERVICE_URL}/apiv1/devices.json",
            payload=[{"device": DEVICE_DATA}],
        )
        mock_aiohttp.get(
            f"{USER_SERVICE_URL}/api/v1/users/data/device_data_table.json",
            payload={"datum": {"value": "[]"}},
        )
        await authenticated_api.get_devices()

        mock_aiohttp.post(
            f"{DEVICE_SERVICE_URL}/apiv1/dsns/AC000W123456789/properties/set_intensity_manual/datapoints.json",
            payload={},
            status=201,
        )
        result = await authenticated_api.set_intensity("AC000W123456789", 99)
        assert result is True


class TestSessions:

    async def test_start_session(self, authenticated_api, mock_aiohttp):
        mock_aiohttp.post(
            f"{DEVICE_SERVICE_URL}/apiv1/dsns/AC000W123456789/properties/set_session_length/datapoints.json",
            payload={},
            status=201,
        )
        result = await authenticated_api.start_session("AC000W123456789", 30)
        assert result is True

    async def test_stop_session(self, authenticated_api, mock_aiohttp):
        mock_aiohttp.post(
            f"{DEVICE_SERVICE_URL}/apiv1/dsns/AC000W123456789/properties/set_session_length/datapoints.json",
            payload={},
            status=201,
        )
        result = await authenticated_api.stop_session("AC000W123456789")
        assert result is True


class TestSchedules:

    async def test_get_schedules(self, authenticated_api, mock_aiohttp):
        mock_aiohttp.get(
            f"{DEVICE_SERVICE_URL}/apiv1/devices.json",
            payload=[{"device": DEVICE_DATA}],
        )
        mock_aiohttp.get(
            f"{USER_SERVICE_URL}/api/v1/users/data/device_data_table.json",
            payload={"datum": {"value": "[]"}},
        )
        devices = await authenticated_api.get_devices()

        mock_aiohttp.get(
            f"{DEVICE_SERVICE_URL}/apiv1/devices/12345/schedules.json",
            payload=[{"schedule": {"key": 1, "name": "Morning"}}],
        )
        schedules = await authenticated_api.get_schedules(devices[0])
        assert len(schedules) == 1
        assert schedules[0]["name"] == "Morning"

    async def test_get_device_key_unknown_dsn(self, authenticated_api):
        with pytest.raises(AeraApiError, match="Unknown device"):
            authenticated_api._get_device_key("NONEXISTENT")


class TestSessionManagement:

    async def test_close_cleans_up(self, mock_aiohttp):
        api = AeraApi("a@b.com", "pw")
        mock_aiohttp.post(
            f"{USER_SERVICE_URL}/users/sign_in.json",
            payload=LOGIN_RESPONSE,
        )
        await api.login()
        await api.close()
        assert api._session is None or api._session.closed
