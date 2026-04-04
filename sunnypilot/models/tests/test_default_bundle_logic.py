from types import SimpleNamespace

from openpilot.sunnypilot.models.helpers import (
  DEFAULT_MODEL_BUNDLE_SHORT_NAME,
  get_builtin_stock_model_name,
  get_builtin_stock_option_label,
  get_default_bundle,
  should_auto_queue_default_bundle,
)


def test_get_default_bundle_finds_nnmv2():
  bundles = [
    SimpleNamespace(internalName="CHV2"),
    SimpleNamespace(internalName=DEFAULT_MODEL_BUNDLE_SHORT_NAME),
  ]

  assert get_default_bundle(bundles).internalName == DEFAULT_MODEL_BUNDLE_SHORT_NAME


def test_builtin_stock_label_is_derived_from_current_header_name():
  builtin_stock_name = get_builtin_stock_model_name()

  assert builtin_stock_name == "CD210"
  assert get_builtin_stock_option_label() == f"Built-in Stock ({builtin_stock_name})"


def test_should_auto_queue_default_bundle_only_when_expected():
  assert should_auto_queue_default_bundle(
    is_offroad=True,
    has_active_bundle=False,
    use_builtin_stock=False,
    download_index=None,
    default_bundle_available=True,
  ) is True

  assert should_auto_queue_default_bundle(
    is_offroad=False,
    has_active_bundle=False,
    use_builtin_stock=False,
    download_index=None,
    default_bundle_available=True,
  ) is False

  assert should_auto_queue_default_bundle(
    is_offroad=True,
    has_active_bundle=True,
    use_builtin_stock=False,
    download_index=None,
    default_bundle_available=True,
  ) is False

  assert should_auto_queue_default_bundle(
    is_offroad=True,
    has_active_bundle=False,
    use_builtin_stock=True,
    download_index=None,
    default_bundle_available=True,
  ) is False

  assert should_auto_queue_default_bundle(
    is_offroad=True,
    has_active_bundle=False,
    use_builtin_stock=False,
    download_index=38,
    default_bundle_available=True,
  ) is False

  assert should_auto_queue_default_bundle(
    is_offroad=True,
    has_active_bundle=False,
    use_builtin_stock=False,
    download_index=None,
    default_bundle_available=False,
  ) is False
