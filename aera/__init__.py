"""Aera for Home API - Python wrapper for the Aera smart fragrance diffuser."""

from aera.api import AeraApi
from aera.const import (
    AERA_APP_ID,
    AERA_APP_SECRET,
)
from aera.device import AeraDevice, DeviceType

__all__ = [
    "AERA_APP_ID",
    "AERA_APP_SECRET",
    "AeraApi",
    "AeraDevice",
    "DeviceType",
]
