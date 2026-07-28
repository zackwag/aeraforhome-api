"""Quick local test - run with: python test_local.py"""

import asyncio
from getpass import getpass

from aera import AeraApi


async def main():
    email = input("Aera email: ")
    password = getpass("Aera password: ")

    api = AeraApi(email, password)

    try:
        print("\nLogging in...")
        await api.login()
        print("Success!\n")

        print("Fetching devices...")
        devices = await api.get_devices()
        print(f"Found {len(devices)} device(s)")

        print()

        for device in devices:
            print(f"--- {device.device_name} ---")
            print(f"  DSN:      {device.dsn}")
            print(f"  Type:     {device.device_type.name}")
            print(f"  Online:   {device.is_online}")

            print("  Fetching properties...")
            props = await api.get_device_properties(device)

            print(f"  Power:     {'On' if device.is_power_on else 'Off'}")
            print(f"  Intensity: {device.intensity}/{device.max_intensity}")
            print(f"  Fragrance: {device.fragrance_name}")
            if device.fragrance_color:
                print(f"  Color:     {device.fragrance_color}")
            remaining = device.fragrance_remaining
            print(f"  Remaining: {remaining}%" if remaining is not None else "  Remaining: N/A")
            print(f"  Session:   {'Active' if device.session_active else 'Inactive'}")
            if device.has_error:
                print(f"  ERROR:     code {device.error_condition}")

            # Dump relevant raw properties for debugging
            print("  --- Raw properties ---")
            for key in sorted(props.keys()):
                val = props[key]
                if val is not None and val != "" and val != 0:
                    print(f"    {key} = {val!r}")
            print()

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        await api.close()


if __name__ == "__main__":
    asyncio.run(main())
