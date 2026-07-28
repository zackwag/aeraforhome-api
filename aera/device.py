"""Aera device model."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aera.contentful import FragranceInfo


class DeviceType(Enum):
    """Aera device model types."""

    AERA1 = "aera1"
    AERA2 = "aera2"
    AERA3 = "aera3"
    AERA3_1 = "aera31"
    AERA_MINI = "aeraMini"
    UNKNOWN = "unknown"

    @classmethod
    def from_oem_model(cls, oem_model: str | None) -> DeviceType:
        if not oem_model:
            return cls.UNKNOWN
        for member in cls:
            if member.value == oem_model:
                return member
        return cls.UNKNOWN

    @property
    def is_full_size(self) -> bool:
        return self in (
            DeviceType.AERA1,
            DeviceType.AERA2,
            DeviceType.AERA3,
            DeviceType.AERA3_1,
        )

    @property
    def is_mini(self) -> bool:
        return self == DeviceType.AERA_MINI

    @property
    def max_intensity(self) -> int:
        return 10 if self.is_full_size else 5


class AeraDevice:
    """Represents a single Aera fragrance diffuser."""

    def __init__(self, device_data: dict[str, Any], properties: dict[str, Any] | None = None):
        self._data = device_data
        self._properties: dict[str, Any] = properties or {}
        self._fragrance_info: FragranceInfo | None = None
        self._room_name: str | None = None

    @property
    def dsn(self) -> str:
        return self._data.get("dsn", "")

    @property
    def device_key(self) -> int:
        return self._data.get("key", 0)

    @property
    def product_name(self) -> str:
        return self._data.get("product_name", "")

    @property
    def device_name(self) -> str:
        if self._room_name:
            return self._room_name
        return self._data.get("device_name", self.product_name)

    @property
    def room_name(self) -> str | None:
        return self._room_name

    @room_name.setter
    def room_name(self, value: str | None) -> None:
        self._room_name = value or None

    @property
    def oem_model(self) -> str:
        return self._data.get("oem_model", "")

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.from_oem_model(self.oem_model)

    @property
    def model(self) -> str:
        return self._data.get("model", "")

    @property
    def sw_version(self) -> str | None:
        return self._data.get("sw_version")

    @property
    def mac(self) -> str | None:
        return self._data.get("mac")

    @property
    def lan_ip(self) -> str | None:
        return self._data.get("lan_ip")

    @property
    def connected_at(self) -> str | None:
        return self._data.get("connected_at")

    @property
    def is_online(self) -> bool:
        status = self._data.get("connection_status")
        return status == "Online"

    @property
    def is_power_on(self) -> bool | None:
        val = self._properties.get("power_state")
        if val is None:
            return None
        return int(val) == 1

    @property
    def intensity(self) -> int | None:
        val = self._properties.get("intensity_state")
        if val is None:
            return None
        return int(val)

    @property
    def max_intensity(self) -> int:
        return self.device_type.max_intensity

    @property
    def cartridge_usage(self) -> int | None:
        val = self._properties.get("cartridge_usage")
        if val is None:
            return None
        return int(val)

    @property
    def fragrance_remaining(self) -> int | None:
        if self.device_type.is_mini:
            return self._mini_fragrance_remaining()
        usage = self.cartridge_usage
        if usage is None:
            return None
        return max(0, 100 - usage)

    def _mini_fragrance_remaining(self) -> int | None:
        pump_life = self._properties.get("pump_life_time")
        pump_qr = self._properties.get("pump_life_time_qr_scanned")
        if pump_life is None or pump_qr is None:
            return None
        if self._fragrance_info is None:
            return None
        mini_fill = self._fragrance_info.mini_fill
        mini_output = self._fragrance_info.mini_output
        if not mini_fill or not mini_output:
            return None
        usage = round(
            ((int(pump_life) - int(pump_qr)) * mini_output / (mini_fill * 3600)) * 100
        )
        return max(0, min(100, 100 - usage))

    @property
    def is_cartridge_present(self) -> bool | None:
        val = self._properties.get("cartridge_present")
        if val is None:
            return None
        return int(val) == 1

    @property
    def fragrance_name(self) -> str | None:
        if self._fragrance_info and self._fragrance_info.fragrance_name:
            return self._fragrance_info.fragrance_name
        return self._properties.get("fragrance_name") or None

    @property
    def fragrance_color(self) -> str | None:
        if self._fragrance_info:
            return self._fragrance_info.color
        return None

    @property
    def fragrance_identifier(self) -> str | None:
        """Raw fragrance identifier from device (short code for Mini, full name for full-size)."""
        return (
            self._properties.get("set_fragrance_identifier")
            or self._properties.get("fragrance_name")
            or None
        )

    @property
    def fragrance_info(self) -> FragranceInfo | None:
        return self._fragrance_info

    @fragrance_info.setter
    def fragrance_info(self, value: FragranceInfo | None) -> None:
        self._fragrance_info = value

    @property
    def error_condition(self) -> int | None:
        val = self._properties.get("error_condition")
        if val is None:
            return None
        return int(val)

    @property
    def has_error(self) -> bool:
        return self.error_condition is not None and self.error_condition != 0

    @property
    def session_active(self) -> bool | None:
        val = self._properties.get("session_state")
        if val is None:
            return None
        return int(val) == 1

    @property
    def session_time_remaining(self) -> int | None:
        val = self._properties.get("session_time_left")
        if val is None:
            return None
        return int(val)

    @property
    def firmware_version(self) -> str | None:
        return self._properties.get("device_fw_version")

    @property
    def has_session_feature(self) -> bool:
        return self.device_type in (
            DeviceType.AERA3,
            DeviceType.AERA3_1,
            DeviceType.AERA_MINI,
        )

    def update_properties(self, properties: dict[str, Any]) -> None:
        self._properties.update(properties)

    def __repr__(self) -> str:
        return (
            f"AeraDevice(dsn={self.dsn!r}, name={self.device_name!r}, "
            f"type={self.device_type.name}, online={self.is_online})"
        )
