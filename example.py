"""Example usage of the Aera for Home API."""

import asyncio

from aera import AeraApi


async def main():
    api = AeraApi("your-email@example.com", "your-password")

    try:
        await api.login()
        print("Logged in successfully!")

        devices = await api.get_devices()
        print(f"\nFound {len(devices)} device(s):")

        for device in devices:
            print(f"\n  {device}")
            print(f"    DSN: {device.dsn}")
            print(f"    Type: {device.device_type.name}")
            print(f"    Online: {device.is_online}")

            # Fetch properties
            props = await api.get_device_properties(device)
            print(f"    Power: {'On' if device.is_power_on else 'Off'}")
            print(f"    Intensity: {device.intensity}/{device.max_intensity}")
            print(f"    Fragrance: {device.fragrance_name}")
            print(f"    Cartridge remaining: {device.fragrance_remaining}%")

            if device.has_error:
                print(f"    ERROR: condition code {device.error_condition}")

            # Example: turn on and set intensity
            # await api.set_power(device, True)
            # await api.set_intensity(device, 5)

            # Example: start a 60-minute session
            # await api.start_session(device, 60)

    finally:
        await api.close()


if __name__ == "__main__":
    asyncio.run(main())
