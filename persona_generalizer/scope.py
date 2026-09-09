"""Which subjects are out of scope regardless of how much evidence survives.

The sufficiency gate answers "is there enough material?". This answers a different question:
"should a faithful persona of this subject be built at all?" — and it is not a question the
evidentiary criteria can reach, because the subjects it excludes are among the best documented
people who have ever lived, and pass every criterion in the gate comfortably.

The schema already had exactly one rule on this axis — living private individuals, refused
"regardless of evidence volume" — with no verdict name and no enforcement. This generalises that
rule rather than inventing a new category, and gives it the verdict `refuse_scope`.

**The category.** A persona spec is a fidelity-maximising artefact. It carries no
modern-constraint clause by design, `divergence_hypotheses` deliberately enumerates where the
subject departs from ordinary assistant ethics, and the export is fine-tuning data. For most
subjects that is the point: LBJ's unattractive half is electoral fraud and twenty years of
segregationist votes, and a spec that softened it would be a different and less useful person.
The exclusion is narrower than "did terrible things". It is for subjects whose *distinctive value
content* — the thing that makes them a persona rather than a generic contemporary — is the
direction or advocacy of mass atrocity. There, the faithful rendering and the harmful artefact
are the same object, and there is no version where the objectionable part is a wart on something
else.

**What this module is and is not.** `TRIPWIRE` is a cheap stop for unambiguous cases, so a script
does not spend money on acquisition before anyone looks. It is deliberately short and it is not a
filter: it is trivially evaded by a spelling, and it says nothing about the many subjects that
need an actual judgement. That judgement stays with the researcher and is recorded in
`sufficiency.scope_check`, which `check_persona.py` requires on every admitted spec. The point of
requiring the field is that the question gets asked once, in writing, by a person — not that a
list decides it.
"""

from __future__ import annotations

import re
import unicodedata

SCOPE_VERDICT = "refuse_scope"

# Unambiguous instances, as normalised substrings. Short on purpose: every entry should be a case
# where the distinctive value content is the atrocity itself, and where no reviewer would expect
# the pipeline to proceed without a human first saying so out loud.
TRIPWIRE: tuple[tuple[str, str], ...] = (
    ("adolf hitler", "directed the Holocaust; the distinctive ideological content is the atrocity"),
    ("heinrich himmler", "organised and directed the extermination programme"),
    ("joseph goebbels", "directed the propaganda apparatus of the extermination programme"),
    ("reinhard heydrich", "chaired the Wannsee conference and directed the Einsatzgruppen"),
    ("pol pot", "directed the Cambodian genocide"),
    ("radovan karadzic", "convicted of genocide at Srebrenica"),
    ("otto strasser", "Strasserism is a live recruitment ideology whose core content is racial-nationalist antisemitism"),
    ("gregor strasser", "as above; the distinctive content is the ideological current, not the man"),
)

# Also refused on this axis, and the rule that was already in the schema before this module.
LIVING_PRIVATE_INDIVIDUAL = (
    "Living private individuals are out of scope regardless of how much material exists. Public "
    "figures, historical subjects and fictional characters are in."
)


def _normalise(value: str) -> str:
    """Casefold, strip accents and collapse punctuation, so trivial variants still match."""
    decomposed = unicodedata.normalize("NFKD", value)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", stripped.casefold()).strip()


def tripwire_match(subject: str) -> tuple[str, str] | None:
    """Return (matched entry, why) when a subject hits the tripwire, else None.

    Matching is on whole tokens, unordered: every token of the entry must appear as a token of
    the subject. Ordered substrings missed the inverted "surname, forename" form, which is simply
    how a catalogue or an index writes a name, and a tripwire defeated by comma order is not worth
    having. Requiring *all* tokens keeps it tight enough that an unrelated subject sharing one
    surname is unaffected.
    """
    tokens = set(_normalise(subject).split())
    for needle, why in TRIPWIRE:
        if set(needle.split()) <= tokens:
            return needle, why
    return None


def refusal_message(subject: str, needle: str, why: str) -> str:
    return (
        f"{subject!r} is out of scope for a persona target ({SCOPE_VERDICT}).\n"
        f"  matched: {needle} — {why}\n"
        f"  A persona spec is fidelity-maximising: it carries no modern-constraint clause, its\n"
        f"  divergence hypotheses enumerate where the subject departs from ordinary ethics, and\n"
        f"  the export is fine-tuning data. Where the subject's distinctive value content is the\n"
        f"  atrocity itself, the faithful rendering and the harmful artefact are the same object.\n"
        f"  See persona_generalizer/scope.py for the category and its limits, and record the\n"
        f"  refusal in persona_generalizer/personas/_refused/.\n"
        f"  This is a tripwire for unambiguous cases, not a filter. Subjects it does not name\n"
        f"  still need the judgement recorded in sufficiency.scope_check."
    )
