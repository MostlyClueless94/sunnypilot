import json
from pathlib import Path

from openpilot.sunnypilot.selfdrive.car.car_list import get_runtime_car_list
from opendbc.sunnypilot.car.platform_list import get_car_list


class TestCarList:
  def test_supported_newer_subarus_are_exposed(self):
    generated_car_list = get_car_list()

    assert "Subaru Forester 2022-24" in generated_car_list
    assert generated_car_list["Subaru Forester 2022-24"]["platform"] == "SUBARU_FORESTER_2022"
    assert "Subaru Outback 2023-25" in generated_car_list
    assert generated_car_list["Subaru Outback 2023-25"]["platform"] == "SUBARU_OUTBACK_2023"
    assert "Subaru Ascent 2023" in generated_car_list
    assert generated_car_list["Subaru Ascent 2023"]["platform"] == "SUBARU_ASCENT_2023"
    assert "Subaru Crosstrek 2025" in generated_car_list
    assert generated_car_list["Subaru Crosstrek 2025"]["platform"] == "SUBARU_CROSSTREK_2025"

  def test_generator(self):
    generated_car_list = get_car_list()
    runtime_car_list = get_runtime_car_list()

    assert runtime_car_list == generated_car_list

  def test_static_json_matches_generated_list(self):
    generated_car_list = get_car_list()
    car_list_json = Path(__file__).resolve().parents[1] / "car_list.json"

    with open(car_list_json) as f:
      static_car_list = json.load(f)

    assert static_car_list == generated_car_list
