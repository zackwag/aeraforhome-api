"""Dump schedule data for debugging."""

import asyncio
from getpass import getpass

from aera import AeraApi


async def main():
    email = input("Aera email: ")
    password = getpass("Aera password: ")

    api = AeraApi(email, password)
    try:
        await api.login()

        devices = await api.get_devices()
        for device in devices:
            schedules = await api.get_schedules(device)
            if schedules:
                print(f"\n--- {device.device_name} ({device.device_type.name}) ---")
                active = [s for s in schedules if s.get("active")]
                print(f"  Total slots: {len(schedules)}, Active: {len(active)}")
                for s in active:
                    print(f"\n  Schedule: {s.get('display_name', s.get('name'))}")
                    print(f"    Key: {s.get('key')}")
                    print(
                        f"    Time: {s.get('start_time_each_day')} - {s.get('end_time_each_day')}"
                    )
                    print(f"    Days: {s.get('days_of_week')}")
                    print(f"    Active: {s.get('active')}")

                    # Fetch actions for this schedule
                    actions = await api.get_schedule_actions(s["key"])
                    if actions:
                        print(f"    Actions ({len(actions)}):")
                        for a in actions:
                            print(
                                f"      - {a.get('name')}: {a.get('value')} "
                                f"(type={a.get('base_type')}, active={a.get('active')}, "
                                f"in_range={a.get('in_range')}, at_start={a.get('at_start')}, "
                                f"at_end={a.get('at_end')}, key={a.get('key')})"
                            )
                    else:
                        print("    Actions: none")
    finally:
        await api.close()


if __name__ == "__main__":
    asyncio.run(main())
