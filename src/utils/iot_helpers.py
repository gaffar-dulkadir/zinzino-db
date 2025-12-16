"""
IoT Helper functions for Zinzino device management.

This module provides utility functions for device validation,
dispense calculations, and threshold checks.
"""

import re
from typing import Dict
from decimal import Decimal


def validate_mac_address(mac: str) -> bool:
    """
    Validate MAC address format.
    
    Args:
        mac: MAC address string
        
    Returns:
        True if valid, False otherwise
    """
    # Accept formats: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
    mac_pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
    return bool(re.match(mac_pattern, mac))


def normalize_mac_address(mac: str) -> str:
    """
    Normalize MAC address to standard format (uppercase with colons).
    
    Args:
        mac: MAC address string
        
    Returns:
        Normalized MAC address
    """
    return mac.replace("-", ":").upper()


def validate_serial_number(serial: str) -> bool:
    """
    Validate device serial number format.
    
    Args:
        serial: Serial number string
        
    Returns:
        True if valid, False otherwise
    """
    # Serial number should be alphanumeric, 8-100 characters
    serial_pattern = r"^[A-Z0-9]{8,100}$"
    return bool(re.match(serial_pattern, serial.upper()))


def calculate_dispense_amount(device_type: str) -> str:
    """
    Calculate dispense amount based on device type.
    
    Args:
        device_type: Type of supplement dispenser
        
    Returns:
        Dose amount as string (e.g., "5ml", "1 capsule")
    """
    dispense_amounts: Dict[str, str] = {
        "fish_oil": "5ml",
        "vitamin_d": "1000 IU",
        "krill_oil": "3ml",
        "vegan": "5ml"
    }
    
    return dispense_amounts.get(device_type, "1 dose")


def check_battery_alert_threshold(level: int) -> bool:
    """
    Check if battery level is below alert threshold.
    
    Args:
        level: Battery level (0-100)
        
    Returns:
        True if alert should be triggered
    """
    BATTERY_THRESHOLD = 20
    return level <= BATTERY_THRESHOLD


def check_supplement_alert_threshold(level: int) -> bool:
    """
    Check if supplement level is below alert threshold.
    
    Args:
        level: Supplement level (0-100)
        
    Returns:
        True if alert should be triggered
    """
    SUPPLEMENT_THRESHOLD = 20
    return level <= SUPPLEMENT_THRESHOLD


def validate_battery_level(level: int) -> bool:
    """
    Validate battery level is within range.
    
    Args:
        level: Battery level
        
    Returns:
        True if valid (0-100)
    """
    return 0 <= level <= 100


def validate_supplement_level(level: int) -> bool:
    """
    Validate supplement level is within range.
    
    Args:
        level: Supplement level
        
    Returns:
        True if valid (0-100)
    """
    return 0 <= level <= 100


def validate_sensor_reading(reading: Decimal) -> bool:
    """
    Validate sensor reading is within acceptable range.
    
    Args:
        reading: Sensor reading value
        
    Returns:
        True if valid (0-999.99)
    """
    return Decimal("0") <= reading <= Decimal("999.99")


def calculate_supplement_doses_remaining(level: int, device_type: str) -> int:
    """
    Estimate remaining doses based on supplement level.
    
    Args:
        level: Current supplement level percentage (0-100)
        device_type: Type of device
        
    Returns:
        Estimated number of doses remaining
    """
    # Maximum doses per device type (when full at 100%)
    max_doses: Dict[str, int] = {
        "fish_oil": 60,      # ~60 doses of 5ml each
        "vitamin_d": 100,    # 100 capsules
        "krill_oil": 40,     # ~40 doses of 3ml each
        "vegan": 60          # ~60 doses of 5ml each
    }
    
    total_capacity = max_doses.get(device_type, 50)
    return int((level / 100) * total_capacity)


def get_device_status_summary(
    is_active: bool,
    is_connected: bool,
    battery_level: int,
    supplement_level: int
) -> str:
    """
    Get comprehensive device status summary.
    
    Args:
        is_active: Device active status
        is_connected: Connection status
        battery_level: Battery level
        supplement_level: Supplement level
        
    Returns:
        Status summary string
    """
    if not is_active:
        return "inactive"
    if not is_connected:
        return "disconnected"
    if check_battery_alert_threshold(battery_level):
        return "low_battery"
    if check_supplement_alert_threshold(supplement_level):
        return "low_supplement"
    return "ok"
