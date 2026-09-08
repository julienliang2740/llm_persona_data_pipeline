# Refused subjects

A refusal is a finding, and it costs the same research as an admission. Recorded here so the next
person to propose a subject reads the verdict instead of redoing the work.

One file per subject, named `<slug>.md`. No `spec.yaml` — nothing here is a persona, and
`check_persona.py --all` skips these directories because it only walks directories containing a
spec. Each file carries the verdict, the per-criterion evidence, the acquisition passes actually
run, and the sources checked.

A `refuse_acquisition` record is an invitation to try again with a better search. A
`refuse_evidence` record is a claim about the sources, and should only be written once the
escalation ladder in the drafting skill has been exhausted.
