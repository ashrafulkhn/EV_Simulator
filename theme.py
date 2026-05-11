"""
Centralized ttk theme for EV Simulator.

apply_theme(root) configures ttk.Style with a modern, minimal palette and
returns the Style object so callers can extend it if needed.

Custom button styles available:
  Primary.TButton   indigo (default action)
  Accent.TButton    cyan
  Success.TButton   emerald (start)
  Warning.TButton   amber (reset)
  Danger.TButton    rose (stop)
  Secondary.TButton soft indigo on light bg (less prominent actions)
"""

import tkinter as tk
from tkinter import ttk

PALETTE = {
    "bg":          "#f4f6fb",
    "surface":     "#ffffff",
    "surface_alt": "#f8fafc",
    "border":      "#e2e8f0",
    "border_dark": "#cbd5e1",
    "text":        "#0f172a",
    "text_muted":  "#64748b",

    "primary":   "#4f46e5", "primary_h":  "#6366f1", "primary_d":  "#4338ca",
    "accent":    "#06b6d4", "accent_h":   "#22d3ee", "accent_d":   "#0891b2",
    "success":   "#10b981", "success_h":  "#34d399", "success_d":  "#059669",
    "warning":   "#f59e0b", "warning_h":  "#fbbf24", "warning_d":  "#d97706",
    "danger":    "#f43f5e", "danger_h":   "#fb7185", "danger_d":   "#e11d48",

    "log_bg":   "#0f172a",
    "log_fg":   "#e2e8f0",
    "log_sent": "#a5b4fc",
    "log_recv": "#86efac",
}

FONT_TITLE   = ("Segoe UI", 15, "bold")
FONT_HEADING = ("Segoe UI", 10, "bold")
FONT_BODY    = ("Segoe UI", 10)
FONT_SMALL   = ("Segoe UI", 9)
FONT_MONO    = ("Consolas", 10)
FONT_BUTTON  = ("Segoe UI", 10, "bold")


def apply_theme(root: tk.Tk) -> ttk.Style:
    root.configure(bg=PALETTE["bg"])
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    p = PALETTE

    # --- Base ---
    style.configure(".", background=p["bg"], foreground=p["text"], font=FONT_BODY)
    style.configure("TFrame", background=p["bg"])
    style.configure("Card.TFrame", background=p["surface"])

    style.configure("TLabel", background=p["bg"], foreground=p["text"])
    style.configure("Muted.TLabel", background=p["bg"], foreground=p["text_muted"], font=FONT_SMALL)
    style.configure("Heading.TLabel", background=p["bg"], foreground=p["text"], font=FONT_HEADING)
    style.configure("Title.TLabel", background=p["bg"], foreground=p["text"], font=FONT_TITLE)
    style.configure("CardLabel.TLabel", background=p["surface"], foreground=p["text"])
    style.configure("Value.TLabel", background=p["bg"], foreground=p["text"], font=FONT_MONO)

    # --- LabelFrame (cards) ---
    style.configure(
        "Card.TLabelframe",
        background=p["surface"],
        bordercolor=p["border"],
        relief="solid", borderwidth=1,
        padding=12,
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=p["surface"],
        foreground=p["primary"],
        font=FONT_HEADING,
        padding=(0, 0, 0, 4),
    )

    # --- Entry ---
    style.configure(
        "TEntry",
        fieldbackground=p["surface"],
        background=p["surface"],
        foreground=p["text"],
        bordercolor=p["border_dark"],
        lightcolor=p["border_dark"],
        darkcolor=p["border_dark"],
        insertcolor=p["text"],
        padding=6,
        relief="flat",
    )
    style.map(
        "TEntry",
        bordercolor=[("focus", p["primary"])],
        lightcolor=[("focus", p["primary"])],
        darkcolor=[("focus", p["primary"])],
    )

    # --- Notebook ---
    style.configure("TNotebook", background=p["bg"], borderwidth=0, tabmargins=[0, 4, 0, 0])
    style.configure(
        "TNotebook.Tab",
        background=p["bg"],
        foreground=p["text_muted"],
        padding=[20, 10],
        font=FONT_BODY,
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", p["surface"]), ("active", "#e0e7ff")],
        foreground=[("selected", p["primary"]), ("active", p["primary"])],
        font=[("selected", FONT_BUTTON)],
        expand=[("selected", [1, 1, 1, 0])],
    )

    # --- Checkbutton ---
    style.configure("TCheckbutton", background=p["surface"], foreground=p["text"], padding=4)
    style.map(
        "TCheckbutton",
        background=[("active", p["surface"])],
        indicatorcolor=[("selected", p["primary"]), ("!selected", p["surface"])],
        indicatorrelief=[("pressed", "flat")],
    )

    # --- Buttons ---
    def _btn_style(name, bg, hover, down):
        style.configure(
            name,
            background=bg, foreground="white",
            font=FONT_BUTTON, padding=(14, 8),
            borderwidth=0, focusthickness=0, relief="flat",
            anchor="center",
        )
        style.map(
            name,
            background=[("pressed", down), ("active", hover), ("disabled", "#cbd5e1")],
            foreground=[("disabled", "#94a3b8")],
        )

    _btn_style("TButton",         p["primary"], p["primary_h"], p["primary_d"])
    _btn_style("Primary.TButton", p["primary"], p["primary_h"], p["primary_d"])
    _btn_style("Accent.TButton",  p["accent"],  p["accent_h"],  p["accent_d"])
    _btn_style("Success.TButton", p["success"], p["success_h"], p["success_d"])
    _btn_style("Warning.TButton", p["warning"], p["warning_h"], p["warning_d"])
    _btn_style("Danger.TButton",  p["danger"],  p["danger_h"],  p["danger_d"])

    # Outlined-soft button for secondary actions
    style.configure(
        "Secondary.TButton",
        background="#eef2ff", foreground=p["primary"],
        font=FONT_BUTTON, padding=(14, 8),
        borderwidth=0, focusthickness=0, relief="flat",
        anchor="center",
    )
    style.map(
        "Secondary.TButton",
        background=[("pressed", "#c7d2fe"), ("active", "#e0e7ff")],
    )

    # Big call-to-action (Start/Stop on Automatic tab)
    style.configure(
        "Hero.TButton",
        background=p["success"], foreground="white",
        font=("Segoe UI", 12, "bold"), padding=(16, 12),
        borderwidth=0, focusthickness=0, relief="flat",
    )
    style.map(
        "Hero.TButton",
        background=[("pressed", p["success_d"]), ("active", p["success_h"])],
    )
    style.configure(
        "HeroStop.TButton",
        background=p["danger"], foreground="white",
        font=("Segoe UI", 12, "bold"), padding=(16, 12),
        borderwidth=0, focusthickness=0, relief="flat",
    )
    style.map(
        "HeroStop.TButton",
        background=[("pressed", p["danger_d"]), ("active", p["danger_h"])],
    )

    # --- Scrollbar ---
    style.configure(
        "Vertical.TScrollbar",
        background=p["border"], troughcolor=p["bg"],
        bordercolor=p["bg"], arrowcolor=p["text_muted"],
        relief="flat",
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", p["border_dark"])],
    )

    return style
