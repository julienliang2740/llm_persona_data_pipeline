"""Institutions to place scenarios in. Data, not prose.

Round-1 families clustered on a handful of settings because the family prompt offered a
short example list and the generator kept reaching for it: three of four Theravada eval
families were the same reception-desk threat. One institution is sampled per slot instead,
so the spread is a property of the plan rather than of the generator's imagination.

Grouped by sector so a coverage plan can vary the sector as well as the name. Deliberately
ordinary and secular: no historical settings, no institution that implies a tradition.
"""

from __future__ import annotations

INSTITUTIONS_BY_SECTOR: dict[str, tuple[str, ...]] = {
    "healthcare": (
        "a community dental practice",
        "a district nursing team",
        "an ambulance dispatch centre",
        "a hospital pharmacy",
        "a residential dementia unit",
        "a fertility clinic",
    ),
    "education": (
        "a further education college",
        "a primary school office",
        "a university admissions team",
        "an after-school club",
        "a driving school",
    ),
    "trades_and_logistics": (
        "a regional parcel depot",
        "a building site",
        "a vehicle recovery firm",
        "a commercial kitchen",
        "a grain co-operative",
        "a scaffolding contractor",
    ),
    "office_and_professional": (
        "a small architecture practice",
        "an insurance claims team",
        "a payroll bureau",
        "a translation agency",
        "a family law firm",
    ),
    "public_and_civic": (
        "a housing benefits office",
        "a parish council",
        "a public library",
        "a planning department",
        "a jobcentre",
        "a coroner's office",
    ),
    "voluntary_and_community": (
        "a food bank",
        "a refugee drop-in centre",
        "an amateur football club",
        "a housing co-operative",
        "a hospice charity shop",
        "a residents' association",
    ),
    "commerce_and_service": (
        "an independent bookshop",
        "a letting agency",
        "a mobile phone repair shop",
        "a wedding venue",
        "a funeral director",
        "a farm shop",
    ),
    "technology_and_platforms": (
        "a content moderation team",
        "a delivery app's driver support desk",
        "a medical records software vendor",
        "a smart meter installer",
        "a genealogy website",
    ),
    "domestic_and_informal": (
        "a shared flat",
        "a family WhatsApp group",
        "a village allotment committee",
        "a school-gate parents' rota",
        "a caravan park",
    ),
}

INSTITUTIONS: tuple[str, ...] = tuple(
    institution for sector in INSTITUTIONS_BY_SECTOR.values() for institution in sector
)

SECTOR_OF: dict[str, str] = {
    institution: sector
    for sector, institutions in INSTITUTIONS_BY_SECTOR.items()
    for institution in institutions
}
