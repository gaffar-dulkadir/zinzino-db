"""
Device service for Zinzino IoT application.

This module provides business logic for device management operations.
"""

import os
import subprocess
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from datalayer.model.zinzino_models import Device
from datalayer.model.dto.device_dto import (
    DeviceCreateDTO, DeviceUpdateDTO, DeviceResponseDTO, DeviceBulkUpdateDTO
)
from datalayer.repository.device_repository import DeviceRepository
from datalayer.repository.activity_repository import ActivityLogRepository
from datalayer.mapper.device_mapper import DeviceMapper
from utils.exceptions import (
    NotFoundError, DuplicateError, ForbiddenError, ValidationError
)
from utils.iot_helpers import (
    normalize_mac_address, validate_mac_address, validate_serial_number,
    validate_battery_level, validate_supplement_level
)


class DeviceService:
    """Service for handling device operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.device_repo = DeviceRepository(session)
        self.activity_repo = ActivityLogRepository(session)
        self.mapper = DeviceMapper()
    
    async def scan_wifi(self) -> Dict[str, Any]:
        """
        Scan for Wi-Fi networks using multiple Linux tools.
        Tries nmcli, iw, and iwlist in order for real WiFi scanning.
        
        Returns:
            Dictionary with list of networks and scan metadata
            
        Raises:
            Exception: If no WiFi scanning method works
        """
        networks = []
        platform = os.name # 'posix' for linux/mac, 'nt' for windows
        scan_method = None
        error_messages = []
        
        if platform != 'posix':
            raise Exception("WiFi scanning is only supported on Linux/Unix systems")
        
        # Method 1: Try nmcli (NetworkManager - most reliable)
        try:
            process = await asyncio.create_subprocess_shell(
                'nmcli -t -f SSID,SIGNAL,SECURITY dev wifi list 2>&1',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if stdout and process.returncode == 0:
                lines = stdout.decode().strip().split('\n')
                for line in lines:
                    if line and line.strip() and not line.startswith('Error'):
                        parts = line.split(':')
                        if len(parts) >= 2:
                            ssid = parts[0].strip()
                            signal_str = parts[1].strip()
                            security = parts[2].strip() if len(parts) > 2 else ''
                            
                            # Parse signal - convert to dBm if percentage
                            try:
                                signal = int(signal_str)
                                # If signal is 0-100, convert to dBm (-100 to -30)
                                if 0 <= signal <= 100:
                                    signal = -100 + (signal * 70 // 100)
                            except:
                                signal = -70
                            
                            if ssid and ssid != '--' and ssid != '\\x00':
                                networks.append({
                                    "ssid": ssid,
                                    "level": signal,
                                    "capabilities": security
                                })
                if networks:
                    scan_method = "nmcli"
                    print(f"✅ WiFi scan successful via nmcli: {len(networks)} networks")
            else:
                error_msg = stderr.decode() if stderr else "nmcli command failed"
                error_messages.append(f"nmcli: {error_msg}")
        except Exception as e:
            error_messages.append(f"nmcli: {str(e)}")
        
        # Method 2: Try iw (modern Linux WiFi tool)
        if not networks:
            try:
                # Get wireless interface
                iface_process = await asyncio.create_subprocess_shell(
                    'iw dev 2>/dev/null | grep Interface | head -n1 | awk \'{print $2}\'',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                iface_out, _ = await iface_process.communicate()
                interface = iface_out.decode().strip()
                
                if interface:
                    # Trigger scan and get results
                    process = await asyncio.create_subprocess_shell(
                        f'sudo -n iw dev {interface} scan 2>&1',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, _ = await process.communicate()
                    
                    if stdout and process.returncode == 0:
                        current_ssid = ""
                        current_signal = -70
                        
                        for line in stdout.decode().split('\n'):
                            line = line.strip()
                            if line.startswith('SSID:'):
                                current_ssid = line.split('SSID:')[1].strip()
                            elif 'signal:' in line:
                                try:
                                    signal_str = line.split('signal:')[1].strip()
                                    current_signal = int(float(signal_str.split()[0]))
                                except:
                                    pass
                                
                                # Add network when we have both SSID and signal
                                if current_ssid:
                                    networks.append({
                                        "ssid": current_ssid,
                                        "level": current_signal,
                                        "capabilities": "Unknown"
                                    })
                                    current_ssid = ""
                                    current_signal = -70
                        
                        if networks:
                            scan_method = "iw"
                            print(f"✅ WiFi scan successful via iw: {len(networks)} networks")
                    else:
                        error_messages.append("iw: scan failed or requires sudo")
                else:
                    error_messages.append("iw: no wireless interface found")
            except Exception as e:
                error_messages.append(f"iw: {str(e)}")
        
        # Method 3: Try iwlist (legacy but widely available)
        if not networks:
            try:
                # Get wireless interface
                iface_process = await asyncio.create_subprocess_shell(
                    'iwconfig 2>/dev/null | grep -o "^[a-z0-9]*" | head -n1',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                iface_out, _ = await iface_process.communicate()
                interface = iface_out.decode().strip()
                
                if interface:
                    process = await asyncio.create_subprocess_shell(
                        f'sudo -n iwlist {interface} scan 2>&1',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, _ = await process.communicate()
                    
                    if stdout and 'Cell ' in stdout.decode():
                        cells = stdout.decode().split('Cell ')
                        for cell in cells[1:]:
                            ssid = ""
                            signal = -70
                            
                            for line in cell.split('\n'):
                                if 'ESSID:' in line:
                                    ssid = line.split('ESSID:')[1].strip().strip('"')
                                elif 'Signal level=' in line:
                                    try:
                                        if 'dBm' in line:
                                            signal_str = line.split('Signal level=')[1].split('dBm')[0].strip()
                                            signal = int(float(signal_str))
                                        else:
                                            # Handle percentage format
                                            signal_str = line.split('Signal level=')[1].split('/')[0].strip()
                                            signal_pct = int(signal_str)
                                            signal = -100 + (signal_pct * 70 // 100)
                                    except:
                                        pass
                            
                            if ssid:
                                networks.append({
                                    "ssid": ssid,
                                    "level": signal,
                                    "capabilities": "Unknown"
                                })
                        
                        if networks:
                            scan_method = "iwlist"
                            print(f"✅ WiFi scan successful via iwlist: {len(networks)} networks")
                    else:
                        error_messages.append("iwlist: scan failed or requires sudo")
                else:
                    error_messages.append("iwlist: no wireless interface found")
            except Exception as e:
                error_messages.append(f"iwlist: {str(e)}")
        
        # If still no networks, raise error with details
        if not networks:
            error_detail = " | ".join(error_messages) if error_messages else "Unknown error"
            raise Exception(
                f"WiFi scanning failed. Tried nmcli, iw, and iwlist. "
                f"Install NetworkManager (nmcli) or ensure wireless-tools are installed. "
                f"Errors: {error_detail}"
            )
        
        # Remove duplicates and sort by signal strength
        unique_networks = []
        seen_ssids = set()
        for network in networks:
            if network["ssid"] not in seen_ssids:
                seen_ssids.add(network["ssid"])
                unique_networks.append(network)
        
        unique_networks.sort(key=lambda x: x["level"], reverse=True)
        
        return {
            "networks": unique_networks,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "scan_method": scan_method,
            "total": len(unique_networks)
        }
    
    async def list_devices(
        self,
        user_id: str,
        include_inactive: bool = False,
        sort: str = "name",
        order: str = "asc"
    ) -> List[DeviceResponseDTO]:
        """
        List all devices for a user.
        
        Args:
            user_id: User UUID
            include_inactive: Include inactive devices
            sort: Sort field (name, created_at, type)
            order: Sort order (asc, desc)
            
        Returns:
            List of device DTOs
        """
        # Get devices from repository
        devices = await self.device_repo.get_all_by_user(user_id, include_inactive)
        
        # Sort devices
        reverse = (order.lower() == "desc")
        if sort == "name":
            devices = sorted(devices, key=lambda d: d.device_name.lower(), reverse=reverse)
        elif sort == "created_at":
            devices = sorted(devices, key=lambda d: d.created_at, reverse=reverse)
        elif sort == "type":
            devices = sorted(devices, key=lambda d: d.device_type, reverse=reverse)
        
        # Convert to DTOs
        return self.mapper.to_dto_list(devices)
    
    async def get_device(self, user_id: str, device_id: str) -> DeviceResponseDTO:
        """
        Get a specific device.
        
        Args:
            user_id: User UUID
            device_id: Device UUID
            
        Returns:
            Device DTO
            
        Raises:
            NotFoundError: If device not found
            ForbiddenError: If user doesn't own the device
        """
        device = await self.device_repo.get_by_id(device_id)
        
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        if device.user_id != user_id:
            raise ForbiddenError("You do not have access to this device")
        
        return self.mapper.to_dto(device)
    
    async def create_device(
        self,
        user_id: str,
        data: DeviceCreateDTO
    ) -> DeviceResponseDTO:
        """
        Create a new device.
        
        Args:
            user_id: User UUID
            data: Device creation data
            
        Returns:
            Created device DTO
            
        Raises:
            DuplicateError: If MAC address or serial number already exists
            ValidationError: If data is invalid
        """
        # Validate MAC address
        if not validate_mac_address(data.mac_address):
            raise ValidationError("Invalid MAC address format")
        
        # Validate serial number
        if not validate_serial_number(data.serial_number):
            raise ValidationError("Invalid serial number format")
        
        # Normalize MAC address
        mac_address = normalize_mac_address(data.mac_address)
        
        # Check for existing MAC address
        existing_mac = await self.device_repo.get_by_mac_address(mac_address)
        if existing_mac:
            raise DuplicateError("Device with this MAC address already exists")
        
        # Check for existing serial number
        existing_serial = await self.device_repo.get_by_serial_number(data.serial_number.upper())
        if existing_serial:
            raise DuplicateError("Device with this serial number already exists")
        
        # Create device
        device = Device(
            user_id=user_id,
            device_name=data.device_name,
            device_type=data.device_type,
            mac_address=mac_address,
            serial_number=data.serial_number.upper(),
            location=data.location,
            firmware_version=data.firmware_version,
            battery_level=100,
            supplement_level=100,
            is_connected=False,
            is_active=True,
            total_doses_dispensed=0
        )
        
        try:
            device = await self.device_repo.create(device)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise DuplicateError("Device with this MAC address or serial number already exists")
        
        return self.mapper.to_dto(device)
    
    async def update_device(
        self,
        user_id: str,
        device_id: str,
        data: DeviceUpdateDTO
    ) -> DeviceResponseDTO:
        """
        Update device information.
        
        Args:
            user_id: User UUID
            device_id: Device UUID
            data: Device update data
            
        Returns:
            Updated device DTO
            
        Raises:
            NotFoundError: If device not found
            ForbiddenError: If user doesn't own the device
            ValidationError: If data is invalid
        """
        device = await self.device_repo.get_by_id(device_id)
        
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        if device.user_id != user_id:
            raise ForbiddenError("You do not have access to this device")
        
        # Update fields if provided
        if data.device_name is not None:
            device.device_name = data.device_name
        
        if data.location is not None:
            device.location = data.location
        
        if data.battery_level is not None:
            if not validate_battery_level(data.battery_level):
                raise ValidationError("Battery level must be between 0 and 100")
            device.battery_level = data.battery_level
        
        if data.supplement_level is not None:
            if not validate_supplement_level(data.supplement_level):
                raise ValidationError("Supplement level must be between 0 and 100")
            device.supplement_level = data.supplement_level
        
        if data.is_connected is not None:
            device.is_connected = data.is_connected
            if data.is_connected:
                device.last_sync = datetime.utcnow()
        
        if data.firmware_version is not None:
            device.firmware_version = data.firmware_version
        
        if data.is_active is not None:
            device.is_active = data.is_active
        
        device = await self.device_repo.update(device)
        await self.session.commit()
        
        return self.mapper.to_dto(device)
    
    async def delete_device(self, user_id: str, device_id: str) -> bool:
        """
        Delete (deactivate) a device.
        
        Args:
            user_id: User UUID
            device_id: Device UUID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If device not found
            ForbiddenError: If user doesn't own the device
        """
        device = await self.device_repo.get_by_id(device_id)
        
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        if device.user_id != user_id:
            raise ForbiddenError("You do not have access to this device")
        
        result = await self.device_repo.delete(device_id)
        await self.session.commit()
        
        return result
    
    async def update_device_status(
        self,
        device_id: str,
        battery_level: int,
        supplement_level: int,
        is_connected: bool,
        firmware_version: str
    ) -> DeviceResponseDTO:
        """
        Update device status (called by IoT device).
        
        Args:
            device_id: Device UUID
            battery_level: Battery level (0-100)
            supplement_level: Supplement level (0-100)
            is_connected: Connection status
            firmware_version: Firmware version
            
        Returns:
            Updated device DTO
            
        Raises:
            NotFoundError: If device not found
            ValidationError: If data is invalid
        """
        device = await self.device_repo.get_by_id(device_id)
        
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        # Validate levels
        if not validate_battery_level(battery_level):
            raise ValidationError("Battery level must be between 0 and 100")
        
        if not validate_supplement_level(supplement_level):
            raise ValidationError("Supplement level must be between 0 and 100")
        
        # Update device
        device.battery_level = battery_level
        device.supplement_level = supplement_level
        device.is_connected = is_connected
        device.firmware_version = firmware_version
        device.last_sync = datetime.utcnow()
        
        device = await self.device_repo.update(device)
        await self.session.commit()
        
        return self.mapper.to_dto(device)
    
    async def get_device_history(
        self,
        user_id: str,
        device_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """
        Get device activity history.
        
        Args:
            user_id: User UUID
            device_id: Device UUID
            start_date: Start date for history
            end_date: End date for history
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            Dictionary with history data
            
        Raises:
            NotFoundError: If device not found
            ForbiddenError: If user doesn't own the device
        """
        device = await self.device_repo.get_by_id(device_id)
        
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        if device.user_id != user_id:
            raise ForbiddenError("You do not have access to this device")
        
        # Get activity logs
        activities = await self.activity_repo.get_by_date_range(
            device_id=device_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        from datalayer.mapper.device_mapper import ActivityLogMapper
        activity_mapper = ActivityLogMapper()
        
        return {
            "device_id": device_id,
            "total_records": len(activities),
            "limit": limit,
            "offset": offset,
            "activities": activity_mapper.to_dto_list(activities)
        }
    
    async def bulk_update_devices(
        self,
        user_id: str,
        updates: DeviceBulkUpdateDTO
    ) -> List[DeviceResponseDTO]:
        """
        Bulk update multiple devices.
        
        Args:
            user_id: User UUID
            updates: Bulk update data
            
        Returns:
            List of updated device DTOs
            
        Raises:
            ValidationError: If any device ID is invalid
            ForbiddenError: If user doesn't own any device
        """
        updated_devices = []
        
        for device_id in updates.device_ids:
            try:
                device_dto = await self.update_device(user_id, device_id, updates.updates)
                updated_devices.append(device_dto)
            except (NotFoundError, ForbiddenError):
                # Skip devices that don't exist or user doesn't own
                continue
        
        return updated_devices
