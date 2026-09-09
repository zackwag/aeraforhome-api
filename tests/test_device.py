"""Tests for AeraDevice and DeviceType."""

from __future__ import annotations

import pytest

from aera.device import AeraDevice, DeviceType
from aera.contentful import FragranceInfo


class TestDeviceType:

    @pytest.mark.parametrize(
        "oem_model, expected",
        [
            ("aera1", DeviceType.AERA1),
            ("aera2", DeviceType.AERA2),
            ("aera3", DeviceType.AERA3),
            ("aera31", DeviceType.AERA3_1),
            ("aeraMini", DeviceType.AERA_MINI),
            ("unknown_model", DeviceType.UNKNOWN),
            ("", DeviceType.UNKNOWN),
            (None, DeviceType.UNKNOWN),
        ],
    )
    def test_from_oem_model(self, oem_model, expected):
        assert DeviceType.from_oem_model(oem_model) == expected

    @pytest.mark.parametrize(
        "device_type, expected",
        [
            (DeviceType.AERA1, True),
            (DeviceType.AERA2, True),
            (DeviceType.AERA3, True),
            (DeviceType.AERA3_1, True),
            (DeviceType.AERA_MINI, False),
            (DeviceType.UNKNOWN, False),
        ],
    )
    def test_is_full_size(self, device_type, expected):
        assert device_type.is_full_size is expected

    @pytest.mark.parametrize(
        "device_type, expected",
        [
            (DeviceType.AERA_MINI, True),
            (DeviceType.AERA1, False),
            (DeviceType.UNKNOWN, False),
        ],
    )
    def test_is_mini(self, device_type, expected):
        assert device_type.is_mini is expected

    def test_max_intensity_full_size(self):
        assert DeviceType.AERA3.max_intensity == 10

    def test_max_intensity_mini(self):
        assert DeviceType.AERA_MINI.max_intensity == 5

    def test_max_intensity_unknown(self):
        assert DeviceType.UNKNOWN.max_intensity == 5


class TestAeraDeviceBasicProperties:

    def test_dsn(self, device):
        assert device.dsn == "AC000W123456789"

    def test_device_key(self, device):
        assert device.device_key == 12345

    def test_product_name(self, device):
        assert device.product_name == "Aera 3.0"

    def test_device_name_no_room(self, device):
        assert device.device_name == "Living Room"

    def test_device_name_with_room(self, device):
        device.room_name = "Kitchen"
        assert device.device_name == "Kitchen"

    def test_device_name_room_cleared(self, device):
        device.room_name = "Kitchen"
        device.room_name = ""
        assert device.device_name == "Living Room"

    def test_room_name_none_on_empty_string(self, device):
        device.room_name = ""
        assert device.room_name is None

    def test_oem_model(self, device):
        assert device.oem_model == "aera3"

    def test_device_type(self, device):
        assert device.device_type == DeviceType.AERA3

    def test_model(self, device):
        assert device.model == "AY001MUS1"

    def test_sw_version(self, device):
        assert device.sw_version == "2.5.0"

    def test_mac(self, device):
        assert device.mac == "00:11:22:33:44:55"

    def test_lan_ip(self, device):
        assert device.lan_ip == "192.168.1.100"

    def test_connected_at(self, device):
        assert device.connected_at == "2024-01-01T00:00:00Z"

    def test_is_online_true(self, device):
        assert device.is_online is True

    def test_is_online_false(self):
        data = {"connection_status": "Offline"}
        assert AeraDevice(data).is_online is False

    def test_is_online_missing(self):
        assert AeraDevice({}).is_online is False

    def test_max_intensity_delegates_to_type(self, device, mini_device):
        assert device.max_intensity == 10
        assert mini_device.max_intensity == 5

    def test_repr(self, device):
        r = repr(device)
        assert "AC000W123456789" in r
        assert "AERA3" in r

    def test_missing_data_defaults(self):
        dev = AeraDevice({})
        assert dev.dsn == ""
        assert dev.device_key == 0
        assert dev.product_name == ""
        assert dev.oem_model == ""
        assert dev.sw_version is None
        assert dev.mac is None
        assert dev.lan_ip is None
        assert dev.connected_at is None


class TestAeraDeviceProperties:

    def test_properties_from_constructor(self, device_with_props):
        assert device_with_props.is_power_on is True
        assert device_with_props.intensity == 5

    def test_update_properties(self, device):
        assert device.is_power_on is None
        device.update_properties({"power_state": 1})
        assert device.is_power_on is True

    def test_power_on(self):
        dev = AeraDevice({}, properties={"power_state": 1})
        assert dev.is_power_on is True

    def test_power_off(self):
        dev = AeraDevice({}, properties={"power_state": 0})
        assert dev.is_power_on is False

    def test_power_none(self):
        assert AeraDevice({}).is_power_on is None

    def test_intensity(self):
        dev = AeraDevice({}, properties={"intensity_state": 7})
        assert dev.intensity == 7

    def test_intensity_none(self):
        assert AeraDevice({}).intensity is None

    def test_cartridge_usage(self):
        dev = AeraDevice({}, properties={"cartridge_usage": 42})
        assert dev.cartridge_usage == 42

    def test_cartridge_usage_none(self):
        assert AeraDevice({}).cartridge_usage is None

    def test_is_cartridge_present_true(self):
        dev = AeraDevice({}, properties={"cartridge_present": 1})
        assert dev.is_cartridge_present is True

    def test_is_cartridge_present_false(self):
        dev = AeraDevice({}, properties={"cartridge_present": 0})
        assert dev.is_cartridge_present is False

    def test_is_cartridge_present_none(self):
        assert AeraDevice({}).is_cartridge_present is None

    def test_error_condition(self):
        dev = AeraDevice({}, properties={"error_condition": 3})
        assert dev.error_condition == 3
        assert dev.has_error is True

    def test_no_error(self):
        dev = AeraDevice({}, properties={"error_condition": 0})
        assert dev.has_error is False

    def test_has_error_none(self):
        assert AeraDevice({}).has_error is False

    def test_session_active_true(self):
        dev = AeraDevice({}, properties={"session_state": 1})
        assert dev.session_active is True

    def test_session_active_false(self):
        dev = AeraDevice({}, properties={"session_state": 0})
        assert dev.session_active is False

    def test_session_active_none(self):
        assert AeraDevice({}).session_active is None

    def test_session_time_remaining(self):
        dev = AeraDevice({}, properties={"session_time_left": 30})
        assert dev.session_time_remaining == 30

    def test_session_time_remaining_none(self):
        assert AeraDevice({}).session_time_remaining is None

    def test_firmware_version(self):
        dev = AeraDevice({}, properties={"device_fw_version": "2.5.1"})
        assert dev.firmware_version == "2.5.1"

    def test_firmware_version_none(self):
        assert AeraDevice({}).firmware_version is None


class TestAeraDeviceFragrance:

    def test_fragrance_remaining_full_size(self):
        dev = AeraDevice(
            {"oem_model": "aera3"},
            properties={"cartridge_usage": 30, "cartridge_present": 1},
        )
        assert dev.fragrance_remaining == 70

    def test_fragrance_remaining_full_size_max(self):
        dev = AeraDevice(
            {"oem_model": "aera3"},
            properties={"cartridge_usage": 0, "cartridge_present": 1},
        )
        assert dev.fragrance_remaining == 100

    def test_fragrance_remaining_full_size_empty(self):
        dev = AeraDevice(
            {"oem_model": "aera3"},
            properties={"cartridge_usage": 120, "cartridge_present": 1},
        )
        assert dev.fragrance_remaining == 0

    def test_fragrance_remaining_no_cartridge(self):
        dev = AeraDevice(
            {"oem_model": "aera3"},
            properties={"cartridge_usage": 30, "cartridge_present": 0},
        )
        assert dev.fragrance_remaining is None

    def test_fragrance_remaining_no_usage_data(self):
        dev = AeraDevice({"oem_model": "aera3"}, properties={"cartridge_present": 1})
        assert dev.fragrance_remaining is None

    def test_fragrance_remaining_mini_with_info(self, sample_fragrance):
        dev = AeraDevice(
            {"oem_model": "aeraMini"},
            properties={
                "pump_life_time": 5000,
                "pump_life_time_qr_scanned": 1000,
            },
        )
        dev.fragrance_info = sample_fragrance
        result = dev.fragrance_remaining
        assert result is not None
        assert 0 <= result <= 100

    def test_fragrance_remaining_mini_no_pump_data(self):
        dev = AeraDevice({"oem_model": "aeraMini"})
        assert dev.fragrance_remaining is None

    def test_fragrance_remaining_mini_no_fragrance_info(self):
        dev = AeraDevice(
            {"oem_model": "aeraMini"},
            properties={
                "pump_life_time": 5000,
                "pump_life_time_qr_scanned": 1000,
            },
        )
        assert dev.fragrance_remaining is None

    def test_fragrance_remaining_mini_no_fill_data(self):
        dev = AeraDevice(
            {"oem_model": "aeraMini"},
            properties={
                "pump_life_time": 5000,
                "pump_life_time_qr_scanned": 1000,
            },
        )
        dev.fragrance_info = FragranceInfo(
            fragrance_id="X",
            fragrance_qr=None,
            fragrance_name="Test",
            firmware_name=None,
            color=None,
            mini_fill=None,
            mini_output=None,
        )
        assert dev.fragrance_remaining is None

    def test_fragrance_name_from_info(self, device_with_props, sample_fragrance):
        device_with_props.fragrance_info = sample_fragrance
        assert device_with_props.fragrance_name == "Ocean Mist"

    def test_fragrance_name_from_property(self, device_with_props):
        assert device_with_props.fragrance_name == "Ocean Mist"

    def test_fragrance_name_no_cartridge(self):
        dev = AeraDevice(
            {"oem_model": "aera3"},
            properties={"cartridge_present": 0},
        )
        assert dev.fragrance_name is None

    def test_fragrance_name_none(self):
        assert AeraDevice({}).fragrance_name is None

    def test_fragrance_color_from_info(self, device_with_props, sample_fragrance):
        device_with_props.fragrance_info = sample_fragrance
        assert device_with_props.fragrance_color == "#3A7BD5"

    def test_fragrance_color_no_info(self, device_with_props):
        assert device_with_props.fragrance_color is None

    def test_fragrance_color_no_cartridge(self):
        dev = AeraDevice(
            {"oem_model": "aera3"},
            properties={"cartridge_present": 0},
        )
        dev.fragrance_info = FragranceInfo(
            fragrance_id=None,
            fragrance_qr=None,
            fragrance_name="Test",
            firmware_name=None,
            color="#FF0000",
            mini_fill=None,
            mini_output=None,
        )
        assert dev.fragrance_color is None

    def test_fragrance_identifier_from_set(self):
        dev = AeraDevice({}, properties={"set_fragrance_identifier": "ABC"})
        assert dev.fragrance_identifier == "ABC"

    def test_fragrance_identifier_fallback_to_name(self):
        dev = AeraDevice({}, properties={"fragrance_name": "Lavender"})
        assert dev.fragrance_identifier == "Lavender"

    def test_fragrance_identifier_none(self):
        assert AeraDevice({}).fragrance_identifier is None

    def test_fragrance_info_setter(self, device, sample_fragrance):
        assert device.fragrance_info is None
        device.fragrance_info = sample_fragrance
        assert device.fragrance_info is sample_fragrance


class TestAeraDeviceSessionFeature:

    @pytest.mark.parametrize(
        "oem_model, expected",
        [
            ("aera3", True),
            ("aera31", True),
            ("aeraMini", True),
            ("aera1", False),
            ("aera2", False),
        ],
    )
    def test_has_session_feature(self, oem_model, expected):
        dev = AeraDevice({"oem_model": oem_model})
        assert dev.has_session_feature is expected
