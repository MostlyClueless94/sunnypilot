from types import SimpleNamespace

from cereal import custom
from opendbc.car import structs
from openpilot.selfdrive.selfdrived.events import Events
from openpilot.sunnypilot.mads.helpers import MadsSteeringModeOnBrake
from openpilot.sunnypilot.mads.mads import ModularAssistiveDrivingSystem
from openpilot.sunnypilot.selfdrive.selfdrived.events import EventsSP


ButtonType = structs.CarState.ButtonEvent.Type
EventNameSP = custom.OnroadEventSP.EventName
State = custom.ModularAssistiveDrivingSystem.ModularAssistiveDrivingSystemState


def _make_lkas_button_event():
  return SimpleNamespace(type=ButtonType.lkas, pressed=True)


def _make_mads_for_button_test(selfdrive_enabled=True, mads_enabled=True):
  events = Events()
  events_sp = EventsSP()
  selfdrive = SimpleNamespace(
    enabled=selfdrive_enabled,
    enabled_prev=False,
    CS_prev=SimpleNamespace(gasPressed=False, cruiseState=SimpleNamespace(available=True)),
    events=events,
    events_sp=events_sp,
  )

  mads = ModularAssistiveDrivingSystem.__new__(ModularAssistiveDrivingSystem)
  mads.enabled = mads_enabled
  mads.allow_always = False
  mads.main_enabled_toggle = False
  mads.no_main_cruise = False
  mads.steering_mode_on_brake = MadsSteeringModeOnBrake.REMAIN_ACTIVE
  mads.unified_engagement_mode = False
  mads.selfdrive = selfdrive
  mads.state_machine = SimpleNamespace(state=State.enabled)
  mads.events = events
  mads.events_sp = events_sp
  mads.disengage_on_accelerator = False
  return mads


def _make_car_state(button_events):
  return SimpleNamespace(
    buttonEvents=button_events,
    cruiseState=SimpleNamespace(available=True),
    gasPressed=False,
    standstill=False,
    vEgo=10.0,
  )


def test_lkas_button_in_full_openpilot_disables_mads_lateral_not_manual_steering_required():
  mads = _make_mads_for_button_test(selfdrive_enabled=True, mads_enabled=True)

  mads.update_events(_make_car_state([_make_lkas_button_event()]))

  assert mads.events_sp.has(EventNameSP.lkasDisable)
  assert not mads.events_sp.has(EventNameSP.manualSteeringRequired)
