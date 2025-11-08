"""
Message templates and handling for EV Simulator
"""

import json
from typing import Dict, Any, List
from config import VEHICLE_ID, DEFAULT_SEQUENCE_NUMBER, DEFAULT_FORM_VALUES

class MessageHandler:
    """Handles creation and formatting of JSON messages for EV operations"""
    
    def __init__(self):
        self.sequence_number = DEFAULT_SEQUENCE_NUMBER
        self.vehicle_info_step = 0  # For sequential vehicle info messages
        
    def increment_sequence(self):
        """Increment sequence number for next message"""
        self.sequence_number += 1
        return self.sequence_number
    
    def reset_vehicle_info_step(self):
        """Reset vehicle info step counter"""
        self.vehicle_info_step = 0
    
    def create_ev_connection_state(self, state: str, include_vehicle_id: bool = False) -> Dict[str, Any]:
        """Create EV connection state message"""
        payload = {"evConnectionState": state}
        if include_vehicle_id:
            payload["vehicleId"] = VEHICLE_ID
            
        return {
            "kind": "evConnectionState",
            "payload": payload,
            "type": "info"
        }
    
    def create_charging_session(self, data: Dict[str, float]) -> Dict[str, Any]:
        """Create charging session message"""
        return {
            "kind": "chargingSession",
            "payload": data,
            "type": "info"
        }
    
    def create_contactors_status(self, status: str) -> Dict[str, Any]:
        """Create contactors status message"""
        return {
            "kind": "contactorsStatus",
            "payload": {"contactorsStatus": status},
            "sequenceNumber": self.increment_sequence(),
            "type": "request"
        }
    
    def create_cable_check(self, voltage: float) -> Dict[str, Any]:
        """Create cable check message"""
        return {
            "kind": "cableCheck",
            "payload": {"voltage": voltage},
            "sequenceNumber": self.increment_sequence(),
            "type": "request"
        }
    
    def create_target_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create target values message"""
        return {
            "kind": "targetValues",
            "payload": data,
            "sequenceNumber": self.increment_sequence(),
            "type": "request"
        }
    
    def create_stop_charging(self) -> Dict[str, Any]:
        """Create stop charging message"""
        return {
            "kind": "stopCharging",
            "payload": {},
            "sequenceNumber": 0,
            "type": "request"
        }
    
    def create_reset(self) -> Dict[str, Any]:
        """Create reset message"""
        return {
            "kind": "reset",
            "payload": {},
            "sequenceNumber": self.increment_sequence(),
            "type": "request"
        }
    
    def get_vehicle_info_sequence(self, form_data: Dict[str, float]) -> List[Dict[str, Any]]:
        """Get the 5-message vehicle info sequence"""
        return [
            # Step 1: Vehicle connection with ID
            self.create_ev_connection_state("connected", include_vehicle_id=True),
            
            # Step 2: EV charging session parameters
            self.create_charging_session({
                "evMaxCurrentAmperes": form_data.get('evMaxCurrentAmperes', DEFAULT_FORM_VALUES['evMaxCurrentAmperes']),
                "evMaxVoltageVolts": form_data.get('evMaxVoltageVolts', DEFAULT_FORM_VALUES['evMaxVoltageVolts']),
                "evMinCurrentAmperes": form_data.get('evMinCurrentAmperes', DEFAULT_FORM_VALUES['evMinCurrentAmperes']),
                "evMinPowerWatts": form_data.get('evMinPowerWatts', DEFAULT_FORM_VALUES['evMinPowerWatts']),
                "evMinVoltageVolts": form_data.get('evMinVoltageVolts', DEFAULT_FORM_VALUES['evMinVoltageVolts'])
            }),
            
            # Step 3: Charging profile power limit
            self.create_charging_session({
                "chargingProfileMaxPowerLimitWatts": form_data.get('chargingProfileMaxPowerLimitWatts', DEFAULT_FORM_VALUES['chargingProfileMaxPowerLimitWatts'])
            }),
            
            # Step 4: Charge mode
            self.create_charging_session({
                "chargeMode": "scheduled"
            }),
            
            # Step 5: Contactors status
            self.create_contactors_status("closed")
        ]
    
    def get_next_vehicle_info_message(self, form_data: Dict[str, float]) -> Dict[str, Any]:
        """Get next message in vehicle info sequence"""
        sequence = self.get_vehicle_info_sequence(form_data)
        
        if self.vehicle_info_step < len(sequence):
            message = sequence[self.vehicle_info_step]
            self.vehicle_info_step += 1
            return message
        else:
            # Reset to beginning of sequence
            self.vehicle_info_step = 0
            return sequence[0]
    
    def format_message_for_log(self, message: Dict[str, Any], direction: str) -> str:
        """Format message for display in log"""
        message_str = json.dumps(message, indent=2)
        if direction == "sent":
            return f">>>>> {message_str}"
        else:
            return f"<<<<< {message_str}"
