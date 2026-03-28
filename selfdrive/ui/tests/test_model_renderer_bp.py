import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TICI_BP_RENDERER = REPO_ROOT / "selfdrive/ui/bp/onroad/model_renderer_bp.py"
MICI_BP_RENDERER = REPO_ROOT / "selfdrive/ui/bp/mici/onroad/model_renderer_bp.py"


def _parse_renderer(path: Path) -> tuple[str, ast.Module]:
  source = path.read_text(encoding="utf-8")
  return source, ast.parse(source, filename=str(path))


def _get_method(tree: ast.Module, class_name: str, method_name: str) -> ast.FunctionDef:
  for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name == class_name:
      for child in node.body:
        if isinstance(child, ast.FunctionDef) and child.name == method_name:
          return child
  raise AssertionError(f"{class_name}.{method_name} not found")


def test_bp_draw_path_signature_matches_base_renderer():
  for renderer_path in (TICI_BP_RENDERER, MICI_BP_RENDERER):
    _, tree = _parse_renderer(renderer_path)
    draw_path = _get_method(tree, "ModelRendererBP", "_draw_path")
    assert [arg.arg for arg in draw_path.args.args] == ["self"]


def test_bp_renderers_do_not_use_legacy_draw_path_calls():
  for renderer_path in (TICI_BP_RENDERER, MICI_BP_RENDERER):
    source, _ = _parse_renderer(renderer_path)
    assert "_draw_path(sm)" not in source
    assert "super()._draw_path()" in source


def test_tici_bp_renderer_prepares_active_path_style_before_drawing():
  source, _ = _parse_renderer(TICI_BP_RENDERER)

  prepare_idx = source.index("self._prepare_active_path_style(sm)")
  lane_idx = source.index("self._draw_lane_lines()")
  draw_path_idx = source.index("self._draw_path()")

  assert prepare_idx < lane_idx < draw_path_idx
