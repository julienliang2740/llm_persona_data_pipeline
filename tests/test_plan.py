

# -------------------------------------------------------------------------------------------
# Principle coverage. The plan assigns which principles a family must put under pressure,
# because leaving it to the generator does not distribute: on a real 16-family run two of
# fourteen principles were applied in 97% of responses and four were never applied at all.
# -------------------------------------------------------------------------------------------


def _principle_spec(n_principles=14):
    from tests.conftest import REPO_ROOT
    from pipeline.target import load_target

    return load_target(REPO_ROOT / "persona_generalizer" / "personas", "lbj", strict=True)


BASE_SETTINGS = {
    "counterfactual_fraction": 0.3,
    "divergence_fraction": 0.5,
    "eval_family_fraction": 0.25,
    "held_out_tradeoffs": 1,
}


def test_principles_are_not_assigned_unless_the_floor_is_configured():
    """Off by default: every target planned before this existed must plan identically."""
    from pipeline import plan as P

    spec = _principle_spec()
    slots = P.plan_families(spec, dict(BASE_SETTINGS), 16)
    assert sum(len(s.principle_ids) for s in slots) == 0


def test_every_principle_gets_a_family_when_the_floor_is_set():
    from pipeline import plan as P
    from collections import Counter

    spec = _principle_spec()
    settings = dict(BASE_SETTINGS, principle_coverage_floor=1.0, principles_per_family=2)
    slots = P.plan_families(spec, settings, 16)
    counts = Counter(pid for s in slots for pid in s.principle_ids)
    all_ids = [p["id"] for p in spec.principles]
    assert set(counts) == set(all_ids), "a principle with no family is never exercised"
    # Round robin, so the spread should be flat to within one.
    assert max(counts.values()) - min(counts.values()) <= 1


def test_the_spread_stays_flat_at_scale():
    from pipeline import plan as P
    from collections import Counter

    spec = _principle_spec()
    settings = dict(BASE_SETTINGS, principle_coverage_floor=1.0, principles_per_family=2)
    counts = Counter(
        pid for s in P.plan_families(spec, settings, 100) for pid in s.principle_ids
    )
    assert max(counts.values()) - min(counts.values()) <= 1


def test_a_starved_principle_is_reported_by_the_plan_check():
    from pipeline import plan as P

    spec = _principle_spec()
    settings = dict(BASE_SETTINGS, principle_coverage_floor=1.0, principles_per_family=2)
    slots = P.plan_families(spec, settings, 120)
    # Strip one principle from every slot and the checker should notice it is uncovered.
    victim = spec.principles[0]["id"]
    for slot in slots:
        slot.principle_ids = [p for p in slot.principle_ids if p != victim]
    problems = P.check_plan(spec, slots, settings)
    assert any(victim in str(p) and "principle" in str(p) for p in problems)
