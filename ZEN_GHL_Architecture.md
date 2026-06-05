# ZEN Residential — GHL Architecture & Pod Reference
**Last updated: June 2026 · 84 properties · 6,212 units · 867 vacant**

---

## TABLE OF CONTENTS

- [Part A — Master Building → Pod Mapping](#part-a--master-building--pod-mapping)
- [Part B — GHL Setup Architecture](#part-b--ghl-setup-architecture)
  - [1. Account Structure](#1-account-structure)
  - [2. Pipeline Stages](#2-pipeline-stages)
  - [3. Custom Fields](#3-custom-fields)
  - [4. ZARA Bot Configuration](#4-zara-bot-configuration)
  - [5. Lead Routing — Geographic Qualification Flow](#5-lead-routing--geographic-qualification-flow)
  - [6. Confirmation Sequence Workflows](#6-confirmation-sequence-workflows)
  - [7. No-Show Risk Scoring & Re-engage](#7-no-show-risk-scoring--re-engage)
  - [8. Pod Touring Calendar](#8-pod-touring-calendar)
  - [9. Cluster Tour Pairings](#9-cluster-tour-pairings)
  - [10. Implementation Checklist](#10-implementation-checklist)

---

---

# PART A — MASTER BUILDING → POD MAPPING

> **Source of truth for all pod assignments. Unit counts verified against notebook June 2026.**
> Buildings with no vacancy data = 0 current vacancies.
> ⚠️ = flag requiring follow-up (see notes column).

---

## EDMONTON — 5 Active Pods

### Pod 0 · Edm Downtown · Mon / Wed / Fri
**22 properties · 1,011 units · 178 vacant now**

| Building | Units | Vacant | Type | Notes |
|---|---|---|---|---|
| Chicklet House | 10 | 6 | Mid Rise | |
| Chrysalis | 24 | 1 | Low Rise | |
| Collage Place | 20 | 0 | Low Rise | |
| Crestmark Place | 24 | 0 | Low Rise | |
| Greenstone Park | 20 | 3 | Mid Rise | |
| Hamlet Village | 8 | 1 | Mid Rise | |
| House Acadian | 21 | 9 | Mid Rise | |
| Kerry Manor | 22 | 4 | Low Rise | |
| Lorinda Court | 20 | 2 | Mid Rise | |
| Mid City Manor | 26 | 5 | Low Rise | |
| Monarch Manor | 34 | 2 | Low Rise | |
| Norwood Village | 154 | 8 | Mid Rise | |
| Oakwood Manor | 11 | 4 | Mid Rise | |
| Palisades | 15 | 6 | Mid Rise | |
| Richard House | 22 | 3 | Low Rise | |
| Rivergate | 9 | 6 | Mid Rise | |
| Royal Lady | 39 | 11 | Mid Rise | |
| Royal Manor | 12 | 3 | Mid Rise | |
| The Edward Block | 161 | 21 | Mid Rise | Not in notebook — unit count unverified |
| The Parks | 241 | 73 | High Rise | |
| The Residence | 100 | 7 | High Rise | |
| Tuscany Villa | 18 | 2 | Low Rise | |

---

### Pod 1 · Edm West · Thu
**12 properties · 1,072 units · 97 vacant now**

| Building | Units | Vacant | Type | Notes |
|---|---|---|---|---|
| 10126 154 Street | 6 | 0 | — | ⚠️ No class (A/B/C) assigned |
| Apple Apartments | 222 | 0 | Mid Rise | |
| Autumn Manor | 24 | 2 | Low Rise | |
| Brighton Court | 78 | 8 | Mid Rise | |
| Carina Apartments | 19 | 0 | Low Rise | |
| Douglas Manor | 57 | 57 | Mid Rise | ⚠️ 100% vacant — confirm active |
| Gala Apartments | 146 | 1 | Low Rise | |
| Glenmore Manor | 37 | 1 | Low Rise | |
| Sky Manor | 18 | 9 | Mid Rise | |
| Villa Grande | 48 | 3 | Low Rise | |
| Vista on 78th | 363 | 1 | Low Rise | |
| Woodridge Place | 54 | 15 | Mid Rise | |

---

### Pod 2 · Edm South · Tue
**8 properties · 571 units · 75 vacant now**

| Building | Units | Vacant | Type | Notes |
|---|---|---|---|---|
| Harmony Walker Lake A | 23 | 0 | Luxury | ⚠️ Unit count from notebook — previously wrong (was 123) |
| Harmony Walker Lake B | 80 | 1 | Luxury | ⚠️ Unit count from notebook — previously wrong (was 55) |
| Jasmine Apartments | 18 | 1 | Low Rise | |
| Millcrest Apts | 117 | 4 | Low Rise | |
| Neu Manor | 5 | 1 | Mid Rise | |
| Rideau Place | 68 | 0 | Low Rise | |
| The Aspen | 78 | 68 | Mid Rise | ⚠️ 87% vacant — lease-up or major turnover |
| The Edge | 182 | 0 | Mid Rise | |

---

### Pod 3 · Edm NE Inner · Wed
**12 properties · 530 units · 45 vacant now**

| Building | Units | Vacant | Type | Notes |
|---|---|---|---|---|
| Balwin Manor | 6 | 2 | Mid Rise | |
| Beverly Heights Manor | 12 | 1 | Mid Rise | |
| Catalina Estates | 9 | 5 | Mid Rise | |
| Cedar Manor | 18 | 7 | Mid Rise | |
| Courts Manor | 17 | 8 | Mid Rise | |
| Grandview Manor | 12 | 4 | Mid Rise | |
| Layali House | 17 | 3 | Mid Rise | |
| Link95 | 12 | 0 | Luxury | |
| Parkdale Terrace | 29 | 11 | Mid Rise | |
| Queensgate Manor | 104 | 2 | Low Rise | |
| Strathearn Place | 12 | 2 | Low Rise | ⚠️ City listed as Edmonton — postal T6C 3E2 confirms Edmonton (Strathearn neighbourhood) — notebook had Calgary (wrong) |
| The Heights at Vista Ridge | 282 | 0 | — | Unit count unverified (not in notebook) |

---

### Pod 4 · Edm North · Tue / Thu ⚡ Priority
**9 properties · 816 units · 121 vacant now**

| Building | Units | Vacant | Type | Notes |
|---|---|---|---|---|
| Copper Manor | 6 | 4 | Mid Rise | |
| Danton Manor | 75 | 2 | Low Rise | |
| Kafa Manor | 8 | 1 | Mid Rise | |
| Maple Leaf Court | 48 | 0 | Low Rise | |
| North Haven Estates | 104 | 5 | Low Rise | |
| Pioneer Apartments | 22 | 6 | Mid Rise | |
| The Barracks | 369 | 18 | Luxury | ⚡ Cluster with Maverick |
| The Manning | 75 | 0 | Mid Rise | |
| The Maverick | 109 | 85 | Mid Rise | ⚡ 78% vacant — top priority |

---

## CALGARY — 4 Active Pods

### Pod 6 · Cal Downtown · Mon–Fri (daily)
**3 properties · 202 units · 36 vacant now**

| Building | Units | Vacant | Type | Notes |
|---|---|---|---|---|
| Eleven | 123 | 16 | High Rise | PCG own portfolio |
| Mission Flats | 24 | 6 | Low Rise | |
| The Loft | 55 | 14 | Mid Rise | |

---

### Pod 7 · Cal Skyview NE · Tue / Thu
**5 properties · 523 units · 17 vacant now**

| Building | Units | Vacant | Type | Notes |
|---|---|---|---|---|
| Jovie | 44 | 5 | Luxury | |
| One51 | 57 | 3 | Mid Rise | |
| Sky 1 | 67 | 1 | Mid Rise | |
| Sky 2 | 177 | 3 | Mid Rise | |
| Trailside Skyview Ranch | 178 | 5 | Mid Rise | |

---

### Pod 8 · Cal SE · Mon / Wed / Fri ⚡ Priority
**3 properties · 453 units · 85 vacant now**

| Building | Units | Vacant | Type | Notes |
|---|---|---|---|---|
| Junction21 | 54 | 14 | Townhouse | |
| Junction88 | 89 | 38 | Mid Rise | |
| Legacy Place | 310 | 33 | Mid Rise | PCG managed |

---

### Pod 12 · Cal SW · (touring day TBD)
**1 property · 48 units · 0 vacant now**

| Building | Units | Vacant | Type | Notes |
|---|---|---|---|---|
| Trails Edge | 48 | 0 | Low Rise | Satellite — combine with Pod 6 touring when vacant |

---

## OUT-OF-CITY SATELLITES

### Pod 9 · Sherwood Park · Mon
| Building | Units | Vacant | Notes |
|---|---|---|---|
| Harmony at the Market | 20 | 2 | |
| Park Centre | 27 | 6 | |

### Pod 10 · St. Albert · Thu
| Building | Units | Vacant | Notes |
|---|---|---|---|
| Linden Park | 57 | 0 | |

### Pod 11 · Okotoks · (touring day TBD)
| Building | Units | Vacant | Notes |
|---|---|---|---|
| Rivers Edge | 24 | 0 | Satellite |

### Pod 12 · Cal SW · (see above)

### Pod 13 · Cochrane · Fri
| Building | Units | Vacant | Notes |
|---|---|---|---|
| Riverview Pointe | 209 | 4 | |

### Pod 14 · Saskatoon · Mon / Wed / Fri
| Building | Units | Vacant | Notes |
|---|---|---|---|
| Cielo | 184 | 5 | Lease-up |
| Greyson | 172 | 5 | Lease-up |
| Lawson Village | 96 | 96 | ⚠️ 100% vacant — lease-up confirmed? |

### Pod 15 · Regina · Tue / Thu
| Building | Units | Vacant | Notes |
|---|---|---|---|
| Lockwood Arms | 197 | 96 | ⚠️ 49% vacant — lease-up or significant turnover |

---

## ⚠️ Outstanding Data Flags

| Issue | Building | Action Required |
|---|---|---|
| Unit count not in notebook | 29 buildings (see list below) | Fill notebook before GHL config |
| No class assigned | 10126 154 Street | Assign A / B / C |
| 100% vacant | Douglas Manor (57u) | Confirm active/inactive |
| 100% vacant | Lawson Village (96u) | Confirm lease-up status |
| 49% vacant | Lockwood Arms (197u) | Confirm lease-up status |
| 87% vacant | The Aspen (78u) | Confirm lease-up or turnover |

**29 buildings with unit count still missing from notebook:**
North Haven Estates · Maple Leaf Court · Linden Park · The Aspen · Kafa Manor · Copper Manor · Grandview Manor · Cedar Manor · Courts Manor · Oakwood Manor · Layali House · Catalina Estates · Sky Manor · Chicklet House · Hamlet Village · Norwood Village · Royal Manor · Balwin Manor · House Acadian · The Palisades · Beverly Heights Manor · Douglas Manor · Parkdale Terrace · Riverview Pointe · Rivergate · Pioneer Apartments · Legacy Place · Cielo · Greyson · Lockwood Arms · Lawson Village · The Edge · The Heights at Vista Ridge

---
---

# PART B — GHL SETUP ARCHITECTURE

---

## 1. Account Structure

### GHL Location
ZEN Residential operates from a **single GHL location** with ZARA handling all pods.
Pod routing is handled via custom fields — not separate sub-accounts.

| Item | Value |
|---|---|
| Location Name | ZEN Residential |
| Location ID | *(collect from GHL → Settings → Business Info)* |
| Primary Bot | ZARA |
| Bot Type | AI Conversation Agent (GHL native or Railway webhook) |
| Timezone | America/Edmonton (MST/MDT) |
| Business Hours | Mon–Fri 8am–8pm, Sat 9am–5pm |

> **If Ellie (COWORK) is on a separate location:** keep them separate. ZARA does NOT share a location with Eleven's Ellie. Confirm location IDs before connecting any pipeline scanner.

---

## 2. Pipeline Stages

**Pipeline Name:** `ZEN Leasing`

| Stage # | Stage Name | Stage ID | Description |
|---|---|---|---|
| 1 | New Lead | *(collect)* | Fresh inbound — ZARA not yet engaged |
| 2 | ZARA Engaged | *(collect)* | ZARA has sent first message |
| 3 | Qualifying | *(collect)* | City + pod identified, bedroom/budget/movein in progress |
| 4 | Pod Assigned | *(collect)* | `zen_pod` field populated, tour not yet offered |
| 5 | Tour Scheduled | *(collect)* | Booking confirmed, confirmation sequence running |
| 6 | Toured | *(collect)* | Tour completed and tagged |
| 7 | Application | *(collect)* | Application submitted |
| 8 | Leased | *(collect)* | Lease signed |
| 9 | Nurture | *(collect)* | Not ready — re-engage in 14–30 days |
| 10 | Dead / Lost | *(collect)* | Unresponsive or explicit no |

> **To collect stage IDs:** GHL → Opportunities → your pipeline → right-click stage → Inspect → look for `stageId` in the API call, or use `GET /opportunities/pipeline` via GHL API.

---

## 3. Custom Fields

All custom fields live on the **Contact** object in GHL.

### Geographic & Pod Fields

| Field Label | API Key | Type | Values |
|---|---|---|---|
| ZEN City | `zen_city` | Dropdown | Edmonton / Calgary / Saskatoon / Regina / Other |
| ZEN Pod | `zen_pod` | Number | 0–15 (matches pod ID in planner) |
| ZEN Pod Name | `zen_pod_name` | Text | e.g. "Edm Downtown" |
| ZEN Tour Cluster | `zen_tour_cluster` | Text | Cluster name if route tour offered |

### Tour & No-Show Fields

| Field Label | API Key | Type | Values |
|---|---|---|---|
| No-Show Risk | `ns_risk` | Dropdown | high / medium / low |
| Tour Confirmed | `tour_confirmed` | Checkbox | Yes / No |
| No-Show Count | `no_show_count` | Number | 0 / 1 / 2+ |
| Last Tour Date | `last_tour_date` | Date | ISO date |
| Last Tour Building | `last_tour_building` | Text | Building name |

### Qualification Fields

| Field Label | API Key | Type | Values |
|---|---|---|---|
| Bedrooms Wanted | `bedrooms_wanted` | Dropdown | Bachelor / 1 Bed / 2 Bed / 3 Bed / 4+ Bed |
| Move-In Date | `movein_date` | Date | Prospect's target date |
| Budget Max | `budget_max` | Number | Monthly rent ceiling |
| Commute Anchor | `commute_anchor` | Text | Where they work/need to be |

> **Create these in GHL:** Settings → Custom Fields → Contacts → + Add Field
> Note all field IDs after creation — bot logic references them by key.

---

## 4. ZARA Bot Configuration

### Identity
| Setting | Value |
|---|---|
| Name | ZARA |
| Role | Leasing Agent — ZEN Residential |
| Tone | Warm, efficient, professional. Never pushy. |
| Cities served | Edmonton, Calgary, Saskatoon, Regina |

### System Prompt Core Blocks (in order)

1. **Identity block** — who ZARA is, who ZEN Residential is
2. **Geographic qualification block** — city → commute anchor → pod assignment (before bedroom/budget)
3. **Qualification block** — bedrooms, budget, move-in date (existing LEASE framework)
4. **Tour offer block** — offer times ONLY within assigned pod's touring window
5. **Pricing block** — NEVER quote prices until move-in date confirmed
6. **No-show block** — instructions for re-engage if tour missed

### Trigger: Bot Activates On
- New contact created via any lead source (Kijiji, Rentals.ca, direct web form, SMS)
- OR manual assignment when human agent hands off

### Bot Off: Trigger Tags
- `human_agent_active` — ZARA steps back
- `leased` — conversation closed
- `do_not_contact` — hard stop

---

## 5. Lead Routing — Geographic Qualification Flow

```
Inbound Lead → [Stage: New Lead]
    ↓
ZARA MSG 1: Welcome + City Confirm
    ↓ (zen_city saved)
ZARA MSG 2: Commute Anchor Question
    ↓ (zen_pod + zen_pod_name saved)
ZARA MSG 3: Soft Confirm area → Qualify bedrooms / budget / movein
    ↓ (qualifications saved to custom fields)
ZARA MSG 4A or 4B: Tour offer (pod touring window only)
    ↓ (booking confirmed → Stage: Tour Scheduled)
4-Touch Confirmation Sequence runs
    ↓
[Stage: Toured] or [Tag: no_show → re-engage]
```

### Pod Assignment Map — Edmonton

| Prospect Says | Pod | Pod Name |
|---|---|---|
| Downtown / Oliver / Jasper Ave / Core | 0 | Edm Downtown |
| West end / Stony Plain / Mayfield / Whitemud west | 1 | Edm West |
| South / Mill Woods / Ellerslie / Riverbend / Windermere | 2 | Edm South |
| NE / Beverly / Belvedere / Clareview / 118 Ave | 3 | Edm NE Inner |
| North / Castledowns / St Albert Trail / Henday north / Londonderry | 4 | Edm North |
| Sherwood Park | 9 | Sherwood Park |
| St. Albert | 10 | St. Albert |
| Flexible / anywhere | *(highest vacancy pod in city)* | |

### Pod Assignment Map — Calgary

| Prospect Says | Pod | Pod Name |
|---|---|---|
| Downtown / Beltline / Mission / 17th Ave | 6 | Cal Downtown |
| NE / Skyview Ranch / Cornerstone / Redstone | 7 | Cal Skyview NE |
| SE / Cranston / Legacy / Mahogany / Auburn Bay | 8 | Cal SE |
| SW / Marda Loop / Killarney / Westhills | 12 | Cal SW |
| Cochrane | 13 | Cochrane |
| Okotoks | 11 | Okotoks |
| Flexible / anywhere | *(highest vacancy pod in city)* | |

### GHL Field Updates on Pod Assignment

```
zen_city    → "Edmonton" or "Calgary"
zen_pod     → [0–15]
zen_pod_name → e.g. "Edm Downtown"
Stage       → move to "Pod Assigned"
```

---

## 6. Confirmation Sequence Workflows

**Trigger:** Contact tag `tour_scheduled` applied
**Workflow name:** `ZEN Tour Confirmation Sequence`

| Touch | Timing | Channel | Message |
|---|---|---|---|
| 1 | Immediately on booking | SMS + Email | Booking confirmed — building, date, time, address, Google Maps link, bring ID |
| 2 | 48 hrs before tour | SMS | Reminder — reply YES to confirm, or let us know to reschedule |
| 2b | 4 hrs after Touch 2 (no reply) | SMS | Follow-up: "Just checking — quick yes helps us hold your spot" |
| 3 | 24 hrs before tour | SMS | See you tomorrow — agent name, address, Maps link |
| 4 | 2 hrs before tour | SMS | Tour in 2 hours — agent mobile for running late |

**On YES reply to Touch 2:** apply tag `tour_confirmed`
**On CANCEL reply:** trigger `ZEN Reschedule Flow` (offer 2 new slots in same pod)

---

## 7. No-Show Risk Scoring & Re-engage

### Risk Scoring (apply at booking)

| Condition | Risk Level | Tag | Extra Action |
|---|---|---|---|
| Booked > 5 days out | High | `ns_risk_high` | Agent calls day before |
| First contact → booking > 48 hrs | Medium | `ns_risk_medium` | Add 72-hr confirmation touch |
| Same-day or next-day booking | Low | `ns_risk_low` | Standard 4-touch only |
| Previously no-showed | High | `ns_risk_high` | Agent call required + GHL note |
| Rescheduled once | Medium | `ns_risk_medium` | Add 72-hr touch |
| Route tour (2 buildings) | Lower | `ns_risk_low` | Route tours have lower no-show rate |

### No-Show Detection Trigger
Condition: Tour time passed + `toured` tag NOT applied within 30 min of tour end

### Re-engage Sequence

| Step | Timing | Message |
|---|---|---|
| MSG 1 | 45 min after missed tour | "Missed you today — hope everything's ok. Still available this week?" + 2 slot options |
| MSG 2 | 24 hrs later (no reply) | "Still interested in [area]? I have options available right now." |
| Action | 5 days no reply | Remove `tour_scheduled` · Add `nurture_no_show` · Move to Nurture stage · Re-engage in 14 days |

> **STOP replies:** Close opportunity as abandoned + GHL note only. No notification to agent. Silent cleanup.

---

## 8. Pod Touring Calendar

### Edmonton

| Pod | Name | Touring Days | Priority | Current Vacant |
|---|---|---|---|---|
| 0 | Edm Downtown | Mon · Wed · Fri | Standard | 178 |
| 1 | Edm West | Thu | Standard | 97 |
| 2 | Edm South | Tue | Standard | 75 |
| 3 | Edm NE Inner | Wed | Standard | 45 |
| 4 | Edm North | Tue · Thu | ⚡ Priority | 121 |
| 9 | Sherwood Park | Mon | Satellite | 8 |
| 10 | St. Albert | Thu | Satellite | 0 |

### Calgary

| Pod | Name | Touring Days | Priority | Current Vacant |
|---|---|---|---|---|
| 6 | Cal Downtown | Mon–Fri (daily) | Standard | 36 |
| 7 | Cal Skyview NE | Tue · Thu | Standard | 17 |
| 8 | Cal SE | Mon · Wed · Fri | ⚡ Priority | 85 |
| 12 | Cal SW | TBD | Satellite | 0 |
| 13 | Cochrane | Fri | Satellite | 4 |
| 11 | Okotoks | TBD | Satellite | 0 |

### Saskatchewan

| Pod | Name | Touring Days | Notes |
|---|---|---|---|
| 14 | Saskatoon | Mon · Wed · Fri | Cielo + Greyson + Lawson Village — lease-up portfolio |
| 15 | Regina | Tue · Thu | Lockwood Arms — lease-up |

> **Rule:** ZARA ONLY offers tour times within the prospect's assigned pod touring window.
> A Pod 0 prospect never gets offered a Pod 4 slot.

---

## 9. Cluster Tour Pairings

ZARA auto-offers a route tour when ≥ 2 buildings in a cluster both have vacancy.

| Cluster | Pod | Buildings | Radius | Trigger Condition |
|---|---|---|---|---|
| Edm North Priority | 4 | The Maverick + The Barracks | ~600m | Any 2 have vacancy |
| Edm Downtown Core | 0 | Kerry Manor + Richard House + Lorinda Court + Mid City Manor + Collage Place + The Edward Block | ~1km | Any 2 have vacancy |
| Edm Downtown Norwood | 0 | Norwood Village + Oakwood Manor + Rivergate + Parkdale Terrace | ~1km | Any 2 have vacancy |
| Cal SE | 8 | Legacy Place + Junction88 + Junction21 | ~3km | Any 2 have vacancy |
| Cal Skyview NE | 7 | Sky 1 + Sky 2 + Trailside + One51 | ~1km | Any 2 have vacancy |
| Edm NE Inner | 3 | Courts Manor + Grandview Manor + Catalina Estates + Layali House | ~1km | Any 2 have vacancy |

### Route Tour Script (MSG 4B)
> "I actually have **two properties near each other** that both have suites matching what you're looking for — you could see both back to back in about 45 minutes, which saves you a trip. Would you like to do a quick route tour?"
>
> If YES → confirm both buildings, start time at Building A, agent meets at lobby.
> If NO → offer choice: "Which one would you like to focus on?"

---

## 10. Implementation Checklist

### GHL Setup (do once)

- [ ] Confirm ZEN Residential GHL Location ID
- [ ] Create `ZEN Leasing` pipeline with all 10 stages — collect all Stage IDs
- [ ] Create all 9 custom fields (geographic + tour + qualification)
- [ ] Note all custom field IDs after creation
- [ ] Configure ZARA bot with system prompt (5 blocks)
- [ ] Set bot triggers: activates on new lead, deactivates on `human_agent_active` / `leased`

### Workflows (build in GHL)

- [ ] `ZEN Tour Confirmation Sequence` (triggered by `tour_scheduled` tag)
  - [ ] Touch 1: Immediate booking confirmation (SMS + email)
  - [ ] Touch 2: 48-hr reminder with YES/NO
  - [ ] Touch 2b: Follow-up if no reply to Touch 2 (4 hrs)
  - [ ] Touch 3: 24-hr "see you tomorrow"
  - [ ] Touch 4: 2-hr "on your way" with agent mobile
- [ ] `ZEN No-Show Re-engage` (triggered by tour time passed + no `toured` tag)
  - [ ] MSG 1: 45 min post-tour
  - [ ] MSG 2: 24 hrs no reply
  - [ ] Action: 5-day dead end → Nurture stage
- [ ] `ZEN Reschedule Flow` (triggered by CANCEL reply to Touch 2)
- [ ] `ZEN Nurture Re-engage 14-day` (triggered by `nurture_no_show` tag)
- [ ] `ZEN STOP Handler` — closes opportunity + GHL note, no agent notification

### ZARA Bot (update system prompt)

- [ ] Add geographic qualification block (city → commute anchor → pod assignment)
- [ ] Add pod-to-touring-window lookup (bot only offers times in correct pod)
- [ ] Add cluster tour detection logic
- [ ] Add no-show count check (2+ = route to human agent)
- [ ] Confirm: pricing never quoted until move-in date confirmed

### Data Hygiene (ongoing)

- [ ] Fill notebook unit counts for 29 buildings still missing
- [ ] Assign class (A/B/C) to 10126 154 Street
- [ ] Confirm Douglas Manor status (57 units, 100% vacant)
- [ ] Confirm Lawson Village status (96 units, 100% vacant)
- [ ] Confirm Lockwood Arms status (197 units, 49% vacant)
- [ ] Verify The Heights at Vista Ridge unit count (282 — not in notebook)
- [ ] Verify The Edward Block unit count (161 — not in notebook)

---

*Document maintained by PCG. Pod planner source of truth: `zen-pod-deploy/index.html`.*
*Conversation flow detail: `zen-pod-deploy/ZARA_GHL_Geographic_Qualification_Flow.md`.*
