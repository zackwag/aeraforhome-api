# aeraforhome-api

Unofficial Python client for the Aera for Home smart fragrance diffuser cloud API, reverse-engineered from the Android app (v2.3.6). Covers:

- **Authentication**: email/password login via the Ayla Networks IoT platform, automatic token refresh on 401.
- **Device control**: power on/off, intensity adjustment, timed fragrance sessions, schedule management.
- **Device state**: fragrance name, remaining percentage, cartridge presence, error conditions.
- **Fragrance catalog**: Mini fragrance lookup with names, codes, and QR URLs via Contentful CMS.

This library is designed to power a Home Assistant integration, but has no dependency on Home Assistant and can be used standalone.

## Installation

```bash
pip install aeraforhome
```

Or install from source:

```bash
pip install -e .
```

## Usage

```python
import asyncio
from aera import AeraApi

async def main():
    api = AeraApi("your-email@example.com", "your-password")

    try:
        await api.login()

        devices = await api.get_devices()
        for device in devices:
            props = await api.get_device_properties(device)
            print(f"{device.device_name}: {device.fragrance_name} ({device.fragrance_remaining}%)")

        # Control a device
        await api.set_power(devices[0], True)
        await api.set_intensity(devices[0], 5)

        # Start a 60-minute session
        await api.start_session(devices[0], 60)

        # Get all Mini-compatible fragrances (for QR scanning)
        fragrances = await api.get_mini_fragrances()
        for f in fragrances:
            print(f"{f['name']} ({f['code']}): {f['qr_url']}")

    finally:
        await api.close()

asyncio.run(main())
```

## Supported Devices

| Model | Type | Max Intensity |
|-------|------|---------------|
| Aera 1 | `aera1` | 10 |
| Aera 2 | `aera2` | 10 |
| Aera 3 | `aera3` | 10 |
| Aera 3.1 | `aera31` | 10 |
| Aera Mini | `aeraMini` | 5 |

## API Methods

| Method | Description |
|--------|-------------|
| `login()` | Authenticate with email/password |
| `refresh_auth()` | Refresh the access token |
| `get_devices()` | Fetch all devices (includes room names) |
| `get_device_properties(device)` | Fetch current state for a device |
| `set_power(device, on)` | Turn device on/off |
| `set_intensity(device, level)` | Set fragrance intensity |
| `start_session(device, minutes)` | Start a timed session |
| `stop_session(device)` | Stop a running session |
| `get_schedules(device)` | Fetch device schedules |
| `update_schedule(key, data)` | Update a schedule |
| `get_schedule_actions(key)` | Fetch actions (intensity) for a schedule |
| `create_schedule_action(key, data)` | Create an action on a schedule |
| `update_schedule_action(key, data)` | Update an existing schedule action |
| `delete_schedule_action(key)` | Delete a schedule action |
| `eject_cartridge(device)` | Eject the fragrance cartridge (full-size only) |
| `get_mini_fragrances()` | Get all Mini fragrance names, codes, and QR URLs |
| `get_device_metadata()` | Fetch user-assigned room names and positions |
| `sign_out()` | Sign out from the service |
| `close()` | Close the HTTP session |

## Device Properties

| Property | Description |
|----------|-------------|
| `device_name` | User-assigned room name (falls back to product name) |
| `device_type` | `DeviceType` enum |
| `is_online` | Connection status |
| `is_power_on` | Power state |
| `intensity` | Current intensity level |
| `fragrance_name` | Resolved fragrance name (via Contentful for Mini) |
| `fragrance_color` | Hex color from fragrance catalog |
| `fragrance_remaining` | Percentage remaining (0-100) |
| `is_cartridge_present` | Whether a cartridge is inserted (full-size only) |
| `session_active` | Whether a timed session is running |
| `session_time_remaining` | Minutes left in session |
| `has_error` | Whether the device has an error condition |
| `error_condition` | Error code (integer, 0 = no error) |
| `firmware_version` | Device firmware version string |
| `max_intensity` | Maximum intensity level for this device type |
| `has_session_feature` | Whether the device supports timed sessions |
| `device_key` | Ayla device key (used for schedule APIs) |

## Scripts

- **`example.py`** - Minimal usage example showing device listing and control.
- **`test_local.py`** - Interactive test script that dumps all device properties including raw values, useful for debugging.
- **`test_schedules.py`** - Dumps active schedules and their actions (intensity values) for all devices.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Disclaimer

This is an unofficial, reverse-engineered client with no affiliation to Aera, Prolitec, or Ayla Networks. It may break if the upstream API changes.
