"""
UI Components and screens for EV Simulator using Tkinter

This module exposes two classes with the same public methods used by
the rest of the application: UIConnectionScreen and UIMainScreen.
They provide a simple Tkinter layout and use callbacks to communicate
user actions back to the app.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable, Optional
from config import DEFAULT_FORM_VALUES


class UIConnectionScreen:
    """Connection screen UI component for Tkinter"""

    def __init__(self, parent: tk.Widget, connect_callback: Callable[[str], None]):
        self.parent = parent
        self.connect_callback = connect_callback
        self.frame = ttk.LabelFrame(parent, text="WebSocket Connection")
        self._build()

    def _build(self):
        lbl = ttk.Label(self.frame, text="WebSocket URI:")
        lbl.grid(row=0, column=0, sticky="w", padx=6, pady=6)

        self.uri_var = tk.StringVar(value="ws://192.168.3.110:8765/GUN4")
        self.uri_entry = ttk.Entry(self.frame, textvariable=self.uri_var, width=45)
        self.uri_entry.grid(row=0, column=1, sticky="we", padx=6, pady=6)

        self.connect_btn = ttk.Button(self.frame, text="Connect", command=self._on_connect_clicked)
        self.connect_btn.grid(row=1, column=0, padx=6, pady=6)

        self.status_var = tk.StringVar(value="Not Connected")
        self.status_label = ttk.Label(self.frame, textvariable=self.status_var)
        self.status_label.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        # Make column 1 expand
        self.frame.columnconfigure(1, weight=1)

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def _on_connect_clicked(self):
        uri = self.uri_var.get().strip()
        if uri:
            self.connect_callback(uri)

    def update_connection_status(self, connected: bool, message: str = ""):
        if connected:
            self.status_var.set(f"Connected: {message}")
            self.connect_btn.configure(text="Disconnect")
        else:
            self.status_var.set(f"Disconnected: {message}")
            self.connect_btn.configure(text="Connect")


class UIMainScreen:
    """Main control screen UI component for Tkinter"""

    def __init__(self, parent: tk.Widget, button_callbacks: Dict[str, Callable], log_callback: Callable[[str], None]):
        self.parent = parent
        self.button_callbacks = button_callbacks
        self.log_callback = log_callback
        self.form_data = DEFAULT_FORM_VALUES.copy()
        self.auto_scroll = True

        self.frame = ttk.Frame(parent)
        self._build()

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def _build(self):
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=6)

        # Controls tab
        self.controls_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.controls_tab, text="Controls")

        # Params tab
        self.params_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.params_tab, text="EV Parameters")

        # Controls layout
        btn_frame = ttk.Frame(self.controls_tab)
        btn_frame.pack(fill="x", padx=6, pady=6)

        self.gun_btn = ttk.Button(btn_frame, text="Connect Gun", command=self.button_callbacks.get('gun_connect'))
        self.gun_btn.grid(row=0, column=0, padx=4, pady=4)

        self.transfer_btn = ttk.Button(btn_frame, text="Transfer Allowed", command=self.button_callbacks.get('transfer_allowed'))
        self.transfer_btn.grid(row=0, column=1, padx=4, pady=4)

        self.send_vehicle_info_btn = ttk.Button(btn_frame, text="Send Vehicle Info (Step 1/5)", command=self.button_callbacks.get('send_vehicle_info'))
        self.send_vehicle_info_btn.grid(row=1, column=0, columnspan=2, padx=4, pady=8, sticky="w")

        self.cable_check_btn = ttk.Button(btn_frame, text="Cable Check", command=self.button_callbacks.get('cable_check'))
        self.cable_check_btn.grid(row=2, column=0, padx=4, pady=4)

        self.start_precharge_btn = ttk.Button(btn_frame, text="Start Precharge", command=self.button_callbacks.get('start_precharge'))
        self.start_precharge_btn.grid(row=2, column=1, padx=4, pady=4)

        self.charge_btn = ttk.Button(btn_frame, text="Charge", command=self.button_callbacks.get('charge'))
        self.charge_btn.grid(row=3, column=0, padx=4, pady=4)

        self.stop_charge_btn = ttk.Button(btn_frame, text="Stop Charging", command=self.button_callbacks.get('stop_charging'))
        self.stop_charge_btn.grid(row=3, column=1, padx=4, pady=4)

        self.reset_btn = ttk.Button(btn_frame, text="Reset", command=self.button_callbacks.get('reset'))
        self.reset_btn.grid(row=4, column=0, padx=4, pady=8)

        # Log area
        log_frame = ttk.LabelFrame(self.controls_tab, text="Message Log")
        log_frame.pack(fill="both", expand=True, padx=6, pady=6)

        toolbar = ttk.Frame(log_frame)
        toolbar.pack(fill="x", padx=4, pady=4)
        clear_btn = ttk.Button(toolbar, text="Clear Log", command=self._clear_log)
        clear_btn.pack(side="left")

        self.auto_scroll_var = tk.StringVar(value="Auto Scroll: ON")
        auto_btn = ttk.Button(toolbar, textvariable=self.auto_scroll_var, command=self._toggle_auto_scroll)
        auto_btn.pack(side="left", padx=6)

        self.log_text = tk.Text(log_frame, height=12, wrap="none")
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)

        # Params tab inputs
        params_frame = ttk.Frame(self.params_tab)
        params_frame.pack(fill="both", expand=True, padx=6, pady=6)

        self.param_vars: Dict[str, tk.DoubleVar] = {}
        form_inputs = [
            ("evMaxCurrentAmperes", "EV Max Current (Amperes)", 217.8),
            ("evMaxVoltageVolts", "EV Max Voltage (Volts)", 450.0),
            ("evMinCurrentAmperes", "EV Min Current (Amperes)", 0.0),
            ("evMinPowerWatts", "EV Min Power (Watts)", 0.0),
            ("evMinVoltageVolts", "EV Min Voltage (Volts)", 0.0),
            ("chargingProfileMaxPowerLimitWatts", "Charging Profile Max Power (Watts)", 120000.0),
            ("cableCheckVoltage", "Cable Check Voltage (Volts)", 450.0),
            ("batteryStateOfCharge", "Battery State of Charge (%)", 10.0),
            ("targetCurrent", "Target Current (Amperes)", 20),
            ("targetVoltage", "Target Voltage (Volts)", 500)
        ]

        for i, (key, label, default) in enumerate(form_inputs):
            lbl = ttk.Label(params_frame, text=label)
            lbl.grid(row=i, column=0, sticky="w", padx=4, pady=4)
            var = tk.DoubleVar(value=default)
            ent = ttk.Entry(params_frame, textvariable=var)
            ent.grid(row=i, column=1, sticky="we", padx=4, pady=4)
            self.param_vars[key] = var

        params_frame.columnconfigure(1, weight=1)

        update_btn = ttk.Button(params_frame, text="Update Parameters", command=self._on_update_params)
        update_btn.grid(row=len(form_inputs), column=0, columnspan=2, pady=8)

    def _clear_log(self):
        self.log_text.delete("1.0", tk.END)

    def _toggle_auto_scroll(self):
        self.auto_scroll = not self.auto_scroll
        self.auto_scroll_var.set("Auto Scroll: ON" if self.auto_scroll else "Auto Scroll: OFF")

    def _on_update_params(self):
        # Cache values from fields
        _ = self.get_form_data()
        if self.log_callback:
            try:
                self.log_callback(">>>>> Parameters updated")
            except Exception:
                pass

    def get_form_data(self) -> Dict[str, float]:
        for key, var in self.param_vars.items():
            try:
                self.form_data[key] = float(var.get())
            except Exception:
                # Keep previous/default
                pass
        return self.form_data

    def add_log_message(self, message: str):
        self.log_text.insert(tk.END, message + "\n")
        if self.auto_scroll:
            self.log_text.see(tk.END)

    def update_gun_button(self, connected: bool):
        self.gun_btn.configure(text="Disconnect Gun" if connected else "Connect Gun")

    def update_vehicle_info_button(self, step: int, total: int = 5):
        self.send_vehicle_info_btn.configure(text=f"Send Vehicle Info (Step {step}/{total})")

