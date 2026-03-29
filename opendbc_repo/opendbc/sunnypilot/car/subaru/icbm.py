"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.

Subaru ICBM (Intelligent Cruise Button Management)
---------------------------------------------------
Emulates ACC set/resume button presses via the ES_Distance CAN message to
adjust the stock Subaru ACC set-speed in response to map-based speed limit
changes from sunnypilot's SpeedLimitAssist stack.

Button emulation works by overriding the Cruise_Set or Cruise_Resume fields
in a replayed ES_Distance frame on the correct bus (alt/bus-1 for Gen2 cars).

This path fires only when openpilot longitudinal control is OFF. When OP long
is active, the longitudinal controller adjusts speed directly and ICBM is
bypassed. The carcontroller gates entry here on:
  - CP_SP.intelligentCruiseButtonManagementAvailable == True
  - CP.openpilotLongitudinalControl == False
  - CS.out.cruiseState.available == True  (ACC main switch on)
"""

import copy
from opendbc.car import structs, DT_CTRL
from opendbc.car.can_definitions import CanData
from opendbc.car.carlog import carlog
from opendbc.car.subaru import subarucan
from opendbc.car.subaru.values import CanBus, SubaruFlags
from opendbc.sunnypilot.car.intelligent_cruise_button_management_interface_base import (
  IntelligentCruiseButtonManagementInterfaceBase,
)

SendButtonState = structs.IntelligentCruiseButtonManagement.SendButtonState

# Minimum time between button press frames: 50 ms, same as Honda ICBM.
# Prevents button spam and ACC faults from rapid repeated presses.
ICBM_BUTTON_MIN_INTERVAL = 0.05  # seconds


class IntelligentCruiseButtonManagementInterface(IntelligentCruiseButtonManagementInterfaceBase):
  """
  Subaru-specific ICBM implementation.

  Injects Cruise_Set (speed down) or Cruise_Resume (speed up) bit pulses into
  a single ES_Distance frame. The frame uses CS.es_distance_msg as the
  passthrough template and increments its COUNTER by 1 so the car sees a
  valid new frame rather than a replay of the previous one.

  Bus selection mirrors the long replay path:
    Gen2 cars (OUTBACK_2023, ASCENT_2023, CROSSTREK_2025) -> CanBus.alt (bus 1)
    Other global cars                                      -> CanBus.main (bus 0)
  """

  def __init__(self, CP: structs.CarParams, CP_SP: structs.CarParamsSP):
    super().__init__(CP, CP_SP)

  def update(
    self,
    CC_SP,
    packer,
    frame: int,
    last_button_frame: int,
    CS,
  ) -> list[CanData]:
    """
    Called each carcontroller tick when ICBM is available and ACC is active.

    Returns a list of CAN messages (0 or 1 ES_Distance frame with a button pulse).
    Returns an empty list when no button is requested or the rate limit is active.
    """
    can_sends: list[CanData] = []

    icbm = CC_SP.intelligentCruiseButtonManagement
    send_button = icbm.sendButton

    if send_button == SendButtonState.none:
      return can_sends

    # Rate-limit: enforce minimum interval between button presses
    elapsed = (frame - last_button_frame) * DT_CTRL
    if elapsed < ICBM_BUTTON_MIN_INTERVAL:
      return can_sends

    # Require a valid ES_Distance template from carstate.
    # If the template is missing or not a dict-like object, skip safely.
    es_distance_msg = getattr(CS, "es_distance_msg", None)
    if not es_distance_msg:
      carlog.warning(f"subaru[{self.CP.carFingerprint}] ICBM: es_distance_msg not available, skipping button press")
      return can_sends

    # Build a modified copy of the current ES_Distance message.
    # Increment counter by 1 (mod 0x10) so the car sees a new frame.
    try:
      values = dict(es_distance_msg)
    except (TypeError, ValueError):
      carlog.warning(f"subaru[{self.CP.carFingerprint}] ICBM: es_distance_msg not iterable, skipping")
      return can_sends

    new_counter = (int(values.get("COUNTER", 0)) + 1) % 0x10
    values["COUNTER"] = new_counter

    # Clear both button bits first, then set the requested one.
    # Never set both simultaneously — that can confuse the ACC controller.
    values["Cruise_Set"] = 0
    values["Cruise_Resume"] = 0
    values["Cruise_Cancel"] = 0  # never cancel during ICBM adjustment

    if send_button == SendButtonState.decrease:
      # Decrease set-speed: Cruise_Set pulse (same as tapping the SET- button)
      values["Cruise_Set"] = 1
      carlog.info(f"subaru[{self.CP.carFingerprint}] ICBM: sending Cruise_Set (decrease) counter={new_counter}")
    elif send_button == SendButtonState.increase:
      # Increase set-speed: Cruise_Resume pulse (same as tapping the RES+ button)
      values["Cruise_Resume"] = 1
      carlog.info(f"subaru[{self.CP.carFingerprint}] ICBM: sending Cruise_Resume (increase) counter={new_counter}")

    # Suppress any latched soft-disable or fault bits in the injected frame
    values["Cruise_Soft_Disable"] = 0
    values["Cruise_Fault"] = 0

    bus = CanBus.alt if (self.CP.flags & SubaruFlags.GLOBAL_GEN2) else CanBus.main
    can_sends.append(packer.make_can_msg("ES_Distance", bus, values))

    return can_sends
