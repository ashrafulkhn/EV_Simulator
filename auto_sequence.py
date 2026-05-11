"""
Automatic test sequence state machine for EV Simulator.

Runs on the shared asyncio event loop. Drives a sequential charging flow:
gun connect -> vehicle info (5 messages) -> transfer allowed -> cable check ->
precharge -> charge (streaming). Listens to incoming PEP "status" info messages
to gate stage transitions.

Thread model:
  - start()/stop()/on_status() are called from the Tk main thread.
  - The state machine coroutine runs on the asyncio thread.
  - All UI callbacks (status_cb, log_cb) must be thread-safe (typically they
    enqueue events that Tk processes).
"""

import asyncio
import logging
from enum import Enum
from typing import Callable, Optional


class Stage(Enum):
    IDLE = "Idle"
    GUN_CONNECT = "Gun Connect"
    VEHICLE_INFO = "Vehicle Info"
    TRANSFER_ALLOWED = "Transfer Allowed"
    CABLE_CHECK = "Cable Check"
    PRECHARGE = "Precharge"
    CHARGE = "Charge"
    STREAMING = "Charging (streaming)"
    STOPPING = "Stopping"
    FAILED = "FAILED"


class AutoSequence:
    def __init__(self, ws_handler, message_handler, get_form_data: Callable[[], dict],
                 status_cb: Callable[[dict], None], log_cb: Callable[[str], None]):
        self.ws = ws_handler
        self.mh = message_handler
        self.get_form_data = get_form_data
        self.status_cb = status_cb
        self.log_cb = log_cb

        self._future = None
        self._stop_flag = False
        self._cfg: dict = {}
        self._stage = Stage.IDLE
        self._retries = 0
        self._last_status: dict = {}
        self._logger = logging.getLogger(__name__)

    def start(self, loop: asyncio.AbstractEventLoop, cfg: dict):
        if self.is_running():
            return
        self._cfg = dict(cfg)
        self._stop_flag = False
        self._last_status = {}
        self._future = asyncio.run_coroutine_threadsafe(self._run(), loop)

    def stop(self, loop: asyncio.AbstractEventLoop):
        self._stop_flag = True
        asyncio.run_coroutine_threadsafe(self._send_stop_and_reset(user_initiated=True), loop)

    def is_running(self) -> bool:
        return self._future is not None and not self._future.done()

    def on_status(self, payload: dict):
        if isinstance(payload, dict):
            self._last_status = payload
            self._emit_status()

    def _emit_status(self):
        try:
            s = self._last_status
            self.status_cb({
                "stage": self._stage.value,
                "retries": self._retries,
                "measuredVoltage":   s.get("measuredVoltage"),
                "measuredCurrent":   s.get("measuredCurrent"),
                "drivenVoltage":     s.get("drivenVoltage"),
                "drivenCurrent":     s.get("drivenCurrent"),
                "temperature":       s.get("temperature"),
                "contactorsStatus":  s.get("contactorsStatus"),
                "isolationStatus":   s.get("isolationStatus"),
                "operationalStatus": s.get("operationalStatus"),
            })
        except Exception:
            self._logger.exception("status_cb failed")

    def _log(self, msg: str):
        try:
            self.log_cb(f"[AUTO] {msg}")
        except Exception:
            pass

    def _set_stage(self, stage: Stage, retries: int = 0):
        self._stage = stage
        self._retries = retries
        self._emit_status()

    async def _send(self, message: dict) -> bool:
        if not self.ws.is_connected():
            self._log("ERROR: WebSocket not connected")
            return False
        try:
            await self.ws.send_message(message)
            self.log_cb(self.mh.format_message_for_log(message, "sent"))
            return True
        except Exception as e:
            self._log(f"send failed: {e}")
            return False

    async def _send_stop_and_reset(self, user_initiated: bool = False):
        if user_initiated:
            self._set_stage(Stage.STOPPING)
            self._log("Stop requested by user")
        await self._send(self.mh.create_stop_charging())
        await asyncio.sleep(0.2)
        await self._send(self.mh.create_reset())
        if user_initiated:
            self._set_stage(Stage.IDLE)

    async def _fail(self, reason: str):
        self._log(f"Sequence FAILED: {reason}")
        await self._send(self.mh.create_stop_charging())
        await asyncio.sleep(0.2)
        await self._send(self.mh.create_reset())
        self._set_stage(Stage.FAILED)

    def _check_stop(self) -> bool:
        if self._stop_flag:
            self._set_stage(Stage.IDLE)
            return True
        return False

    def _check_inoperative(self) -> bool:
        op = self._last_status.get("operationalStatus")
        return op is not None and op != "operative"

    async def _run(self):
        try:
            cfg = self._cfg
            self._log("Auto sequence started")

            # Gun connect
            self._set_stage(Stage.GUN_CONNECT)
            await self._send(self.mh.create_ev_connection_state("connected"))
            await asyncio.sleep(cfg["post_gun_wait"])
            if self._check_stop(): return

            # Vehicle info x5 (built once to share form snapshot across the burst)
            self._set_stage(Stage.VEHICLE_INFO)
            form = self.get_form_data()
            sequence = self.mh.get_vehicle_info_sequence(form)
            for i, msg in enumerate(sequence):
                self._log(f"Vehicle info {i + 1}/5")
                await self._send(msg)
                await asyncio.sleep(cfg["vehicle_info_interval"])
                if self._check_stop(): return

            # Transfer allowed
            self._set_stage(Stage.TRANSFER_ALLOWED)
            await self._send(self.mh.create_ev_connection_state("energyTransferAllowed"))
            await asyncio.sleep(cfg["post_transfer_wait"])
            if self._check_stop(): return

            # Cable check
            if not await self._cable_check(cfg): return
            if self._check_stop(): return

            # Precharge
            if not await self._precharge(cfg): return
            if self._check_stop(): return

            # Charge ramp + stream until stop
            await self._charge(cfg)

        except asyncio.CancelledError:
            self._log("Auto sequence cancelled")
        except Exception as e:
            self._logger.exception("AutoSequence crashed")
            await self._fail(f"unexpected error: {e}")

    async def _cable_check(self, cfg) -> bool:
        max_retries = cfg["max_retries"]
        interval = cfg["cable_check_interval"]
        for attempt in range(1, max_retries + 1):
            if self._stop_flag: return False
            self._set_stage(Stage.CABLE_CHECK, retries=attempt)
            form = self.get_form_data()
            voltage = form.get("cableCheckVoltage", 450.0)
            await self._send(self.mh.create_cable_check(voltage))
            await asyncio.sleep(interval)
            if self._check_inoperative():
                await self._fail("PECC reported inoperative during cable check")
                return False
            if self._last_status.get("isolationStatus") == "valid":
                self._log(f"Cable check PASSED on attempt {attempt}")
                return True
        await self._fail(f"cable check did not report isolation valid after {max_retries} retries")
        return False

    async def _precharge(self, cfg) -> bool:
        max_retries = cfg["max_retries"]
        interval = cfg["precharge_interval"]
        v_pct = cfg["precharge_voltage_pct"] / 100.0
        i_pct = cfg["precharge_current_pct"] / 100.0
        track_current = cfg["precharge_track_current"]

        for attempt in range(1, max_retries + 1):
            if self._stop_flag: return False
            self._set_stage(Stage.PRECHARGE, retries=attempt)
            form = self.get_form_data()
            target_v = float(form.get("prechargeTargetVoltage", 400))
            target_i = float(form.get("prechargeTargetCurrent", 10))
            msg = self.mh.create_target_values({
                "batteryStateOfCharge": form.get("batteryStateOfCharge", 45),
                "chargingState": "preCharge",
                "targetCurrent": target_i,
                "targetVoltage": target_v,
            })
            await self._send(msg)
            await asyncio.sleep(interval)
            if self._check_inoperative():
                await self._fail("PECC reported inoperative during precharge")
                return False
            mv = self._last_status.get("measuredVoltage")
            mc = self._last_status.get("measuredCurrent")
            v_ok = isinstance(mv, (int, float)) and mv >= target_v * v_pct
            i_ok = (not track_current) or (isinstance(mc, (int, float)) and mc >= target_i * i_pct)
            if v_ok and i_ok:
                self._log(f"Precharge PASSED on attempt {attempt} (V={mv}, I={mc})")
                return True
        await self._fail(f"precharge did not reach threshold after {max_retries} retries")
        return False

    async def _charge(self, cfg):
        max_retries = cfg["max_retries"]
        interval = cfg["charge_interval"]
        v_pct = cfg["charge_voltage_pct"] / 100.0
        i_pct = cfg["charge_current_pct"] / 100.0
        track_current = cfg["charge_track_current"]

        reached = False
        ramp_attempt = 0
        while True:
            if self._stop_flag:
                self._set_stage(Stage.IDLE)
                return
            form = self.get_form_data()
            target_v = float(form.get("chargeTargetVoltage", 500))
            target_i = float(form.get("chargeTargetCurrent", 60))
            msg = self.mh.create_target_values({
                "batteryStateOfCharge": form.get("batteryStateOfCharge", 78),
                "chargingState": "charging",
                "targetCurrent": target_i,
                "targetVoltage": target_v,
            })
            await self._send(msg)
            await asyncio.sleep(interval)
            if self._check_inoperative():
                await self._fail("PECC reported inoperative during charge")
                return

            mv = self._last_status.get("measuredVoltage")
            mc = self._last_status.get("measuredCurrent")
            v_ok = isinstance(mv, (int, float)) and mv >= target_v * v_pct
            i_ok = (not track_current) or (isinstance(mc, (int, float)) and mc >= target_i * i_pct)

            if reached:
                self._set_stage(Stage.STREAMING)
                continue

            if v_ok and i_ok:
                reached = True
                self._set_stage(Stage.STREAMING)
                self._log(f"Charge threshold reached (V={mv}, I={mc}). Streaming...")
            else:
                ramp_attempt += 1
                self._set_stage(Stage.CHARGE, retries=ramp_attempt)
                if ramp_attempt >= max_retries:
                    await self._fail(f"charge did not reach threshold after {max_retries} retries")
                    return
