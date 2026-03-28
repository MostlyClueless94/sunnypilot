import json

from opendbc.sunnypilot.car.platform_list import get_car_list, CAR_LIST_JSON_OUT


class TestCarList:
  def test_supported_newer_subarus_are_exposed(self):
    generated_car_list = get_car_list()

    assert "Subaru Outback 2023-25" in generated_car_list
    assert generated_car_list["Subaru Outback 2023-25"]["platform"] == "SUBARU_OUTBACK_2023"
    assert "Subaru Ascent 2023" in generated_car_list
    assert generated_car_list["Subaru Ascent 2023"]["platform"] == "SUBARU_ASCENT_2023"
    assert "Subaru Crosstrek 2025" in generated_car_list
    assert generated_car_list["Subaru Crosstrek 2025"]["platform"] == "SUBARU_CROSSTREK_2025"
    assert "Subaru Forester 2022-24" not in generated_car_list

  def test_generator(self):
    generated_car_list = json.dumps(get_car_list(), indent=2, ensure_ascii=False)
    with open(CAR_LIST_JSON_OUT) as f:
      current_car_list = f.read()

    assert generated_car_list == current_car_list, "Run opendbc/sunnypilot/car/platform_list.py to update the car list"
