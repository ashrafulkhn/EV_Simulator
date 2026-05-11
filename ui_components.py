"""
UI Components and screens for EV Simulator using Tkinter.

Public API (consumed by main.py):
  UIConnectionScreen(parent, connect_callback)
    .grid(...) / .pack(...)
    .update_connection_status(connected, message)

  UIMainScreen(parent, button_callbacks, log_callback)
    .grid(...) / .pack(...)
    .get_form_data() -> dict
    .add_log_message(str)
    .update_gun_button(bool)
    .update_vehicle_info_button(step, total=5)
    .set_auto_callbacks(start_cb, stop_cb)
    .get_auto_config() -> dict
    .set_auto_running(bool)
    .update_auto_status(dict)
    .form_data (attribute — last-cached form dict)
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable, Optional

from config import DEFAULT_FORM_VALUES, AUTO_DEFAULTS, STAGE_COLORS, DEFAULT_WS_URI
from theme import PALETTE, FONT_MONO, FONT_HEADING, FONT_TITLE, FONT_BODY


# ---------------------------------------------------------------------------
# Connection screen (top bar)
# ---------------------------------------------------------------------------

class UIConnectionScreen:
    def __init__(self, parent: tk.Widget, connect_callback: Callable[[str], None]):
        self.parent = parent
        self.connect_callback = connect_callback
        self.frame = ttk.Labelframe(parent, text="WebSocket Connection", style="Card.TLabelframe")
        self._build()

    def _build(self):
        bar = ttk.Frame(self.frame, style="Card.TFrame")
        bar.grid(row=0, column=0, sticky="we")
        bar.columnconfigure(1, weight=1)

        lbl = ttk.Label(bar, text="URI", style="CardLabel.TLabel")
        lbl.grid(row=0, column=0, padx=(0, 10), pady=4, sticky="w")

        # self.uri_var = tk.StringVar(value="ws://192.168.3.110:8765/GUN4")
        self.uri_var = tk.StringVar(value=DEFAULT_WS_URI)
        self.uri_entry = ttk.Entry(bar, textvariable=self.uri_var)
        self.uri_entry.grid(row=0, column=1, sticky="we", padx=(0, 12), pady=4)

        self.connect_btn = ttk.Button(bar, text="Connect", style="Primary.TButton",
                                      command=self._on_connect_clicked)
        self.connect_btn.grid(row=0, column=2, padx=(0, 12), pady=4)

        # Status indicator (dot + text)
        status_box = ttk.Frame(bar, style="Card.TFrame")
        status_box.grid(row=0, column=3, sticky="e", pady=4)

        self.status_dot = tk.Canvas(status_box, width=12, height=12,
                                    bg=PALETTE["surface"], highlightthickness=0)
        self.status_dot.grid(row=0, column=0, padx=(0, 8))
        self._dot = self.status_dot.create_oval(2, 2, 11, 11,
                                                fill=PALETTE["danger"], outline="")

        self.status_var = tk.StringVar(value="Not Connected")
        self.status_label = ttk.Label(status_box, textvariable=self.status_var,
                                      style="CardLabel.TLabel")
        self.status_label.grid(row=0, column=1, sticky="e")

        self.frame.columnconfigure(0, weight=1)

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
            self.status_var.set(f"Connected  {message}".strip())
            self.status_dot.itemconfigure(self._dot, fill=PALETTE["success"])
            self.connect_btn.configure(text="Disconnect", style="Danger.TButton")
        else:
            self.status_var.set(f"Disconnected  {message}".strip())
            self.status_dot.itemconfigure(self._dot, fill=PALETTE["danger"])
            self.connect_btn.configure(text="Connect", style="Primary.TButton")


# ---------------------------------------------------------------------------
# Main screen
# ---------------------------------------------------------------------------

class UIMainScreen:
    def __init__(self, parent: tk.Widget, button_callbacks: Dict[str, Callable],
                 log_callback: Callable[[str], None]):
        self.parent = parent
        self.button_callbacks = button_callbacks
        self.log_callback = log_callback
        self.form_data = DEFAULT_FORM_VALUES.copy()
        self.auto_scroll = True

        self.param_vars: Dict[str, tk.Variable] = {}
        self.auto_config_vars: Dict[str, tk.Variable] = {}
        self.auto_start_callback: Optional[Callable[[], None]] = None
        self.auto_stop_callback: Optional[Callable[[], None]] = None
        self._auto_running = False

        self.frame = ttk.Frame(parent)
        self._build()

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build(self):
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill="both", expand=True)

        self.controls_tab   = ttk.Frame(self.notebook)
        self.params_tab     = ttk.Frame(self.notebook)
        self.automatic_tab  = ttk.Frame(self.notebook)
        self.config_tab     = ttk.Frame(self.notebook)

        self.notebook.add(self.controls_tab,  text="  Controls  ")
        self.notebook.add(self.params_tab,    text="  EV Parameters  ")
        self.notebook.add(self.automatic_tab, text="  Automatic  ")
        self.notebook.add(self.config_tab,    text="  Configuration  ")

        self._build_controls_tab()
        self._build_params_tab()
        self._build_automatic_tab()
        self._build_config_tab()

    # ------------------------------------------------------------------
    # Controls tab
    # ------------------------------------------------------------------
    def _build_controls_tab(self):
        page = ttk.Frame(self.controls_tab)
        page.pack(fill="both", expand=True, padx=18, pady=18)
        page.columnconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)

        # ---- Top row: action cards ----
        action_row = ttk.Frame(page)
        action_row.grid(row=0, column=0, sticky="we")
        for c in range(4):
            action_row.columnconfigure(c, weight=1, uniform="cards")

        # Card: Connection
        c1 = ttk.Labelframe(action_row, text="Connection", style="Card.TLabelframe")
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        c1.columnconfigure(0, weight=1)
        self.gun_btn = ttk.Button(c1, text="Connect Gun", style="Primary.TButton",
                                  command=self.button_callbacks.get('gun_connect'))
        self.gun_btn.grid(row=0, column=0, sticky="we", pady=(0, 6))
        self.transfer_btn = ttk.Button(c1, text="Transfer Allowed", style="Secondary.TButton",
                                       command=self.button_callbacks.get('transfer_allowed'))
        self.transfer_btn.grid(row=1, column=0, sticky="we")

        # Card: Vehicle Info
        c2 = ttk.Labelframe(action_row, text="Vehicle Info", style="Card.TLabelframe")
        c2.grid(row=0, column=1, sticky="nsew", padx=8)
        c2.columnconfigure(0, weight=1)
        self.send_vehicle_info_btn = ttk.Button(c2, text="Send Vehicle Info  (Step 1/5)",
                                                style="Accent.TButton",
                                                command=self.button_callbacks.get('send_vehicle_info'))
        self.send_vehicle_info_btn.grid(row=0, column=0, sticky="we")
        ttk.Label(c2, text="Click 5 times to walk through the\nvehicle-info burst.",
                  style="CardLabel.TLabel", justify="left", foreground=PALETTE["text_muted"],
                  font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=(8, 0))

        # Card: Power Flow
        c3 = ttk.Labelframe(action_row, text="Power Flow", style="Card.TLabelframe")
        c3.grid(row=0, column=2, sticky="nsew", padx=8)
        c3.columnconfigure(0, weight=1)
        self.cable_check_btn = ttk.Button(c3, text="Cable Check", style="Primary.TButton",
                                          command=self.button_callbacks.get('cable_check'))
        self.cable_check_btn.grid(row=0, column=0, sticky="we", pady=(0, 6))
        self.start_precharge_btn = ttk.Button(c3, text="Start Precharge", style="Primary.TButton",
                                              command=self.button_callbacks.get('start_precharge'))
        self.start_precharge_btn.grid(row=1, column=0, sticky="we", pady=(0, 6))
        self.charge_btn = ttk.Button(c3, text="Charge", style="Success.TButton",
                                     command=self.button_callbacks.get('charge'))
        self.charge_btn.grid(row=2, column=0, sticky="we")

        # Card: Terminate
        c4 = ttk.Labelframe(action_row, text="Terminate", style="Card.TLabelframe")
        c4.grid(row=0, column=3, sticky="nsew", padx=(8, 0))
        c4.columnconfigure(0, weight=1)
        self.stop_charge_btn = ttk.Button(c4, text="Stop Charging", style="Danger.TButton",
                                          command=self.button_callbacks.get('stop_charging'))
        self.stop_charge_btn.grid(row=0, column=0, sticky="we", pady=(0, 6))
        self.reset_btn = ttk.Button(c4, text="Reset", style="Warning.TButton",
                                    command=self.button_callbacks.get('reset'))
        self.reset_btn.grid(row=1, column=0, sticky="we")

        # ---- Log ----
        log_frame = ttk.Labelframe(page, text="Message Log", style="Card.TLabelframe")
        log_frame.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(log_frame, style="Card.TFrame")
        toolbar.grid(row=0, column=0, sticky="we", pady=(0, 8))
        ttk.Button(toolbar, text="Clear", style="Secondary.TButton",
                   command=self._clear_log).pack(side="left")
        self.auto_scroll_var = tk.StringVar(value="Auto Scroll: ON")
        ttk.Button(toolbar, textvariable=self.auto_scroll_var, style="Secondary.TButton",
                   command=self._toggle_auto_scroll).pack(side="left", padx=(8, 0))

        text_wrap = tk.Frame(log_frame, bg=PALETTE["log_bg"], highlightthickness=0, bd=0)
        text_wrap.grid(row=1, column=0, sticky="nsew")
        text_wrap.columnconfigure(0, weight=1)
        text_wrap.rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            text_wrap, wrap="none", bd=0, relief="flat",
            bg=PALETTE["log_bg"], fg=PALETTE["log_fg"],
            insertbackground=PALETTE["log_fg"],
            selectbackground=PALETTE["primary"], selectforeground="white",
            font=FONT_MONO, padx=10, pady=10, height=12,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(text_wrap, orient="vertical", command=self.log_text.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=vsb.set)
        self.log_text.tag_configure("sent", foreground=PALETTE["log_sent"])
        self.log_text.tag_configure("recv", foreground=PALETTE["log_recv"])
        self.log_text.tag_configure("info", foreground=PALETTE["text_muted"])

    # ------------------------------------------------------------------
    # EV Parameters tab
    # ------------------------------------------------------------------
    def _build_params_tab(self):
        page = ttk.Frame(self.params_tab)
        page.pack(fill="both", expand=True, padx=18, pady=18)
        page.columnconfigure(0, weight=1, uniform="cols")
        page.columnconfigure(1, weight=1, uniform="cols")

        ev_limits = [
            ("evMaxCurrentAmperes", "EV Max Current", "A", 217.8),
            ("evMaxVoltageVolts",   "EV Max Voltage", "V", 450.0),
            ("evMinCurrentAmperes", "EV Min Current", "A", 0.0),
            ("evMinVoltageVolts",   "EV Min Voltage", "V", 0.0),
            ("evMinPowerWatts",     "EV Min Power",   "W", 0.0),
        ]
        profile = [
            ("chargingProfileMaxPowerLimitWatts", "Charging Profile Max Power", "W", 120000.0),
            ("cableCheckVoltage",                 "Cable Check Voltage",        "V", 450.0),
            ("batteryStateOfCharge",              "Battery State of Charge",    "%", 10.0),
        ]
        precharge_targets = [
            ("prechargeTargetVoltage", "Precharge Voltage", "V", 400.0),
            ("prechargeTargetCurrent", "Precharge Current", "A", 10.0),
        ]
        charge_targets = [
            ("chargeTargetVoltage", "Charge Voltage", "V", 500.0),
            ("chargeTargetCurrent", "Charge Current", "A", 60.0),
        ]

        self._build_param_card(page, "EV Limits",         ev_limits,         row=0, col=0, padx=(0, 8))
        self._build_param_card(page, "Charging Profile",  profile,           row=0, col=1, padx=(8, 0))
        self._build_param_card(page, "Precharge Targets", precharge_targets, row=1, col=0, padx=(0, 8), pady=(14, 0))
        self._build_param_card(page, "Charge Targets",    charge_targets,    row=1, col=1, padx=(8, 0), pady=(14, 0))

        # Apply row (spans both columns)
        action_card = ttk.Labelframe(page, text="Apply", style="Card.TLabelframe")
        action_card.grid(row=2, column=0, columnspan=2, sticky="we", pady=(14, 0))
        action_card.columnconfigure(0, weight=1)
        action_card.columnconfigure(1, weight=0)
        ttk.Label(action_card,
                  text="Updates the cached values used by manual and automatic flows. "
                       "Click after editing any value above.",
                  style="CardLabel.TLabel", foreground=PALETTE["text_muted"],
                  wraplength=520, justify="left").grid(row=0, column=0, sticky="w", padx=(0, 12))
        ttk.Button(action_card, text="Update Parameters", style="Primary.TButton",
                   command=self._on_update_params).grid(row=0, column=1, sticky="e")

    def _build_param_card(self, parent, title, fields, row, col, padx=0, pady=0):
        card = ttk.Labelframe(parent, text=title, style="Card.TLabelframe")
        card.grid(row=row, column=col, sticky="nsew", padx=padx, pady=pady)
        card.columnconfigure(1, weight=1)

        for i, (key, label, unit, default) in enumerate(fields):
            ttk.Label(card, text=label, style="CardLabel.TLabel").grid(
                row=i, column=0, sticky="w", padx=(0, 12), pady=4)
            var = tk.DoubleVar(value=default)
            self.param_vars[key] = var
            ent = ttk.Entry(card, textvariable=var, width=14, justify="right")
            ent.grid(row=i, column=1, sticky="we", pady=4)
            ttk.Label(card, text=unit, style="CardLabel.TLabel",
                      foreground=PALETTE["text_muted"]).grid(
                row=i, column=2, sticky="w", padx=(8, 0), pady=4)

    # ------------------------------------------------------------------
    # Automatic tab
    # ------------------------------------------------------------------
    def _build_automatic_tab(self):
        page = ttk.Frame(self.automatic_tab)
        page.pack(fill="both", expand=True, padx=18, pady=18)
        page.columnconfigure(0, weight=2, uniform="auto")
        page.columnconfigure(1, weight=3, uniform="auto")
        page.rowconfigure(0, weight=1)

        # ---- Left: control card ----
        left = ttk.Labelframe(page, text="Automatic Test", style="Card.TLabelframe")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text="Current Stage", style="CardLabel.TLabel",
                  foreground=PALETTE["text_muted"], font=("Segoe UI", 9)).grid(
            row=0, column=0, sticky="w")

        self.auto_stage_var = tk.StringVar(value="Idle")
        self.auto_stage_label = tk.Label(
            left, textvariable=self.auto_stage_var,
            bg=STAGE_COLORS["Idle"], fg="white",
            font=("Segoe UI", 16, "bold"),
            padx=18, pady=14, anchor="center",
        )
        self.auto_stage_label.grid(row=1, column=0, sticky="we", pady=(4, 14))

        self.auto_btn = ttk.Button(left, text="Start Charging", style="Hero.TButton",
                                   command=self._on_auto_button)
        self.auto_btn.grid(row=2, column=0, sticky="we")

        ttk.Label(left,
                  text="Sends the configured sequence: connect gun → vehicle info → "
                       "transfer allowed → cable check → precharge → charge.",
                  style="CardLabel.TLabel", foreground=PALETTE["text_muted"],
                  wraplength=260, justify="left",
                  font=("Segoe UI", 9)).grid(row=3, column=0, sticky="we", pady=(14, 0))

        # ---- Right: live readings ----
        right = ttk.Labelframe(page, text="Live Readings", style="Card.TLabelframe")
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        for c in range(3):
            right.columnconfigure(c, weight=1, uniform="readout")

        self.auto_retries_var       = tk.StringVar(value="—")
        self.auto_meas_voltage_var  = tk.StringVar(value="—")
        self.auto_meas_current_var  = tk.StringVar(value="—")
        self.auto_drv_voltage_var   = tk.StringVar(value="—")
        self.auto_drv_current_var   = tk.StringVar(value="—")
        self.auto_temperature_var   = tk.StringVar(value="—")
        self.auto_contactors_var    = tk.StringVar(value="—")
        self.auto_isolation_var     = tk.StringVar(value="—")
        self.auto_operational_var   = tk.StringVar(value="—")

        cells = [
            # row 0 — status
            ("Operational",      self.auto_operational_var, 0, 0, None),
            ("Contactors",       self.auto_contactors_var,  0, 1, None),
            ("Isolation",        self.auto_isolation_var,   0, 2, None),
            # row 1 — measured
            ("Measured Voltage", self.auto_meas_voltage_var, 1, 0, "V"),
            ("Measured Current", self.auto_meas_current_var, 1, 1, "A"),
            ("Temperature",      self.auto_temperature_var,  1, 2, "°C"),
            # row 2 — driven + meta
            ("Driven Voltage",   self.auto_drv_voltage_var, 2, 0, "V"),
            ("Driven Current",   self.auto_drv_current_var, 2, 1, "A"),
            ("Retries",          self.auto_retries_var,     2, 2, None),
        ]
        for label, var, r, c, unit in cells:
            cell = ttk.Frame(right, style="Card.TFrame")
            cell.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)
            cell.columnconfigure(0, weight=1)
            ttk.Label(cell, text=label, style="CardLabel.TLabel",
                      foreground=PALETTE["text_muted"], font=("Segoe UI", 9)).grid(
                row=0, column=0, sticky="w")
            row_val = ttk.Frame(cell, style="Card.TFrame")
            row_val.grid(row=1, column=0, sticky="w", pady=(2, 0))
            ttk.Label(row_val, textvariable=var, style="CardLabel.TLabel",
                      font=("Consolas", 14, "bold")).pack(side="left")
            if unit:
                ttk.Label(row_val, text=" " + unit, style="CardLabel.TLabel",
                          foreground=PALETTE["text_muted"], font=("Segoe UI", 10)).pack(
                    side="left", anchor="s", pady=(0, 2))

        for r in range(3):
            right.rowconfigure(r, weight=1)

        hint = ttk.Label(
            page,
            text="Tip: full message log lives on the Controls tab. EV Parameter "
                 "changes apply on the next send after you click Update Parameters.",
            style="Muted.TLabel", wraplength=720, justify="left",
        )
        hint.grid(row=1, column=0, columnspan=2, sticky="we", pady=(14, 0))

    # ------------------------------------------------------------------
    # Configuration tab
    # ------------------------------------------------------------------
    def _build_config_tab(self):
        page = ttk.Frame(self.config_tab)
        page.pack(fill="both", expand=True, padx=18, pady=18)
        page.columnconfigure(0, weight=1, uniform="cfg")
        page.columnconfigure(1, weight=1, uniform="cfg")

        def add_row(card, row, label, key, default, unit, var_type=tk.DoubleVar):
            ttk.Label(card, text=label, style="CardLabel.TLabel").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=4)
            var = var_type(value=default)
            self.auto_config_vars[key] = var
            ttk.Entry(card, textvariable=var, width=10, justify="right").grid(
                row=row, column=1, sticky="we", pady=4)
            ttk.Label(card, text=unit, style="CardLabel.TLabel",
                      foreground=PALETTE["text_muted"]).grid(
                row=row, column=2, sticky="w", padx=(8, 0), pady=4)

        # Card: waits
        waits = ttk.Labelframe(page, text="Initial Waits", style="Card.TLabelframe")
        waits.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        waits.columnconfigure(1, weight=1)
        add_row(waits, 0, "After Gun Connect",     "post_gun_wait",      AUTO_DEFAULTS["post_gun_wait"],      "s")
        add_row(waits, 1, "After Transfer Allowed","post_transfer_wait", AUTO_DEFAULTS["post_transfer_wait"], "s")

        # Card: intervals
        intervals = ttk.Labelframe(page, text="Message Intervals", style="Card.TLabelframe")
        intervals.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        intervals.columnconfigure(1, weight=1)
        add_row(intervals, 0, "Vehicle Info",  "vehicle_info_interval", AUTO_DEFAULTS["vehicle_info_interval"], "s")
        add_row(intervals, 1, "Cable Check",   "cable_check_interval",  AUTO_DEFAULTS["cable_check_interval"],  "s")
        add_row(intervals, 2, "Precharge",     "precharge_interval",    AUTO_DEFAULTS["precharge_interval"],    "s")
        add_row(intervals, 3, "Charge",        "charge_interval",       AUTO_DEFAULTS["charge_interval"],       "s")

        # Card: thresholds
        thresholds = ttk.Labelframe(page, text="Pass Thresholds (% of target)",
                                    style="Card.TLabelframe")
        thresholds.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(14, 0))
        thresholds.columnconfigure(1, weight=1)
        add_row(thresholds, 0, "Precharge Voltage", "precharge_voltage_pct", AUTO_DEFAULTS["precharge_voltage_pct"], "%")
        add_row(thresholds, 1, "Precharge Current", "precharge_current_pct", AUTO_DEFAULTS["precharge_current_pct"], "%")
        add_row(thresholds, 2, "Charge Voltage",    "charge_voltage_pct",    AUTO_DEFAULTS["charge_voltage_pct"],    "%")
        add_row(thresholds, 3, "Charge Current",    "charge_current_pct",    AUTO_DEFAULTS["charge_current_pct"],    "%")

        # Card: retries + current tracking
        misc = ttk.Labelframe(page, text="Retries & Tracking", style="Card.TLabelframe")
        misc.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(14, 0))
        misc.columnconfigure(1, weight=1)
        add_row(misc, 0, "Max retries per stage", "max_retries",
                AUTO_DEFAULTS["max_retries"], "", var_type=tk.IntVar)

        pre_track = tk.BooleanVar(value=AUTO_DEFAULTS["precharge_track_current"])
        chg_track = tk.BooleanVar(value=AUTO_DEFAULTS["charge_track_current"])
        self.auto_config_vars["precharge_track_current"] = pre_track
        self.auto_config_vars["charge_track_current"]    = chg_track
        ttk.Checkbutton(misc, text="Track current during Precharge", variable=pre_track).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(10, 2))
        ttk.Checkbutton(misc, text="Track current during Charge", variable=chg_track).grid(
            row=2, column=0, columnspan=3, sticky="w")

        # Reset button
        reset_row = ttk.Frame(page)
        reset_row.grid(row=2, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(reset_row, text="Reset to Defaults", style="Secondary.TButton",
                   command=self._reset_auto_config).pack(side="right")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _reset_auto_config(self):
        for key, var in self.auto_config_vars.items():
            var.set(AUTO_DEFAULTS[key])

    def _clear_log(self):
        self.log_text.delete("1.0", tk.END)

    def _toggle_auto_scroll(self):
        self.auto_scroll = not self.auto_scroll
        self.auto_scroll_var.set("Auto Scroll: ON" if self.auto_scroll else "Auto Scroll: OFF")

    def _on_update_params(self):
        _ = self.get_form_data()
        if self.log_callback:
            try:
                self.log_callback(">>>>> Parameters updated")
            except Exception:
                pass

    def _on_auto_button(self):
        if self._auto_running:
            if self.auto_stop_callback:
                self.auto_stop_callback()
        else:
            if self.auto_start_callback:
                self.auto_start_callback()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_form_data(self) -> Dict[str, float]:
        for key, var in self.param_vars.items():
            try:
                self.form_data[key] = float(var.get())
            except Exception:
                pass
        return self.form_data

    def add_log_message(self, message: str):
        tag = None
        if message.startswith(">>>>>"):
            tag = "sent"
        elif message.startswith("<<<<<"):
            tag = "recv"
        elif message.startswith("[AUTO]") or message.startswith("INFO") or message.startswith("ERROR"):
            tag = "info"
        if tag:
            self.log_text.insert(tk.END, message + "\n", tag)
        else:
            self.log_text.insert(tk.END, message + "\n")
        if self.auto_scroll:
            self.log_text.see(tk.END)

    def update_gun_button(self, connected: bool):
        self.gun_btn.configure(
            text="Disconnect Gun" if connected else "Connect Gun",
            style="Danger.TButton" if connected else "Primary.TButton",
        )

    def update_vehicle_info_button(self, step: int, total: int = 5):
        self.send_vehicle_info_btn.configure(text=f"Send Vehicle Info  (Step {step}/{total})")

    def set_auto_callbacks(self, start_cb: Callable[[], None], stop_cb: Callable[[], None]):
        self.auto_start_callback = start_cb
        self.auto_stop_callback = stop_cb

    def get_auto_config(self) -> Dict[str, Any]:
        cfg = {}
        for key, var in self.auto_config_vars.items():
            try:
                cfg[key] = var.get()
            except Exception:
                cfg[key] = AUTO_DEFAULTS[key]
        return cfg

    def set_auto_running(self, running: bool):
        self._auto_running = running
        if running:
            self.auto_btn.configure(text="Stop Charging", style="HeroStop.TButton")
        else:
            self.auto_btn.configure(text="Start Charging", style="Hero.TButton")

    def update_auto_status(self, status: Dict[str, Any]):
        stage = status.get("stage", "Idle")
        self.auto_stage_var.set(stage)
        self.auto_stage_label.configure(bg=STAGE_COLORS.get(stage, "#94a3b8"))

        retries = status.get("retries", 0)
        self.auto_retries_var.set(str(retries) if retries else "—")

        def fmt(v, suffix=""):
            if isinstance(v, (int, float)):
                return f"{v:.2f}{suffix}"
            return "—"

        self.auto_meas_voltage_var.set(fmt(status.get("measuredVoltage")))
        self.auto_meas_current_var.set(fmt(status.get("measuredCurrent")))
        self.auto_drv_voltage_var.set(fmt(status.get("drivenVoltage")))
        self.auto_drv_current_var.set(fmt(status.get("drivenCurrent")))
        self.auto_temperature_var.set(fmt(status.get("temperature")))
        self.auto_contactors_var.set(status.get("contactorsStatus") or "—")
        self.auto_isolation_var.set(status.get("isolationStatus") or "—")
        self.auto_operational_var.set(status.get("operationalStatus") or "—")
