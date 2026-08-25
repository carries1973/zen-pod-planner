# Mapping the ILS structure to the building structure

Written 2026-08-25, from what actually broke while joining the Aug-20 Buildium
rent roll to the Aug-24 ILS feed on this portfolio.

## The mistake to avoid

Everyone — including this map, and including me — starts by assuming these
things nest cleanly:

    property code  ⊃  building  ⊃  door  ⊃  listing

They do not. Every one of those containments is violated by real ZEN data:

| Assumption | Counter-example in this portfolio |
|---|---|
| a code is one building | **SF46** is 8405 *and* 8409 108 Street. **SF175** is 61–83 Fenwyck. **SF337** is 10314, 10316 *and* 10318 147 Street. |
| a building has one code | **18120 28 Ave SW** carries SF313, SF315, SF316, SF318, SF320, SF322, SF323, SF324, SF326, SF328, SF330. |
| a listing is one door | `B1 & B2`, `1 & 2`, `Basement G3 & G4` — one ad, several doors, sold as interchangeable. |
| a listing is one property | `SF318, SF313, SF315, SF316, Sf323, SF324 — 3 Bedroom Townhouse` — one ad, six codes. |
| a door has one record | Rivers Edge **B26** exists twice in Buildium: leased to 2027 under one record, vacant since 2025 under another. |

**Exactly one containment holds:** a door belongs to one building and one
property code. That is the only safe spine.

## The canonical model

Four entities. None of them is a parent of the others; three of them are just
*sets of doors* with their own attributes.

```
DOOR — the grain. One leasable door. The spine.
  door_id          ours, surrogate, stable forever
  scope            SF175            (Buildium's management grouping)
  unit             "63-Upper"       (verbatim, exactly as Buildium spells it)
  building_id      → BUILDING
  status           Rented | Vacant           ← accounting truth, from the roll
  state            vacant | expiring | preleased | leased   ← marketing truth
  avail            date the door is free
  lease_end, rent, ...

BUILDING — a civic address / physical structure. Geography and code compliance.
  address (parsed canonical form), city, postal, lat/lng, pod
  structure_type, legal_suite_status per door   ← see "the other reading" below

SCOPE — Buildium's *management* boundary: owner, PMA, off-boarding.
  code SF175, label as Buildium writes it, owner, offboarding + date
  NOT a place and NOT a door. It is an accounting envelope.

LISTING — a marketing offer.
  ils_unit_id      the ILS "Unit ID"          ← stable primary key
  ils_property_id, platform, status (enabled/disabled)
  headline, advertised_rent, incentive, photos, copy
  → doors[]        MANY-TO-MANY, explicit
```

### The join is a table, not a rule

`listing → door` is many-to-many and **must be stored, not inferred**.
`listing_crosswalk.csv` in this folder is that table:

    ils_unit_id, scope, unit, source, confirmed_on, note

Why stored:

* **The ILS Unit ID is stable** — 225 of 225 rows distinct in the Aug-24 feed.
* **The listing title is not** — only 67 of 225 lead titles still matched a
  live listing title, because titles get edited. Any join built on titles rots.
* **The unit ids genuinely disagree** and no rule fixes it: ILS `G2` vs
  Buildium `Bsmt - G2`; ILS `12228` vs Buildium `12228 - Garden`; ILS `Main`
  vs `10314 Main`; ILS `614`/`411` vs 20 Masters' own scheme.

**Only rows with `confirmed_on` filled are authoritative.** Everything else in
the file is a *proposal* the tool re-derives each run, so a better matcher
improves it and a guess never hardens into evidence. Confirming a pair retires
it permanently. Currently: 0 confirmed, 182 proposed.

## Not losing the advertising requirements

Advertising needs four things the door grain does not have. Force them onto a
door and you lose them.

1. **Availability is a window, not a flag.** `Rented` is not a reason to pull
   an ad. On Aug 20 there were **105 doors** with a lease ending inside 60 days
   and nothing lined up — those are what leasing is selling. Treating
   `Rented ⇒ pull the ad` wrongly condemned **26 ads**, including SF320 unit 45
   whose lease ended four days after the as-of date. Hence `state` and `avail`
   on the door, and a `MARKETING_WINDOW_DAYS` constant (60) that is a parameter,
   not a hard-coded truth.
2. **A listing is a bundle.** "one of these four basement suites" is a real
   offer. Collapse it to a door and you either lose the other three or
   fabricate three ads. Keep the many-to-many.
3. **Advertised rent ≠ contract rent.** The roll's Rent is what a sitting
   tenant pays, and a vacant door has no lease, so **152 of the vacant doors
   have no rent in the roll at all**. Asking rent and incentives ("1 Month
   Free") live on the LISTING. Never impute one from the other.
4. **Marketing content belongs to a floorplan or a building, not a door.**
   Copy, photos, amenities, pet policy are shared across identical doors.

## Not losing the code requirements

The code system is an accounting and PMA boundary, so:

* **Doors carry `(scope, unit)` verbatim.** Never re-key a door because a
  listing groups it differently, and never "tidy" a Buildium unit id.
* **A pin keeps every code that owns doors on it** (`codes[]`), not the
  majority one. Keeping only one took listing-code coverage down to 62 of 144;
  keeping all of them took it to 143 of 144.
* **Off-boarding is a scope-level fact with a date**, and it outranks any
  marketing state: an ad for an off-boarded scope comes down regardless.
* **Display grouping is its own concept.** The map's pin is a fourth thing —
  neither scope nor building — and it must never be allowed to define identity.

## The other reading of "code"

If "building code" means the *Alberta Building Code* rather than the SF code,
the model above holds and gains one field: `legal_suite_status` per door
(legal secondary suite / non-conforming / illegal), on the BUILDING side because
it is a property of the structure, not of the lease. It matters commercially —
a garden or basement suite that is not a legal secondary suite should not be
advertised as a separate dwelling — and this portfolio advertises a lot of
`Garden`, `Bsmt`, `Lower` and `G1..G4` doors. That data is in neither the rent
roll nor the ILS feed, so it would have to come from somewhere else. Say the
word and it gets added as a first-class attribute with its own gate.
