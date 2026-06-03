# ZARA Property Onboarding Template — Master Intake Form
### ZEN Residential · Complete Setup for GHL + ZARA AI Agent + Rentsync + Yardi/RentCafe
*Complete one form per property. All fields required unless marked optional.*
*Form version: 2026-06-03 · Covers: GHL CRM · ZARA AI · Rentsync · Yardi/RentCafe · Kijiji · Rentals.ca*

---

## TABLE OF CONTENTS

- [Section 0 — GHL & System Configuration](#section-0--ghl--system-configuration) ← **Do first**
- [Section 1 — Property Identity](#section-1--property-identity)
- [Section 2 — Contact & Phone Routing](#section-2--contact--phone-routing)
- [Section 3 — Marketing Identity & SEO](#section-3--marketing-identity--seo)
- [Section 4 — Advertising Platform Syndication](#section-4--advertising-platform-syndication) ← **New**
- [Section 5 — Office Hours](#section-5--office-hours)
- [Section 6 — Suite Types & Availability](#section-6--suite-types--availability)
- [Section 7 — What's Included in Rent](#section-7--whats-included-in-rent)
- [Section 8 — Laundry](#section-8--laundry)
- [Section 9 — Parking](#section-9--parking)
- [Section 10 — Storage](#section-10--storage)
- [Section 11 — Pet Policy](#section-11--pet-policy)
- [Section 12 — Building Amenities](#section-12--building-amenities)
- [Section 13 — Application Process](#section-13--application-process)
- [Section 14 — Move-In & Lease Details](#section-14--move-in--lease-details)
- [Section 15 — Neighbourhood & Location](#section-15--neighbourhood--location)
- [Section 16 — Building Rules & Policies](#section-16--building-rules--policies)
- [Section 17 — Incentives & Promotions](#section-17--incentives--promotions)
- [Section 18 — Photos & Visual Media](#section-18--photos--visual-media) ← **New**
- [Section 19 — Escalation](#section-19--escalation)
- [Section 20 — Brand & Tone](#section-20--brand--tone)
- [System Notes for Onboarder](#system-notes-for-onboarder)

---

---

## SECTION 0 — GHL & System Configuration

> **Do this section first.** Everything else — ZARA, briefing emails, calendar booking, pipeline automation — depends on these IDs. The deployment cannot proceed without them.
> Refer to GHL Architecture doc (`ZEN_GHL_Architecture.md`) for full pipeline and custom field specs.

---

### GHL Location

**GHL Location ID:**
*(GHL → Settings → Business Info → Location ID)*
```
GHL_LOCATION_ID=
```

**GHL Private Integration Token (PIT):**
*(GHL → Settings → Integrations → API Keys → Create Private Integration Token)*
```
GHL_API_KEY=pit-
```

**Required PIT Scopes** *(confirm all are checked before saving)*:
- [ ] contacts.readonly
- [ ] contacts.write
- [ ] opportunities.readonly
- [ ] opportunities.write
- [ ] conversations.readonly
- [ ] conversations.write
- [ ] conversations/message.readonly
- [ ] conversations/message.write
- [ ] calendars.readonly
- [ ] calendars/events.write

> ⚠️ **Never use an Agency token.** Must be a property-level Private Integration Token. Conversations scope missing = agent silently fails to read message history.

---

### ZARA Pod Assignment

*(From `ZEN_GHL_Architecture.md` — confirm pod before deploying)*

**City:** _______________________________________________

**Pod Number:** _______________________________________________

**Pod Name:** *(e.g., "Edm Downtown", "Cal SE")* _______________________________________________

**Touring Days for this Pod:** _______________________________________________

**Pod Touring Window** *(times ZARA may offer — e.g., "Tue/Thu 10am–4pm")*: _______________________________________________

**Route Tour Cluster?** *(Does this building participate in a cluster tour pairing?)*  Y  ·  N
If yes, cluster name and partner buildings: _______________________________________________

GHL Custom Field Values to Set:
```
zen_city     =
zen_pod      =
zen_pod_name =
```

---

### Pipeline

**Pipeline Name:** *(confirm exists in GHL or create)*: _______________________________________________

Collect stage IDs via: `GET /opportunities/pipelines?locationId={LOCATION_ID}`

| Stage Name | GHL Stage ID |
|---|---|
| New Lead / Initial Inquiry | `GHL_STAGE_INITIAL=` |
| ZARA Engaged | `GHL_STAGE_ENGAGED=` |
| Qualifying | `GHL_STAGE_QUALIFYING=` |
| Pod Assigned | `GHL_STAGE_POD_ASSIGNED=` |
| Tour Scheduled | `GHL_STAGE_SHOWING_BOOKED=` |
| Toured | `GHL_STAGE_SHOWING_COMPLETE=` |
| Application | `GHL_STAGE_APPLICATION=` |
| Leased | `GHL_STAGE_WON=` |
| Nurture | `GHL_STAGE_NURTURE=` |
| Dead / Lost | `GHL_STAGE_LOST=` |
| Abandoned / Ghosted | `GHL_STAGE_ABANDONED=` |

> ⚠️ **Post-tour hard-block stages** — ZARA must NEVER contact prospects in these stages. List the exact stage names used in this GHL account:
> Hard-blocked: _______________________________________________
> (Minimum: Toured, Application, Leased, Dead/Lost, Abandoned — add Negotiating if used)

---

### Calendars

Collect calendar IDs via: `GET /calendars/?locationId={LOCATION_ID}`

```
GHL_CALENDAR_GROUP_TOUR=        # Pod touring day group calendar
GHL_CALENDAR_1ON1=              # Private / 1-on-1 showing calendar
GHL_CALENDAR_SECOND_TOUR=       # Return visit / second showing
```

**Tour booking slot duration:** _____ minutes

**Buffer between slots:** _____ minutes

---

### Custom Fields — Qualifying

Collect field IDs via: `GET /locations/{LOCATION_ID}/customFields`

```
GHL_FIELD_MOVEIN_DATE=          # Move-in date
GHL_FIELD_BEDROOMS=             # Bedroom preference
GHL_FIELD_BUDGET=               # Budget / max rent
GHL_FIELD_PETS=                 # Pets (Y/N + type)
GHL_FIELD_UNIT_PREFERENCE=      # Unit preferences / notes
```

### Custom Fields — ZARA Geographic & Pod

```
GHL_FIELD_ZEN_CITY=             # zen_city (Edmonton / Calgary / etc.)
GHL_FIELD_ZEN_POD=              # zen_pod (0–15)
GHL_FIELD_ZEN_POD_NAME=         # zen_pod_name (text)
GHL_FIELD_ZEN_TOUR_CLUSTER=     # zen_tour_cluster (if applicable)
```

### Custom Fields — No-Show & Tour

```
GHL_FIELD_NS_RISK=              # ns_risk (high / medium / low)
GHL_FIELD_TOUR_CONFIRMED=       # tour_confirmed (checkbox)
GHL_FIELD_NO_SHOW_COUNT=        # no_show_count (number)
GHL_FIELD_LAST_TOUR_DATE=       # last_tour_date
GHL_FIELD_LAST_TOUR_BUILDING=   # last_tour_building
```

---

### Briefing Email Configuration

**Property Manager Name:** _______________________________________________

**Property Manager Email** *(receives daily ZARA briefing)*: _______________________________________________

**Regional/Overflow Email** *(backup recipient)*: _______________________________________________

```
BRIEFING_TO=propertymanager@,carrie@propertyconsultinggroup.ca
BRIEFING_FROM_EMAIL=info@propertyconsultinggroup.ca
BRIEFING_GMAIL_USER=info@propertyconsultinggroup.ca
BRIEFING_GMAIL_PASS=             # Google App Password — 16 chars, NOT account password
```

> ⚠️ **Google Workspace SMTP requires an App Password.** Generate at: Google Account → Security → 2-Step Verification → App Passwords. NOT the account login password.

---

### Yardi Integration

**Yardi Property Code / PM Database ID:** *(e.g., 326, 358)* _______________________________________________

**RentCafe Site Manager URL:** *(for post-onboarding SEO setup)* _______________________________________________

---

---

## SECTION 1 — Property Identity

**Property Name:** _______________________________________________

**Civic Address (full street address):** _______________________________________________

**Nearest Cross-Street / Intersection** *(Rentsync listing sites use this)*: _______________________________________________

**City:** _______________________________________________

**Province:** _______________________________________________

**Postal Code:** _______________________________________________

**Neighbourhood / Community Name:** _______________________________________________

**Property Timezone** *(circle one)*: Mountain · Pacific · Central · Eastern · Atlantic · Newfoundland

---

**Physical Building Type** *(circle one)*:
Apartment · Condo · Duplex/Triplex · Townhouse · Loft · Home

**Specialty / Geographic Classification** *(check all that apply — Yardi Marketing Type → Specialty)*:
□ Affordable  □ Student  □ City Centre Calgary  □ Central Edmonton  □ Downtown Edmonton
□ East/North/South/West Calgary  □ East/North/South/West Edmonton
□ Sherwood Park  □ St. Albert  □ Saskatchewan  □ None

**Housing Types** *(Rentsync multi-select — affects which listing channels the property is published to)*:
□ Conventional Rental / Family Housing  □ Student Housing  □ Senior Housing  □ Military/Veteran Housing

**Property Classification** *(circle one)*:  A  ·  B  ·  C

---

**Year Built:** _______________________________________________

**Total Number of Units:** _______________________________________________

**Number of Floors:** _______________________________________________

**Ownership / Legal Entity Name** *(e.g., Zen Residential Ltd.)*: _______________________________________________

**Rentsync Accounting Code / GL Code:** _______________________________________________

**Rentsync Listing Permalink / Slug** *(URL path — e.g.,* `/the-parks`*)*: _______________________________________________

**Latitude / Longitude** *(confirm map pin accurate)*: _______________________________________________

**Property Logo** *(file or URL — displayed on Rentsync listing)*: _______________________________________________

---

## SECTION 2 — Contact & Phone Routing

**Primary Leasing Phone:** _______________________________________________

**Listing Phone** *(RentCafe ILS — may be same as above)*: _______________________________________________

**ILS Tracking Phone** *(Yardi syndication tracking number — distinct from leasing line; tracks leads from listing portals)*: _______________________________________________

**Property Fax** *(Yardi — optional)*: _______________________________________________

---

**Primary Leasing Email:** _______________________________________________

**Guest Card / Application Routing Email** *(where GHL guest cards and applications are routed — Yardi)*: _______________________________________________

**Regional / Overflow Leasing Email** *(Yardi)*: _______________________________________________

**Maintenance Email** *(separate from leasing — Rentsync Contact Info + Yardi resident portal)*: _______________________________________________

**Tech Support Phone / Email** *(Yardi resident portal — optional)*: _______________________________________________

---

**Property Website URL:** _______________________________________________

**Tour Booking Link** *(URL for self-scheduled showings — also used by ZARA)*: _______________________________________________

**Online Leasing / Application URL** *(Yardi RentCafe)*: _______________________________________________

**Google Business Profile URL:** _______________________________________________

**Google Maps Listing URL:** _______________________________________________

---

## SECTION 3 — Marketing Identity & SEO

**Short Marketing Tagline** *(≤10 words — Rentsync headline + Yardi Home Page Title)*:
_______________________________________________

**Full Property Marketing Description** *(Yardi Description field + primary listing copy)*:
_______________________________________________
_______________________________________________
_______________________________________________

**Location & Community Details** *(second description block — Rentsync only; neighbourhood narrative separate from building description)*:
_______________________________________________
_______________________________________________

**Rentsync SEO Title** *(≤60 chars)*: _______________________________________________

**Rentsync SEO Meta Description** *(≤160 chars)*: _______________________________________________

*Yardi requires per-page SEO (H1, Title, Meta Description) for ~20 pages. Complete directly in RentCafe Site Manager post-onboarding. The tagline and description above cover the Home page and are the baseline for all others.*

---

## SECTION 4 — Advertising Platform Syndication

> This section controls which channels are activated in Rentsync's syndication network and which platforms require independent content setup.

### Rentsync Syndication — Activate Which Channels?

*(Check all platforms to publish to. Rentsync syndicates automatically once activated. Confirm availability for this property's city/type before enabling.)*

**Primary Platforms:**
□ Kijiji  □ Rentals.ca  □ Zumper  □ Padmapper  □ ViewIt  □ Liv.rent
□ Facebook Marketplace *(via Rentsync integration)*
□ RentCafe ILS *(Yardi — separate setup)*

**Secondary / Niche:**
□ Gottarent  □ RentBoard  □ Point2 Homes  □ HotPads
□ Other: _______________________________________________

**Do NOT activate** *(note any platforms to exclude for this property)*: _______________________________________________

---

### Kijiji

**Activate on Kijiji?**  Y  ·  N

Kijiji content is per floor plan — collected in Section 6 Suite Types table.

| Floor Plan | Kijiji Catch Phrase *(≤64 chars)* | Kijiji Description *(≤2,000 chars)* |
|---|---|---|
| Studio | | |
| 1 Bedroom | | |
| 2 Bedroom | | |
| 3 Bedroom | | |
| Other: _______ | | |

---

### Rentals.ca

**Activate on Rentals.ca?**  Y  ·  N

**Rentals.ca Property Contact Name** *(may differ from leasing line)*: _______________________________________________

**Any Rentals.ca–specific copy or requirements for this property?**: _______________________________________________

---

### Facebook Marketplace / Social

**Activate Facebook Marketplace?**  Y  ·  N

**Facebook Page URL** *(if applicable)*: _______________________________________________

**Instagram Handle** *(if applicable)*: _______________________________________________

---

### Lead Source Tracking

*(Used in GHL to tag where each lead came from — needed for ZARA attribution and briefing accuracy)*

**Lead source names used in GHL for this property** *(run `GET /contacts/?locationId=...` to verify — source naming conventions differ per property)*:
_______________________________________________

**UTM parameters in use?**  Y  ·  N
If yes, document: _______________________________________________

---

## SECTION 5 — Office Hours

*(Must be day-by-day — Yardi requires structured time fields; ZARA needs this to answer "are you open Saturday?" accurately.)*

| Day | Open? | Open Time | Close Time |
|---|---|---|---|
| Monday | Y · N | _______ AM/PM | _______ AM/PM |
| Tuesday | Y · N | _______ AM/PM | _______ AM/PM |
| Wednesday | Y · N | _______ AM/PM | _______ AM/PM |
| Thursday | Y · N | _______ AM/PM | _______ AM/PM |
| Friday | Y · N | _______ AM/PM | _______ AM/PM |
| Saturday | Y · N | _______ AM/PM | _______ AM/PM |
| Sunday | Y · N | _______ AM/PM | _______ AM/PM |

**Showings offered outside office hours?**  Y  ·  N  · With advance notice: _______________

**Additional hours message** *(appended to display — e.g., "Showings by appointment on holidays")*: _______________________________________________

---

## SECTION 6 — Suite Types & Availability

*(Do NOT enter specific unit rents — those come from Yardi. Enter market rent ranges only.)*

| Suite Type | Sq Ft Range | Market Rent Range | Den? (Y/N) | Available? | Orientation | Furnishing |
|---|---|---|---|---|---|---|
| Studio | | | | Y · N | | Furnished · Semi · Unfurnished |
| 1 Bedroom | | | | Y · N | N/NE/E/SE/S/SW/W/NW | Furnished · Semi · Unfurnished |
| 2 Bedroom | | | | Y · N | N/NE/E/SE/S/SW/W/NW | Furnished · Semi · Unfurnished |
| 3 Bedroom | | | | Y · N | N/NE/E/SE/S/SW/W/NW | Furnished · Semi · Unfurnished |
| Other: _______ | | | | Y · N | N/NE/E/SE/S/SW/W/NW | Furnished · Semi · Unfurnished |

---

**Deposit Type** *(Rentsync stores as formula, not dollar amount — circle per suite type or property-wide)*:
None · Half Month's Rent · One Month's Rent · Two Months' Rent · Other: _______________

*(Dollar amounts go in Yardi — see Section 13 Application Process)*

**Unit Features:**  □ Luxury  □ Executive  □ Waterfront

**Renovation Status** *(default)*: Ready · Under Repair · To Be Assessed · To Be Repaired

**Hydro Rate** *(if separately metered per unit)*: $_____/unit

---

**Lease Terms Available:**
□ 1 mo  □ 2 mo  □ 3 mo  □ 6 mo  □ 9 mo  □ 12 mo  □ Other: _______

**Default Lease Term:** _______________________________________________

**Minimum Lease Term** *(for ZARA)*: _______________________________________________

**Waitlist Policy:** _______________________________________________

> ⚠️ *Rentsync Limitation: Lease term dropdown supports up to "One Year" only. Terms of 13, 18, or 24 months cannot be stored as structured data in Rentsync — must go in description copy. Flag non-standard terms:* _______________________________________________

---

**Per Floor Plan — ILS Marketing Copy**

| Floor Plan | Marketing Description *(≤1,000 chars)* | Kijiji Catch Phrase *(≤64 chars)* | Kijiji Description *(≤2,000 chars)* |
|---|---|---|---|
| Studio | | | |
| 1 Bedroom | | | |
| 2 Bedroom | | | |
| 3 Bedroom | | | |

---

## SECTION 7 — What's Included in Rent

**Utilities Included?** *(Rentsync master toggle)*: Yes · No

*If Yes, check all that apply:*

**Basic Utilities:**  □ Heat  □ Water  □ Electricity  □ Gas  □ Sewage  □ Garbage Collection

**Ancillary:**  □ Internet  □ Cable  □ Phone

**Other:**  □ Recycling  □ On-site laundry access

**Tenant pays separately:** _______________________________________________

*Yardi handles utility inclusions through amenity checkboxes and floor plan descriptions — no single toggle. Ensure amenity flags and descriptions reflect these inclusions.*

---

## SECTION 8 — Laundry

**Laundry type** *(circle one)*:
In-suite washer/dryer · In-suite hookups only · Shared laundry room (coin) · Shared laundry room (card) · No laundry on site

**Amenity Mapping** *(check all that apply)*:
□ Washer in suite  □ Dryer in suite  □ W/D Hookups only  □ Dishwasher  □ Laundry facilities (shared)

**Cost per load** *(if shared)*: $_______

**Number of machines** *(washer / dryer)*: _______________________________________________

**Location of shared laundry:** _______________________________________________

---

## SECTION 9 — Parking

**Is parking available?**  Y  ·  N

| Parking Type | Available? | Monthly Rate | # of Stalls |
|---|---|---|---|
| Underground | Y · N | $_______ | _______ |
| Indoor | Y · N | $_______ | _______ |
| Covered | Y · N | $_______ | _______ |
| Garage | Y · N | $_______ | _______ |
| Outdoor / Surface | Y · N | $_______ | _______ |
| Street | Y · N | $_______ | _______ |
| Electric / EV | Y · N | $_______ | _______ |
| Valet | Y · N | $_______ | _______ |

**Total parking spots (building-wide):** _______

**Stalls per unit allowed:** _______

**Tandem / parallel stalls?**  Y · N

**Visitor parking?**  Y · N

**Parking included in rent or billed separately?** _______________________________________________

**Availability:** Always available · Limited · Waitlist

**Other parking details** *(heated, access card, assignment process)*: _______________________________________________

---

## SECTION 10 — Storage

**Storage available?**  Y · N

**Included in rent?**  Y · N

**Monthly rate per locker:** $_______
*(Rentsync stores at unit level — not property level. This rate will be applied per unit.)*

**Size / type:** _______________________________________________

**Total storage spaces:** _______

**Availability:** Always · Limited · Waitlist

---

## SECTION 11 — Pet Policy

**Pets Allowed?**
Rentsync *(circle)*: Yes · No · Cats Only
Yardi *(circle)*: Dogs Allowed · Cats Allowed · Pet Friendly · Not Allowed

| Pet Type | Allowed? | One-Time Deposit ($) | Monthly Pet Fee ($) | One-Time Fee ($) | Max Weight (lbs) | Breed Restrictions |
|---|---|---|---|---|---|---|
| Cats | Y · N | $_______ | $_______ | $_______ | N/A | _______ |
| Small Dogs | Y · N | $_______ | $_______ | $_______ | ≤_____ lbs | _______ |
| Large Dogs | Y · N | $_______ | $_______ | $_______ | ≤_____ lbs | _______ |

**Rentsync Pet Checkboxes:**  □ Cats  □ Small Dogs  □ Large Dogs

**Max pets per unit:** _______

**Other pet rules:** _______________________________________________

**Custom Pet Policy Text** *(for website / listing — must include weight limit, breed restrictions, and monthly fee since Rentsync has no structured fields for these)*:
_______________________________________________
_______________________________________________

---

## SECTION 12 — Building Amenities

**Community / Property Amenities:**

□ Fitness centre / gym  □ Free weights  □ Group exercise / yoga classes
□ Pool  □ Hot tub / spa  □ Sauna  □ Steam room
□ Outdoor patio / courtyard  □ BBQ / picnic area  □ Rooftop terrace  □ Sundeck
□ Party / events room  □ Recreation room  □ Clubhouse
□ Co-working / study lounge  □ Business centre  □ Media room  □ Library  □ Guest suite
□ Concierge / front desk  □ 24/7 concierge  □ 24/7 emergency service  □ Door attendant
□ On-site management  □ On-site maintenance
□ Night patrol / security staff  □ Security cameras / surveillance
□ Security fob / controlled access  □ Keyless entry
□ Elevator  □ Accessible units available
□ Bike storage  □ Package lockers *(brand)*: _______________________
□ EV charging stations
□ Dog wash station  □ Dog run / off-leash area
□ Playground  □ Child care
□ Recycling  □ Green building certification  □ Historic designation
□ Visitor parking  □ Covered parking  □ Off-street parking  □ Garage
□ Short-term lease available  □ Furnished units available
□ High-speed internet in common areas
□ Basketball court  □ Tennis court  □ Volleyball court  □ Racquetball court
□ Meal service  □ Housekeeping service  □ Club discount program
□ Other: _______________________________________________

**Nearby Amenities** *(Rentsync structured checkboxes)*:
□ Beach nearby  □ Convenience store  □ Parks nearby  □ Public transit  □ Schools nearby  □ Shopping nearby

---

**Unit / Apartment Amenities:**

□ Air conditioner  □ Central air conditioning
□ In-suite washer / dryer  □ W/D hookups only  □ Dishwasher  □ Microwave
□ Refrigerator  □ Gas range  □ Garburator  □ Efficient appliances
□ Fireplace  □ Individual / electronic thermostat
□ Hardwood floors  □ Vinyl plank  □ Ceramic / tile  □ Carpet
□ High ceilings  □ Large closets  □ Walk-in closet  □ Ensuite bathroom
□ Balcony  □ Skylight
□ City view  □ Park view  □ Waterfront view
□ Window coverings / blinds included
□ Cable included  □ Cable ready  □ Internet included  □ Internet ready
□ Security alarm  □ Extra storage in unit  □ Ceiling fan  □ Handrails
□ Other: _______________________________________________

**Amenities currently out of service or seasonal** *(note expected return date)*: _______________________________________________

---

## SECTION 13 — Application Process

**Application fee** *(if any)*: $_______

**Security / damage deposit:** _______________________________________________

**Deposit dollar range per floor plan** *(for Yardi — Min/Max)*:
Studio: $_____ – $_____   1BR: $_____ – $_____   2BR: $_____ – $_____   3BR: $_____ – $_____

**Documents required to apply:** _______________________________________________

**How do prospects apply?** *(portal URL / in person / email)*: _______________________________________________

**Typical approval timeline:** _______________________________________________

**Co-signers / guarantors accepted?**  Y · N

**Students accepted?**  Y · N · With conditions: _______________________________________________

**Minimum income requirement:** _______________________________________________

**Credit check requirements:** _______________________________________________

**Background screening agency** *(name / URL — for Yardi Third Party Screening config)*: _______________________________________________

**Occupancy limits** *(Yardi Guest Card Settings)*:
Studio: max ___ occupants   1BR: max ___   2BR: max ___   3BR: max ___

**Max pets per application** *(Yardi)*: _______

**eSignature of lease available?**  Y · N

---

## SECTION 14 — Move-In & Lease Details

**Move-in fee** *(if any)*: $_______

**Pro-rated first month?**  Y · N

**Key / fob deposit:** $_______

**Move-in inspection process:** _______________________________________________

**Elevator booking required for move-in?**  Y · N

**Move-in / move-out blackout days** *(Yardi can exclude specific days)*: _______________________________________________

---

## SECTION 15 — Neighbourhood & Location

**Nearest transit stop and walking distance:** _______________________________________________

**Nearest grocery store and distance:** _______________________________________________

**Nearest school(s) and distance:** _______________________________________________

**Nearest major employer or institution:** _______________________________________________

**Other nearby landmarks** *(up to 5 — gyms, hospitals, entertainment)*: _______________________________________________

**Walk Score** *(if known)*: _______

**Transit Score** *(if known)*: _______

**WalkScore URL** *(for Yardi Maps & Directions — optional)*: _______________________________________________

*Walk Score and Transit Score are not native fields in Rentsync or Yardi — manually entered wherever displayed. Neither system auto-populates these.*

**Neighbourhood character** *(e.g., quiet residential, walkable, young professionals)*: _______________________________________________

---

## SECTION 16 — Building Rules & Policies

**Smoking policy** *(circle)*: No smoking anywhere · Designated outdoor areas only · Other: _______________

**Cannabis policy:** _______________________________________________

**Quiet hours:** _______________________________________________

**Guest policy** *(overnight guests, long-term guests)*: _______________________________________________

**Balcony / patio rules:** _______________________________________________

**Other rules prospects ask about frequently:** _______________________________________________

---

## SECTION 17 — Incentives & Promotions

> ⚠️ **Critical:** Rentsync and Yardi manage promotions in separate, incompatible systems. They cannot sync automatically — must be entered and maintained independently in each system.
>
> **ZARA rule:** Incentives are NEVER shared with a prospect until move-in date is confirmed. Do NOT enter incentive amounts in the ZARA system prompt. ZARA says: "Once you confirm your move-in date, I can share what's available at that time."

**Does ZEN offer move-in incentives for this property?**  Y · N

**Form they take** *(free months / reduced deposit / gift card / other)*: _______________________________________________

| Promotion | Rentsync Setup | Yardi Setup |
|---|---|---|
| Promotion Title | _______ | _______ |
| Category | Free Rent · Reduced Deposit · Other | _______ |
| # of Free Months | _______ | _______ |
| Recommended Lease Length | _______ | _______ |
| Amount ($) | N/A | $_______ |
| Concession Charge Type | N/A | PCO · PFC · RCO · SCO |
| Promo Code | N/A | _______ |
| Start Date | _______ | _______ |
| End Date | _______ | _______ |

*Add rows for each active promotion. If no active promotion at time of onboarding, document the framework only.*

**How are internal staff informed when incentives change?** _______________________________________________

---

## SECTION 18 — Photos & Visual Media

> Photos are required on every platform before publishing. Missing photos = listings suppressed or ranked lower on Kijiji, Rentals.ca, and Rentsync. Collect these before go-live.

### Photo Requirements by Platform

| Platform | Min Photos | Max Photos | Preferred Format | Notes |
|---|---|---|---|---|
| Rentsync | 5 | 40 | JPG/PNG, min 1200×800 | Uploaded per suite type |
| Yardi / RentCafe | 5 | 50 | JPG/PNG, min 1024×768 | Uploaded per floor plan + per amenity |
| Kijiji | 1 | 24 | JPG, max 5MB each | Per listing/floor plan |
| Rentals.ca | 3 | 30 | JPG/PNG | Per property |

---

### Photo Checklist — Provide at Minimum

**Exterior:**
□ Front of building (daytime)
□ Front of building (evening / night, if possible)
□ Building entrance / lobby
□ Signage

**Suites** *(one full set per suite type — Studio, 1BR, 2BR, 3BR)*:
□ Living room
□ Kitchen
□ Primary bedroom
□ Secondary bedroom *(if applicable)*
□ Bathroom(s)
□ Balcony / outdoor space *(if applicable)*
□ Closet / storage space

**Amenities** *(one photo per amenity that exists)*:
□ Fitness centre / gym
□ Pool / hot tub / sauna
□ Common lounge / party room
□ Outdoor patio / courtyard / BBQ area
□ Bike storage
□ Package room / lockers
□ Parking (underground / covered)
□ Dog wash station / dog run *(if applicable)*
□ Laundry room *(if shared)*

---

### Photo Submission

**How are photos being submitted?** *(circle)*:
Google Drive link  ·  Dropbox link  ·  WeTransfer  ·  Direct upload  ·  Other

**Link / location:** _______________________________________________

**Photo credit / attribution** *(required for some ILS platforms)*: _______________________________________________

---

### Video & Virtual Tour

**Video tour available?**  Y · N

**Video URL** *(YouTube / Vimeo — used in Yardi and Rentsync)*: _______________________________________________

**3D / Virtual tour available?** *(e.g., Matterport)*  Y · N

**Virtual tour URL:** _______________________________________________

*Yardi RentCafe supports embedding video and virtual tour links at the floor plan level. Rentsync embeds at the property level.*

---

## SECTION 19 — Escalation

**Situations ZARA must always escalate to a human** *(examples: legal complaints, accommodation requests, media inquiries, aggressive prospects, prospects who have been contacted 3+ times with no response)*:
_______________________________________________
_______________________________________________

**Who does ZARA say will follow up?** *(exact name / role — e.g., "your leasing advisor")*: _______________________________________________

**Escalation contact name:** _______________________________________________

**Escalation contact direct phone:** _______________________________________________

**Escalation contact email:** _______________________________________________

**Hours escalation contact is reachable:** _______________________________________________

**After-hours emergency contact** *(maintenance / urgent — separate from leasing)*: _______________________________________________

---

## SECTION 20 — Brand & Tone

**In one sentence, what makes this property special?** *(ZARA's opening pitch — be specific, not generic)*:
_______________________________________________

**Who is the typical resident?** *(demographic, lifestyle, what brought them here)*:
_______________________________________________

**Demographic adaptation note** *(ZARA adjusts tone by class automatically — confirm any property-specific adjustments)*:
Class A (this property): _______________________________________________
Class B/C adjustment: _______________________________________________

**Anything ZARA must NEVER say about this property** *(past incidents, competitor comparisons, anything off-limits)*:
_______________________________________________

**What do competitors say that ZARA should be prepared to address?**
_______________________________________________

**Lingo bans** *(words/phrases ZARA must not use — e.g., "come in", "cheap", "affordable")*:
_______________________________________________

---

---

## SYSTEM NOTES FOR ONBOARDER

*Do not fill in — reference during data entry.*

| Topic | Rentsync | Yardi/RentCafe | GHL / ZARA | Action |
|---|---|---|---|---|
| Phone numbers | 1 field | 3 fields (Property, Listing, ILS Tracking) | N/A | Enter all 3 in Yardi; confirm which goes in Rentsync |
| Email routing | Contact + Maintenance email | Property + Guest Card + Regional Leasing email | BRIEFING_TO | Enter all — map separately per system |
| Lease terms | Fixed dropdown (max 12 months) | 1–36 month checkboxes | ZARA knows from system prompt | 13+ month terms go in description copy in Rentsync |
| Deposits | Type/formula per unit (no $ amount) | Dollar range (Min/Max) per floor plan | N/A | $ amounts Yardi only |
| Pet financials | Cats/Small/Large checkboxes + 1 deposit field | Per-type structured fields (deposit, rent, fee, weight, breed) | ZARA knows full policy from KB | Full detail required for Yardi; put weight/breed/fee in Rentsync description |
| Office hours | Single rich-text field | Structured day-by-day | ZARA uses structured hours from system prompt | Collect day-by-day (Section 5) — all three need it |
| Promotions | Standalone marketing entries | Voyager concession records with charge codes | ZARA never quotes until move-in confirmed | Enter separately in each system — cannot sync |
| Amenities | Name only | Name + display name + description + images | ZARA lists from KB | Marketing copy per amenity in Yardi; also put in Rentsync description |
| Furnishing | Unit-level status | Floor plan-level type | N/A | "Part Furnished" (Yardi) ≈ "Semi Furnished" (Rentsync) |
| Den | Explicit toggle per unit | Floor plan name convention (e.g., "1 Bed + Den") | N/A | Names may not sync — confirm floor plan naming with Yardi PM |
| Walk Score | No native field | Toggle + URL in Maps & Directions | ZARA quotes from KB | Manual entry in both; always collect at onboarding |
| SEO | Property-level only | Per-page H1 + Title + Meta for ~20 pages | N/A | Complete per-page SEO directly in RentCafe Site Manager post-onboarding |
| Laundry | No dedicated field — amenity flags | Standard amenity checkboxes | ZARA describes from KB | Map laundry type to amenity flags per Section 8 |
| Storage rates | Unit-level (not property-level) | Rentable Items module | N/A | Rate entered per unit in Rentsync; stall inventory in Yardi Rentable Items |
| Photos | Uploaded per suite type | Per floor plan + per amenity | N/A | Collect before go-live — see Section 18. Missing photos = suppressed listings |
| GHL Location ID | N/A | N/A | Foundation of all automation | Collect first — everything else depends on it |
| Pipeline stage IDs | N/A | N/A | Required for stage moves and hard-block list | Collect via API before deploying ZARA |
| Pod assignment | N/A | N/A | zen_pod + zen_city required at first run | Set custom fields immediately after GHL setup |
| Post-tour hard-block | N/A | N/A | Stage names must match exact GHL stage names | Mismatches caused Negotiating contacts to get ZARA outreach (Angela Gomez incident) |
| Tags behaviour | N/A | N/A | PUT /contacts replaces all tags — always fetch + merge | Never send partial tags array |
| Email threading | N/A | N/A | GHL collapses threads — must call expandEmailThread() | Without this, ZARA reads wrong sender's words |
| Kijiji content | Via Rentsync syndication | Via Yardi ILS | N/A | Collect per floor plan in Section 4 / Section 6 |
| Lead source names | N/A | N/A | Differ per property — verify before briefing goes live | Run GET /contacts to confirm source values |

---

*Form version: 2026-06-03*
*Architecture reference: `zen-pod-deploy/ZEN_GHL_Architecture.md`*
*Conversation flow: `zen-pod-deploy/ZARA_GHL_Geographic_Qualification_Flow.md`*
*GHL deployment gotchas: COWORK Leasing Agent Template memory (`project_cowork_leasing_agent_template.md`)*
