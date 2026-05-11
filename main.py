"""
Main EV Simulator Application using Tkinter

This replaces the DearPyGui UI with a Tkinter implementation while
keeping the existing asyncio-based WebSocket handler and message
creation logic. WebSocket events are marshalled to the Tk main thread
via a thread-safe queue.
"""

import asyncio
import json
import threading
import logging
import queue
import tkinter as tk
from typing import Optional

from config import APP_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT
from websocket_handler import WebSocketHandler
from message_handler import MessageHandler
from ui_components import UIConnectionScreen, UIMainScreen
from auto_sequence import AutoSequence
from theme import apply_theme

class EVSimulatorApp:
    """Main EV Simulator Application (Tkinter)"""

    def __init__(self):
        self.ws_handler = WebSocketHandler()
        self.message_handler = MessageHandler()

        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        apply_theme(self.root)

        # Thread-safe queue for events from asyncio thread -> Tkinter
        self._event_queue: "queue.Queue[tuple]" = queue.Queue()

        # UI
        self.connection_screen = UIConnectionScreen(self.root, self._on_connect_clicked)
        self.connection_screen.grid(row=0, column=0, sticky="nwe", padx=16, pady=(14, 6))

        self.main_screen = UIMainScreen(self.root, button_callbacks=self._get_button_callbacks(), log_callback=self._add_log_message)
        self.main_screen.grid(row=1, column=0, sticky="nsew", padx=16, pady=(6, 14))

        # Configure root resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # App state
        self.gun_connected = False
        self.vehicle_info_step = 0

        # Asyncio loop in background thread
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Wire WebSocket callbacks to place events on queue
        self.ws_handler.set_message_callback(lambda m: self._event_queue.put(("message", m)))
        self.ws_handler.set_connection_callback(lambda status: self._event_queue.put(("connection", status)))

        # Auto sequence: callbacks marshal to Tk via the event queue.
        self.auto_sequence = AutoSequence(
            ws_handler=self.ws_handler,
            message_handler=self.message_handler,
            get_form_data=lambda: self.main_screen.form_data,
            status_cb=lambda s: self._event_queue.put(("auto_status", s)),
            log_cb=lambda m: self._event_queue.put(("log", m)),
        )
        self.main_screen.set_auto_callbacks(self._on_start_auto, self._on_stop_auto)

    def _get_button_callbacks(self):
        return {
            'gun_connect': self._on_gun_connect,
            'transfer_allowed': self._on_transfer_allowed,
            'send_vehicle_info': self._on_send_vehicle_info,
            'cable_check': self._on_cable_check,
            'start_precharge': self._on_start_precharge,
            'charge': self._on_charge,
            'stop_charging': self._on_stop_charging,
            'reset': self._on_reset
        }

    def _on_connect_clicked(self, uri: str):
        """Called when user clicks Connect/Disconnect in UI."""
        if self.ws_handler.is_connected():
            if self.loop:
                asyncio.run_coroutine_threadsafe(self.ws_handler.disconnect(), self.loop)
        else:
            if self.loop:
                asyncio.run_coroutine_threadsafe(self.ws_handler.connect(uri), self.loop)

    def _on_gun_connect(self):
        if self.gun_connected:
            message = self.message_handler.create_ev_connection_state("disconnected")
            self.gun_connected = False
        else:
            message = self.message_handler.create_ev_connection_state("connected")
            self.gun_connected = True

        self._send_message(message)
        self.main_screen.update_gun_button(self.gun_connected)

    def _on_transfer_allowed(self):
        message = self.message_handler.create_ev_connection_state("energyTransferAllowed")
        self._send_message(message)

    def _on_send_vehicle_info(self):
        form_data = self.main_screen.get_form_data()
        message = self.message_handler.get_next_vehicle_info_message(form_data)

        # update step
        self.vehicle_info_step = (self.vehicle_info_step + 1) % 5
        if self.vehicle_info_step == 0:
            self.vehicle_info_step = 5
        self.main_screen.update_vehicle_info_button(self.vehicle_info_step)

        self._send_message(message)

    def _on_cable_check(self):
        form_data = self.main_screen.get_form_data()
        voltage = form_data.get('cableCheckVoltage', 450.0)
        message = self.message_handler.create_cable_check(voltage)
        self._send_message(message)

    def _on_start_precharge(self):
        form_data = self.main_screen.get_form_data()
        message = self.message_handler.create_target_values({
            "batteryStateOfCharge": form_data.get('batteryStateOfCharge', 45),
            "chargingState": "preCharge",
            "targetCurrent": form_data.get('prechargeTargetCurrent', 10),
            "targetVoltage": form_data.get('prechargeTargetVoltage', 400)
        })
        self._send_message(message)

    def _on_charge(self):
        form_data = self.main_screen.get_form_data()
        message = self.message_handler.create_target_values({
            "batteryStateOfCharge": form_data.get('batteryStateOfCharge', 78.0),
            "chargingState": "charging",
            "targetCurrent": form_data.get('chargeTargetCurrent', 60),
            "targetVoltage": form_data.get('chargeTargetVoltage', 500)
        })
        self._send_message(message)

    def _on_stop_charging(self):
        message = self.message_handler.create_stop_charging()
        self._send_message(message)

    def _on_reset(self):
        message = self.message_handler.create_reset()
        self._send_message(message)

    def _on_start_auto(self):
        if not self.ws_handler.is_connected():
            self._add_log_message("ERROR: Connect to the WebSocket before starting Auto")
            return
        if self.auto_sequence.is_running():
            return
        # Refresh form data from Tk vars on the main thread so the sequence
        # reads from a thread-safe snapshot.
        self.main_screen.get_form_data()
        cfg = self.main_screen.get_auto_config()
        if self.loop:
            self.auto_sequence.start(self.loop, cfg)
            self.main_screen.set_auto_running(True)

    def _on_stop_auto(self):
        if self.loop and self.auto_sequence.is_running():
            self.auto_sequence.stop(self.loop)

    def _send_message(self, message: dict):
        if self.ws_handler.is_connected():
            if self.loop:
                asyncio.run_coroutine_threadsafe(self.ws_handler.send_message(message), self.loop)
            formatted_message = self.message_handler.format_message_for_log(message, "sent")
            self._add_log_message(formatted_message)
        else:
            self._add_log_message("ERROR: Not connected to WebSocket")

    def _dispatch_incoming(self, raw: str):
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return
        if not isinstance(parsed, dict):
            return
        if parsed.get("type") == "info" and parsed.get("kind") == "status":
            self.auto_sequence.on_status(parsed.get("payload") or {})

    def _add_log_message(self, message: str):
        # Ensure UI update happens in Tk main thread
        try:
            self.main_screen.add_log_message(message)
        except Exception:
            pass

    def _process_event_queue(self):
        """Process events placed by the asyncio thread."""
        try:
            while True:
                event, payload = self._event_queue.get_nowait()
                if event == "message":
                    self._add_log_message(f"<<<<< {payload}")
                    self._dispatch_incoming(payload)
                elif event == "connection":
                    connected = bool(payload)
                    self.connection_screen.update_connection_status(connected, "")
                    if not connected:
                        self._add_log_message("INFO: Disconnected")
                elif event == "log":
                    self._add_log_message(payload)
                elif event == "auto_status":
                    self.main_screen.update_auto_status(payload)
                    stage = payload.get("stage")
                    if stage in ("Idle", "FAILED"):
                        self.main_screen.set_auto_running(False)
                else:
                    self.logger.debug("Unknown event in queue: %s", event)
        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self._process_event_queue)

    def _start_async_loop(self):
        def run_async():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        async_thread = threading.Thread(target=run_async, daemon=True)
        async_thread.start()

    def run(self):
        # Start asyncio loop thread
        self._start_async_loop()

        # Start processing events from websocket thread
        self.root.after(100, self._process_event_queue)

        # Run Tk main loop
        try:
            self.root.mainloop()
        finally:
            # Ensure asyncio loop is stopped when GUI closes
            if self.loop:
                self.loop.call_soon_threadsafe(self.loop.stop)


def main():
    app = EVSimulatorApp()
    app.run()


if __name__ == "__main__":
    main()
