"""The template target must stay a valid, strict-mode spec, and `main.py check` must
report problems instead of a traceback."""

from __future__ import annotations

import shutil
from pathlib import Path

import main as cli
from pipeline.target import load_target

TARGETS = Path("targets")


def test_template_loads_in_strict_mode():
    spec = load_target(TARGETS, "_template", strict=True)
    assert spec.target_id == "_template"
    assert len(spec.principles) >= 3
    assert spec.raw.get("deliberation_shape")
    assert spec.raw.get("signature_moves")


def test_check_command_passes_on_template(capsys):
    assert cli.check_target(TARGETS, "_template") == 0
    out = capsys.readouterr().out
    assert "OK (strict)" in out
    assert "all cited ids resolve" in out


def test_check_command_reports_a_bad_passage_id(tmp_path, capsys):
    broken = tmp_path / "broken"
    shutil.copytree(TARGETS / "_template", broken)
    spec = (broken / "spec.yaml").read_text(encoding="utf-8")
    spec = spec.replace("id: _template", "id: broken").replace("sources: [TT 1.2]", "sources: [TT 9.9]")
    (broken / "spec.yaml").write_text(spec, encoding="utf-8")
    assert cli.check_target(tmp_path, "broken") == 2
    err = capsys.readouterr().err
    assert "TT 9.9" in err and "NOT OK" in err


def test_every_real_target_passes_strict_check():
    for target_id in ("confucian", "catholic", "protestant", "theravada"):
        assert cli.check_target(TARGETS, target_id) == 0
