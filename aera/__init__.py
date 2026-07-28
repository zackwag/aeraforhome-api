"""Aera for Home API - Python wrapper for the Aera smart fragrance diffuser."""

from aera.api import AeraApi
from aera.device import AeraDevice, DeviceType
from aera.const import (
    AERA_APP_ID,
    AERA_APP_SECRET,
)

__all__ = [
    "AeraApi",
    "AeraDevice",
    "DeviceType",
    "AERA_APP_ID",
    "AERA_APP_SECRET",
]
