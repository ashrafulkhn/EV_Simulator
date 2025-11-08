"""
Test script to verify EV Simulator installation and basic functionality
"""

import sys
import importlib

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import dearpygui.dearpygui as dpg
        print("✓ Dear PyGui imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Dear PyGui: {e}")
        return False
    
    try:
        import websockets
        print("✓ WebSockets imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import WebSockets: {e}")
        return False
    
    try:
        import asyncio
        print("✓ Asyncio imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Asyncio: {e}")
        return False
    
    return True

def test_project_modules():
    """Test if project modules can be imported"""
    print("\nTesting project modules...")
    
    try:
        from config import COLORS, DEFAULT_FORM_VALUES
        print("✓ Config module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import config: {e}")
        return False
    
    try:
        from websocket_handler import WebSocketHandler
        print("✓ WebSocket handler imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import websocket_handler: {e}")
        return False
    
    try:
        from message_handler import MessageHandler
        print("✓ Message handler imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import message_handler: {e}")
        return False
    
    try:
        from ui_components import UIConnectionScreen, UIMainScreen
        print("✓ UI components imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import ui_components: {e}")
        return False
    
    return True

def test_message_creation():
    """Test message creation functionality"""
    print("\nTesting message creation...")
    
    try:
        from message_handler import MessageHandler
        handler = MessageHandler()
        
        # Test basic message creation
        msg1 = handler.create_ev_connection_state("connected")
        assert msg1["kind"] == "evConnectionState"
        print("✓ EV connection state message created")
        
        # Test vehicle info sequence
        form_data = {"evMaxCurrentAmperes": 217.8, "evMaxVoltageVolts": 450.0}
        sequence = handler.get_vehicle_info_sequence(form_data)
        assert len(sequence) == 5
        print("✓ Vehicle info sequence created (5 messages)")
        
        # Test cable check message
        msg2 = handler.create_cable_check(450.0)
        assert msg2["kind"] == "cableCheck"
        print("✓ Cable check message created")
        
        return True
        
    except Exception as e:
        print(f"✗ Message creation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("EV Simulator - Installation Test")
    print("=" * 40)
    
    all_passed = True
    
    # Test external dependencies
    if not test_imports():
        all_passed = False
    
    # Test project modules
    if not test_project_modules():
        all_passed = False
    
    # Test message creation
    if not test_message_creation():
        all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("✓ All tests passed! EV Simulator is ready to run.")
        print("\nTo start the application, run:")
        print("  python main.py")
    else:
        print("✗ Some tests failed. Please check the error messages above.")
        print("\nTo install missing dependencies, run:")
        print("  pip install -r requirements.txt")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
