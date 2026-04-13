from opendbc.car import structs
from openpilot.selfdrive.car.helpers import convert_to_capnp


def test_carstate_sp_brake_light_fields_survive_capnp_conversion():
  car_state_sp = structs.CarStateSP()
  car_state_sp.brakeLightsAvailable = True
  car_state_sp.brakeLightsOn = True

  msg = convert_to_capnp(car_state_sp)

  assert msg.brakeLightsAvailable
  assert msg.brakeLightsOn
