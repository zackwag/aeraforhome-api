"""Constants extracted from the Aera for Home Android app."""

AERA_APP_ID = "android-id-id"
AERA_APP_SECRET = "android-id-oYOAkxPCU46_E04WxtwfOYatrUI"

USER_SERVICE_URL = "https://user-field.aylanetworks.com"
DEVICE_SERVICE_URL = "https://ads-field.aylanetworks.com"

# Properties written TO device (inputs)
PROP_SET_POWER_STATE = "set_power_state"
PROP_SET_INTENSITY_MANUAL = "set_intensity_manual"
PROP_SET_INTENSITY_SCHEDULE = "set_intensity_sched"
PROP_SET_SESSION_LENGTH = "set_session_length"
PROP_SET_FRAGRANCE_IDENTIFIER = "set_fragrance_identifier"
PROP_DEVICE_FW_VERSION = "device_fw_version"
PROP_QR_SCANNED_TIME = "pump_life_time_qr_scanned"

# Properties read FROM device (outputs)
PROP_POWER_STATE = "power_state"
PROP_INTENSITY_STATE = "intensity_state"
PROP_CARTRIDGE_USAGE = "cartridge_usage"
PROP_CARTRIDGE_PRESENT = "cartridge_present"
PROP_FRAGRANCE_NAME = "fragrance_name"
PROP_ERROR_CONDITION = "error_condition"
PROP_INTERRUPT_SCHEDULE = "interrupt_schedule"
PROP_SESSION_STATE = "session_state"
PROP_SESSION_TIME_LEFT = "session_time_left"
PROP_PUMP_LIFE_TIME = "pump_life_time"

DEVICE_METADATA_KEY = "device_data_table"

ALL_READABLE_PROPERTIES = [
    PROP_POWER_STATE,
    PROP_INTENSITY_STATE,
    PROP_CARTRIDGE_USAGE,
    PROP_CARTRIDGE_PRESENT,
    PROP_FRAGRANCE_NAME,
    PROP_ERROR_CONDITION,
    PROP_INTERRUPT_SCHEDULE,
    PROP_SESSION_STATE,
    PROP_SESSION_TIME_LEFT,
    PROP_PUMP_LIFE_TIME,
    PROP_SET_INTENSITY_MANUAL,
    PROP_SET_POWER_STATE,
    PROP_SET_SESSION_LENGTH,
    PROP_SET_FRAGRANCE_IDENTIFIER,
    PROP_DEVICE_FW_VERSION,
    PROP_QR_SCANNED_TIME,
]
