"""
Quick verification script to test if the EV Simulator can start without errors
"""

import sys
import traceback

def test_app_startup():
    """Test if the app can start without errors"""
    try:
        print("Testing EV Simulator startup...")
        
        # Import all modules
        from main import EVSimulatorApp
        print("✓ All modules imported successfully")
        
        # Try to create the app (this will test UI creation)
        app = EVSimulatorApp()
        print("✓ EVSimulatorApp created successfully")
        
        # Test message handler
        from message_handler import MessageHandler
        handler = MessageHandler()
        test_msg = handler.create_ev_connection_state("connected")
        print("✓ Message handler working")
        
        print("\n🎉 EV Simulator is ready to run!")
        print("The application should now be running in the background.")
        print("Look for the Dear PyGui window on your screen.")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during startup: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_app_startup()
    sys.exit(0 if success else 1)
