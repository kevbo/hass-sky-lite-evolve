"""Constants for the Sky Lite Evolve integration."""

DOMAIN = "sky_lite_evolve"

# Connection modes
CONF_CONNECTION_TYPE = "connection_type"
CONNECTION_TYPE_CLOUD = "cloud"
CONNECTION_TYPE_LOCAL = "local"

# Cloud config keys
CONF_ACCESS_KEY = "access_key"
CONF_SECRET_KEY = "secret_key"
CONF_DEVICE_ID = "device_id"
CONF_REGION = "region"

# Local config keys
CONF_LOCAL_KEY = "local_key"
CONF_IP_ADDRESS = "ip_address"

# Tuya cloud regions (codes used by tinytuya.Cloud)
TUYA_REGIONS = {
    "us": "US (West)",
    "us-e": "US (East)",
    "eu": "EU (Central)",
    "eu-w": "EU (West)",
    "cn": "China",
    "in": "India",
}

# DPS codes for Evolve (Tuya local protocol)
DPS_POWER = "20"
DPS_MODE = "51"
DPS_COLOR_STATE = "52"
DPS_LASER_STATE = "53"
DPS_LASER_BRIGHTNESS = "54"
DPS_COLOR = "24"
DPS_BRIGHTNESS = "25"
DPS_SCENE = "58"
DPS_MOTOR_STATE = "60"
DPS_ROTATION = "62"

# Tuya Cloud API command codes
CMD_SWITCH_LED = "switch_led"
CMD_MODE = "star_work_mode"
CMD_COLOR_STATE = "colour_switch"
CMD_LASER_STATE = "laser_switch"
CMD_LASER_BRIGHTNESS = "laser_bright"
CMD_COLOR = "colour_data"
CMD_BRIGHTNESS = "bright_value"
CMD_SCENE = "star_scene_data"
CMD_MOTOR_STATE = "fan_switch"
CMD_ROTATION = "fan_speed"

# DPS -> Cloud command code mapping
DPS_TO_CLOUD_CODE = {
    DPS_POWER: CMD_SWITCH_LED,
    DPS_MODE: CMD_MODE,
    DPS_COLOR_STATE: CMD_COLOR_STATE,
    DPS_LASER_STATE: CMD_LASER_STATE,
    DPS_LASER_BRIGHTNESS: CMD_LASER_BRIGHTNESS,
    DPS_COLOR: CMD_COLOR,
    DPS_BRIGHTNESS: CMD_BRIGHTNESS,
    DPS_SCENE: CMD_SCENE,
    DPS_MOTOR_STATE: CMD_MOTOR_STATE,
    DPS_ROTATION: CMD_ROTATION,
}

# Value ranges
LASER_BRIGHTNESS_MIN = 10
LASER_BRIGHTNESS_MAX = 1000
ROTATION_SPEED_MIN = 1
ROTATION_SPEED_MAX = 100

# Tuya local protocol version for the Evolve
TUYA_VERSION = "3.5"
