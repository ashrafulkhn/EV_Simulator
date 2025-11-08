"""
Configuration constants and settings for EV Simulator
"""

# Application Settings
APP_TITLE = "EV Simulator"
APP_VERSION = "1.0.0"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

# UI Colors and Themes
COLORS = {
    'background': [1.0, 1.0, 1.0, 1.0],
    'surface': [1.0, 1.0, 1.0, 1.0],
    'text': [0.1, 0.1, 0.1, 1.0],
    'text_secondary': [0.5, 0.5, 0.5, 1.0]
}

# Central color theme in 0-255 RGBA. Change these to customize the app's look.
COLOR_THEME = {
    # Light, clean canvas
    'window_bg': [247, 249, 252, 255],
    'text': [20, 24, 28, 255],

    # Inputs (white fields, subtle borders)
    'input_bg': [255, 255, 255, 255],
    'input_bg_hovered': [244, 247, 252, 255],
    'input_bg_active': [233, 238, 245, 255],
    'input_border': [196, 205, 216, 255],

    # Surfaces
    'child_bg': [255, 255, 255, 255],

    # Tab fallback colors (tabs also themed to primary)
    'tab': [227, 232, 240, 255],
    'tab_hovered': [210, 219, 235, 255],
    'tab_active': [60, 120, 255, 255],
    'tab_unfocused': [227, 232, 240, 255],
    'tab_unfocused_active': [210, 219, 235, 255],
}

# Button color palette (normal, hovered, active) in 0-255 RGBA
BUTTON_PALETTE = {
    # Indigo primary
    'primary': ([79, 70, 229, 255], [99, 102, 241, 255], [67, 56, 202, 255]),
    # Slate secondary
    'secondary': ([100, 116, 139, 255], [148, 163, 184, 255], [71, 85, 105, 255]),
    # Cyan accent
    'accent': ([6, 182, 212, 255], [34, 211, 238, 255], [8, 145, 178, 255]),
    # Emerald success
    'success': ([16, 185, 129, 255], [52, 211, 153, 255], [5, 150, 105, 255]),
    # Amber warning
    'warning': ([245, 158, 11, 255], [251, 191, 36, 255], [217, 119, 6, 255]),
    # Rose error
    'error': ([244, 63, 94, 255], [251, 113, 133, 255], [225, 29, 72, 255]),
}

# WebSocket Settings
DEFAULT_WS_URI = "ws://192.168.3.110:8765/GUN4" # This is the default URI for the websocket server. This is running on my machine.
CONNECTION_TIMEOUT = 10
RECONNECT_ATTEMPTS = 3

# Message Settings
VEHICLE_ID = "fca47a148ee4"
DEFAULT_SEQUENCE_NUMBER = 1226

# Form Default Values
DEFAULT_FORM_VALUES = {
    'evMaxCurrentAmperes': 217.8,
    'evMaxVoltageVolts': 450.0,
    'evMinCurrentAmperes': 0.0,
    'evMinPowerWatts': 0.0,
    'evMinVoltageVolts': 0.0,
    'chargingProfileMaxPowerLimitWatts': 22000.0,
    'cableCheckVoltage': 450.0,
    'batteryStateOfCharge': 10.0,
    'targetCurrent': 1.8,
    'targetVoltage': 402.2
}

# UI Layout Constants
PADDING = 10
BUTTON_HEIGHT = 30
INPUT_HEIGHT = 25
LOG_HEIGHT = 200
