from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Iterator


DEFAULT_FAULT_WINDOW_NS = 5_000_000_000
STATE_CONTEXT_COUNT = 5
RELEVANT_SUBARU_LOG_TOKENS = (
  "angle LKAS request=",
  "angle LKAS inhibit=",
  "angle Steering_2 valid=",
  "ES_Status Cruise_Activated=",
  "Eyesight cruise fault=",
  "steerFaultTemporary=",
  "steerFaultPermanent=",
)


@dataclass(frozen=True)
class SubaruFaultState:
  time_ns: int
  steer_fault_temporary: bool
  steer_fault_permanent: bool
  steering_angle_deg: float
  steering_rate_deg: float
  steering_torque: float
  steering_torque_eps: float
  cruise_enabled: bool
  cruise_available: bool


@dataclass(frozen=True)
class SubaruLogTransition:
  time_ns: int
  channel: str
  message: str


@dataclass(frozen=True)
class SubaruFaultSummary:
  fault_kind: str
  fault_state: SubaruFaultState
  preceding_states: list[SubaruFaultState]
  following_states: list[SubaruFaultState]
  nearby_transitions: list[SubaruLogTransition]


def _coerce_float(value: Any) -> float:
  try:
    return float(value)
  except (TypeError, ValueError):
    return 0.0


def _coerce_bool(value: Any) -> bool:
  return bool(value)


def is_relevant_subaru_log(message: str) -> bool:
  return any(token in message for token in RELEVANT_SUBARU_LOG_TOKENS)


def _normalize_log_message_payload(payload: Any) -> str:
  if hasattr(payload, "message"):
    payload = payload.message
  if isinstance(payload, bytes):
    return payload.decode("utf-8", errors="replace")
  return str(payload)


def normalize_logreader_event(event: Any) -> dict[str, Any] | None:
  which = event.which()
  time_ns = int(getattr(event, "logMonoTime", 0))

  if which == "carState":
    car_state = event.carState
    return {
      "kind": "carState",
      "time_ns": time_ns,
      "steer_fault_temporary": _coerce_bool(getattr(car_state, "steerFaultTemporary", False)),
      "steer_fault_permanent": _coerce_bool(getattr(car_state, "steerFaultPermanent", False)),
      "steering_angle_deg": _coerce_float(getattr(car_state, "steeringAngleDeg", 0.0)),
      "steering_rate_deg": _coerce_float(getattr(car_state, "steeringRateDeg", 0.0)),
      "steering_torque": _coerce_float(getattr(car_state, "steeringTorque", 0.0)),
      "steering_torque_eps": _coerce_float(getattr(car_state, "steeringTorqueEps", 0.0)),
      "cruise_enabled": _coerce_bool(getattr(car_state.cruiseState, "enabled", False)),
      "cruise_available": _coerce_bool(getattr(car_state.cruiseState, "available", False)),
    }

  if which in ("logMessage", "errorLogMessage"):
    message = _normalize_log_message_payload(getattr(event, which))
    return {
      "kind": which,
      "time_ns": time_ns,
      "channel": which,
      "message": message,
    }

  return None


def iter_normalized_subaru_fault_events(events: Iterable[Any]) -> Iterator[dict[str, Any]]:
  for event in events:
    if isinstance(event, dict):
      normalized = event
    else:
      normalized = normalize_logreader_event(event)

    if normalized is None:
      continue

    if normalized["kind"] == "carState":
      yield normalized
    elif normalized["kind"] in ("logMessage", "errorLogMessage") and is_relevant_subaru_log(normalized.get("message", "")):
      yield normalized


def _state_from_normalized_event(event: dict[str, Any]) -> SubaruFaultState:
  return SubaruFaultState(
    time_ns=int(event.get("time_ns", 0)),
    steer_fault_temporary=_coerce_bool(event.get("steer_fault_temporary", False)),
    steer_fault_permanent=_coerce_bool(event.get("steer_fault_permanent", False)),
    steering_angle_deg=_coerce_float(event.get("steering_angle_deg", 0.0)),
    steering_rate_deg=_coerce_float(event.get("steering_rate_deg", 0.0)),
    steering_torque=_coerce_float(event.get("steering_torque", 0.0)),
    steering_torque_eps=_coerce_float(event.get("steering_torque_eps", 0.0)),
    cruise_enabled=_coerce_bool(event.get("cruise_enabled", False)),
    cruise_available=_coerce_bool(event.get("cruise_available", False)),
  )


def _transition_from_normalized_event(event: dict[str, Any]) -> SubaruLogTransition:
  return SubaruLogTransition(
    time_ns=int(event.get("time_ns", 0)),
    channel=str(event.get("channel", event.get("kind", "logMessage"))),
    message=str(event.get("message", "")),
  )


def summarize_first_subaru_lkas_fault(events: Iterable[dict[str, Any]], window_ns: int = DEFAULT_FAULT_WINDOW_NS) -> SubaruFaultSummary | None:
  states: list[SubaruFaultState] = []
  transitions: list[SubaruLogTransition] = []
  first_fault_state: SubaruFaultState | None = None
  first_fault_kind = ""

  for event in events:
    kind = event.get("kind")
    if kind == "carState":
      state = _state_from_normalized_event(event)
      states.append(state)
      if first_fault_state is None and (state.steer_fault_permanent or state.steer_fault_temporary):
        first_fault_state = state
        first_fault_kind = "permanent" if state.steer_fault_permanent else "temporary"
    elif kind in ("logMessage", "errorLogMessage") and is_relevant_subaru_log(str(event.get("message", ""))):
      transitions.append(_transition_from_normalized_event(event))

  if first_fault_state is None:
    return None

  window_start = first_fault_state.time_ns - window_ns
  window_end = first_fault_state.time_ns + window_ns

  preceding_states = [state for state in states if state.time_ns < first_fault_state.time_ns][-STATE_CONTEXT_COUNT:]
  following_states = [state for state in states if state.time_ns > first_fault_state.time_ns][:STATE_CONTEXT_COUNT]
  nearby_transitions = [transition for transition in transitions if window_start <= transition.time_ns <= window_end]

  return SubaruFaultSummary(
    fault_kind=first_fault_kind,
    fault_state=first_fault_state,
    preceding_states=preceding_states,
    following_states=following_states,
    nearby_transitions=nearby_transitions,
  )


def _format_time_offset(reference_time_ns: int, time_ns: int) -> str:
  return f"{(time_ns - reference_time_ns) / 1e9:+.3f}s"


def _format_state_line(reference_time_ns: int, state: SubaruFaultState) -> str:
  return (
    f"  - {_format_time_offset(reference_time_ns, state.time_ns)} "
    f"angle={state.steering_angle_deg:.2f} rate={state.steering_rate_deg:.2f} "
    f"torque={state.steering_torque:.2f} torqueEps={state.steering_torque_eps:.2f} "
    f"faultTemporary={state.steer_fault_temporary} faultPermanent={state.steer_fault_permanent} "
    f"cruiseEnabled={state.cruise_enabled} cruiseAvailable={state.cruise_available}"
  )


def format_subaru_fault_summary(summary: SubaruFaultSummary | None) -> str:
  if summary is None:
    return "No Subaru LKAS steer fault found."

  fault_time_ns = summary.fault_state.time_ns
  lines = [
    f"First Subaru LKAS {summary.fault_kind} fault at {fault_time_ns} ns",
    (
      f"Fault snapshot: angle={summary.fault_state.steering_angle_deg:.2f} "
      f"rate={summary.fault_state.steering_rate_deg:.2f} "
      f"torque={summary.fault_state.steering_torque:.2f} "
      f"torqueEps={summary.fault_state.steering_torque_eps:.2f} "
      f"cruiseEnabled={summary.fault_state.cruise_enabled} "
      f"cruiseAvailable={summary.fault_state.cruise_available}"
    ),
  ]

  if summary.preceding_states:
    lines.append("Preceding carState samples:")
    lines.extend(_format_state_line(fault_time_ns, state) for state in summary.preceding_states)

  if summary.following_states:
    lines.append("Following carState samples:")
    lines.extend(_format_state_line(fault_time_ns, state) for state in summary.following_states)

  if summary.nearby_transitions:
    lines.append("Nearby Subaru transitions:")
    for transition in summary.nearby_transitions:
      lines.append(f"  - {_format_time_offset(fault_time_ns, transition.time_ns)} [{transition.channel}] {transition.message}")

  return "\n".join(lines)
