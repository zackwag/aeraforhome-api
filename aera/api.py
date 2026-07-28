"""Aera for Home API client using the Ayla IoT platform."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from aera.const import (
    AERA_APP_ID,
    AERA_APP_SECRET,
    ALL_READABLE_PROPERTIES,
    DEVICE_METADATA_KEY,
    DEVICE_SERVICE_URL,
    PROP_EJECT_PRESSED,
    PROP_SET_INTENSITY_MANUAL,
    PROP_SET_POWER_STATE,
    PROP_SET_SESSION_LENGTH,
    USER_SERVICE_URL,
)
from aera.contentful import ContentfulClient
from aera.device import AeraDevice

_LOGGER = logging.getLogger(__name__)


class AeraAuthError(Exception):
    """Raised when authentication fails."""


class AeraApiError(Exception):
    """Raised when an API call fails."""


class AeraApi:
    """Async client for the Aera for Home cloud API (Ayla Networks)."""

    def __init__(
        self,
        email: str,
        password: str,
        session: aiohttp.ClientSession | None = None,
        app_id: str = AERA_APP_ID,
        app_secret: str = AERA_APP_SECRET,
    ):
        self._email = email
        self._password = password
        self._app_id = app_id
        self._app_secret = app_secret
        self._session = session
        self._owns_session = session is None
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._devices: dict[str, AeraDevice] = {}
        self._contentful: ContentfulClient | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    def _auth_header(self) -> dict[str, str]:
        if not self._access_token:
            raise AeraAuthError("Not authenticated. Call login() first.")
        return {"Authorization": f"auth_token {self._access_token}"}

    async def login(self) -> bool:
        """Authenticate with the Ayla user service."""
        session = await self._get_session()
        payload = {
            "user": {
                "email": self._email,
                "password": self._password,
                "application": {
                    "app_id": self._app_id,
                    "app_secret": self._app_secret,
                },
            }
        }
        async with session.post(
            f"{USER_SERVICE_URL}/users/sign_in.json",
            json=payload,
        ) as resp:
            if resp.status == 401:
                raise AeraAuthError("Invalid email or password.")
            if resp.status != 200:
                text = await resp.text()
                raise AeraAuthError(f"Login failed ({resp.status}): {text}")
            data = await resp.json()
            self._access_token = data.get("access_token")
            self._refresh_token = data.get("refresh_token")
            _LOGGER.debug("Login successful")
            return True

    async def refresh_auth(self) -> bool:
        """Refresh the access token."""
        if not self._refresh_token:
            raise AeraAuthError("No refresh token available. Call login() first.")
        session = await self._get_session()
        payload = {"user": {"refresh_token": self._refresh_token}}
        async with session.post(
            f"{USER_SERVICE_URL}/users/refresh_token.json",
            json=payload,
        ) as resp:
            if resp.status != 200:
                self._access_token = None
                self._refresh_token = None
                raise AeraAuthError("Token refresh failed. Re-authentication needed.")
            data = await resp.json()
            self._access_token = data.get("access_token")
            self._refresh_token = data.get("refresh_token")
            _LOGGER.debug("Token refresh successful")
            return True

    async def _request(
        self,
        method: str,
        url: str,
        json: dict | None = None,
        retry_on_401: bool = True,
    ) -> Any:
        """Make an authenticated API request with auto-refresh on 401."""
        session = await self._get_session()
        headers = self._auth_header()
        async with session.request(method, url, headers=headers, json=json) as resp:
            if resp.status == 401 and retry_on_401:
                _LOGGER.debug("Got 401, attempting token refresh")
                await self.refresh_auth()
                return await self._request(method, url, json=json, retry_on_401=False)
            if resp.status not in (200, 201, 204):
                text = await resp.text()
                raise AeraApiError(f"API error ({resp.status}): {text}")
            if resp.status == 204 or resp.content_length == 0:
                return None
            return await resp.json()

    async def get_devices(self) -> list[AeraDevice]:
        """Fetch all devices associated with the account."""
        data = await self._request("GET", f"{DEVICE_SERVICE_URL}/apiv1/devices.json")
        devices = []
        for item in data:
            device_data = item.get("device", item)
            dsn = device_data.get("dsn", "")
            if dsn in self._devices:
                self._devices[dsn]._data = device_data
            else:
                self._devices[dsn] = AeraDevice(device_data)
            devices.append(self._devices[dsn])
        try:
            await self.get_device_metadata()
        except Exception as ex:
            _LOGGER.debug("Failed to fetch device metadata: %s", ex)
        return devices

    async def get_device_metadata(self) -> dict[str, dict[str, Any]]:
        """Fetch user-assigned device metadata (room names, positions).

        Returns a dict of DSN -> metadata dict. Also applies room names
        to any already-fetched devices.
        """
        import json as json_lib

        data = await self._request(
            "GET",
            f"{USER_SERVICE_URL}/api/v1/users/data/{DEVICE_METADATA_KEY}.json",
        )
        datum = data.get("datum", data)
        value_str = datum.get("value", "")
        metadata: dict[str, dict[str, Any]] = {}
        try:
            entries = json_lib.loads(value_str) if value_str else []
        except (json_lib.JSONDecodeError, TypeError):
            entries = []
        for entry in entries:
            dsn = entry.get("dsn", "")
            if dsn:
                metadata[dsn] = entry
                if dsn in self._devices:
                    self._devices[dsn].room_name = entry.get("room_name", "")
        return metadata

    async def get_device_properties(self, device: AeraDevice | str) -> dict[str, Any]:
        """Fetch all properties for a device. Returns a dict of name -> value."""
        dsn = device.dsn if isinstance(device, AeraDevice) else device
        data = await self._request(
            "GET", f"{DEVICE_SERVICE_URL}/apiv1/dsns/{dsn}/properties.json"
        )
        properties: dict[str, Any] = {}
        for item in data:
            prop = item.get("property", item)
            name = prop.get("name")
            value = prop.get("value")
            if name:
                properties[name] = value
        if dsn in self._devices:
            dev = self._devices[dsn]
            dev.update_properties(properties)
            await self._resolve_fragrance(dev)
        return properties

    async def _ensure_contentful(self) -> ContentfulClient:
        """Lazily load the Contentful fragrance data."""
        if self._contentful is None:
            session = await self._get_session()
            self._contentful = ContentfulClient(session)
        if not self._contentful.is_loaded:
            await self._contentful.load_fragrances()
        return self._contentful

    async def _resolve_fragrance(self, device: AeraDevice) -> None:
        """Resolve fragrance metadata from Contentful for a device."""
        identifier = device.fragrance_identifier
        if not identifier:
            return
        contentful = await self._ensure_contentful()
        info = contentful.resolve_fragrance(identifier, device.device_type.is_mini)
        device.fragrance_info = info

    async def set_property(
        self, device: AeraDevice | str, property_name: str, value: Any
    ) -> bool:
        """Set a property value on a device (creates a datapoint)."""
        dsn = device.dsn if isinstance(device, AeraDevice) else device
        payload = {"datapoint": {"value": value}}
        await self._request(
            "POST",
            f"{DEVICE_SERVICE_URL}/apiv1/dsns/{dsn}/properties/{property_name}/datapoints.json",
            json=payload,
        )
        if dsn in self._devices:
            self._devices[dsn].update_properties({property_name: value})
        return True

    async def set_power(self, device: AeraDevice | str, on: bool) -> bool:
        """Turn device on or off."""
        return await self.set_property(device, PROP_SET_POWER_STATE, 1 if on else 0)

    async def set_intensity(self, device: AeraDevice | str, level: int) -> bool:
        """Set fragrance intensity level (1-10 for full-size, 1-5 for Mini)."""
        dsn = device.dsn if isinstance(device, AeraDevice) else device
        dev = self._devices.get(dsn)
        if dev:
            max_level = dev.max_intensity
            level = max(1, min(level, max_level))
        return await self.set_property(device, PROP_SET_INTENSITY_MANUAL, level)

    async def start_session(
        self, device: AeraDevice | str, duration_minutes: int
    ) -> bool:
        """Start a timed fragrance session."""
        return await self.set_property(device, PROP_SET_SESSION_LENGTH, duration_minutes)

    async def stop_session(self, device: AeraDevice | str) -> bool:
        """Stop a running fragrance session (set session length to 0)."""
        return await self.set_property(device, PROP_SET_SESSION_LENGTH, 0)

    async def eject_cartridge(self, device: AeraDevice | str) -> bool:
        """Eject the fragrance cartridge (full-size devices only)."""
        return await self.set_property(device, PROP_EJECT_PRESSED, 1)

    async def get_mini_fragrances(self) -> list[dict[str, str | None]]:
        """Get all Mini-compatible fragrances with name, code, and QR URL."""
        contentful = await self._ensure_contentful()
        return [
            {
                "name": f.fragrance_name,
                "code": f.fragrance_id,
                "qr_url": f.fragrance_qr,
            }
            for f in contentful.get_mini_fragrances()
        ]

    async def get_schedules(self, device: AeraDevice | str) -> list[dict[str, Any]]:
        """Fetch all schedules for a device."""
        device_key = self._get_device_key(device)
        data = await self._request(
            "GET", f"{DEVICE_SERVICE_URL}/apiv1/devices/{device_key}/schedules.json"
        )
        schedules = []
        for item in data:
            schedule = item.get("schedule", item)
            schedules.append(schedule)
        return schedules

    async def update_schedule(
        self, schedule_key: int, schedule_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a schedule."""
        payload = {"schedule": schedule_data}
        data = await self._request(
            "PUT",
            f"{DEVICE_SERVICE_URL}/apiv1/schedules/{schedule_key}.json",
            json=payload,
        )
        return data.get("schedule", data)

    async def get_schedule_actions(self, schedule_key: int) -> list[dict[str, Any]]:
        """Fetch all actions for a schedule."""
        data = await self._request(
            "GET",
            f"{DEVICE_SERVICE_URL}/apiv1/schedules/{schedule_key}/schedule_actions.json",
        )
        actions = []
        for item in data:
            action = item.get("schedule_action", item)
            actions.append(action)
        return actions

    async def create_schedule_action(
        self, schedule_key: int, action_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a new action on a schedule."""
        payload = {"schedule_action": action_data}
        data = await self._request(
            "POST",
            f"{DEVICE_SERVICE_URL}/apiv1/schedules/{schedule_key}/schedule_actions.json",
            json=payload,
        )
        return data.get("schedule_action", data)

    async def update_schedule_action(
        self, action_key: int, action_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing schedule action."""
        payload = {"schedule_action": action_data}
        data = await self._request(
            "PUT",
            f"{DEVICE_SERVICE_URL}/apiv1/schedule_actions/{action_key}.json",
            json=payload,
        )
        return data.get("schedule_action", data)

    async def delete_schedule_action(self, action_key: int) -> bool:
        """Delete a schedule action."""
        await self._request(
            "DELETE",
            f"{DEVICE_SERVICE_URL}/apiv1/schedule_actions/{action_key}.json",
        )
        return True

    def _get_device_key(self, device: AeraDevice | str) -> int:
        """Get the numeric device key for API calls that require it."""
        if isinstance(device, AeraDevice):
            return device.device_key
        dev = self._devices.get(device)
        if dev:
            return dev.device_key
        raise AeraApiError(f"Unknown device: {device}")

    async def sign_out(self) -> bool:
        """Sign out from the Ayla service."""
        if not self._access_token:
            return True
        session = await self._get_session()
        headers = self._auth_header()
        payload = {"user": {"access_token": self._access_token}}
        try:
            async with session.post(
                f"{USER_SERVICE_URL}/users/sign_out.json",
                headers=headers,
                json=payload,
            ) as resp:
                pass
        except Exception:
            pass
        self._access_token = None
        self._refresh_token = None
        return True

    async def close(self) -> None:
        """Close the session."""
        if self._contentful:
            await self._contentful.close()
            self._contentful = None
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    @property
    def is_authenticated(self) -> bool:
        return self._access_token is not None

    @property
    def devices(self) -> dict[str, AeraDevice]:
        return self._devices
