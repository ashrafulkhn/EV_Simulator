"""
Test script to verify text display in Dear PyGui
"""

import dearpygui.dearpygui as dpg

def test_text_display():
    """Test basic text display functionality"""
    dpg.create_context()
    dpg.create_viewport(title="Text Display Test", width=400, height=300)
    
    with dpg.window(label="Test Window", width=400, height=300):
        dpg.add_text(default_value="This is a test text")
        dpg.add_text(default_value="WebSocket Connection", color=[0.1, 0.1, 0.1, 1.0])
        dpg.add_separator()
        dpg.add_text(default_value="WebSocket URI:")
        dpg.add_input_text(default_value="ws://localhost:8080", width=300)
        dpg.add_spacer()
        dpg.add_button(label="Test Button", width=100)
    
    dpg.setup_dearpygui()
    dpg.show_viewport()
    
    print("Text display test window should be visible.")
    print("Close the window to continue...")
    
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()
    
    dpg.destroy_context()
    print("Text display test completed!")

if __name__ == "__main__":
    test_text_display()
