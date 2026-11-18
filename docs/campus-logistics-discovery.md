# Campus Logistics Discovery

Discovery date: 2026-04-06

This note combines:

- `www.my-stuwe.de.har`
- a public follow-up check against `www.my-stuwe.de`
- the official university location-plan page: `https://uni-tuebingen.de/universitaet/standort-und-anfahrt/lageplaene/`

The goal is to identify food, navigation, and building data that fits the existing student dashboard direction.

## Existing Gap

The repo has no campus-food or campus-navigation surface today. That means no mensa menus, no canteen directory, no building search, and no map-aware location layer for lecture halls or clinics.

## my-stuwe Mealplan Contracts

Observed and verified routes:

| Route or flow | Observed contract | Inferred capability | Student value |
| --- | --- | --- | --- |
| `/wp-json/mealplans/v1` | REST route registry | discover supported mealplan endpoints and language params | `high` |
| `/wp-json/mealplans/v1/canteens` | public bulk JSON endpoint | fetch all active canteens in one request | `very high` |
| `/wp-json/mealplans/v1/canteens/{id}` | public JSON endpoint | fetch one canteen's menus and metadata | `very high` |
| canteen page HTML with `data-canteen='...'` | embedded widget config | map public page slug to mealplan canteen id | `high` |
| public canteen pages with Google Maps buttons | address deep links | connect menus to physical locations | `high` |

Verified mealplan schema:

- top-level canteen object:
  - `canteenId`
  - `canteen`
  - `menus`
- per menu entry:
  - `id`
  - `menuLine`
  - `photo`
  - `studentPrice`
  - `guestPrice`
  - `pupilPrice`
  - `menuDate`
  - `menu`
  - `meats`
  - `icons`
  - `filtersInclude`
  - `allergens`
  - `additives`
  - `co2`

Important findings:

- `/wp-json/mealplans/v1/canteens` currently returns 10 canteens, including non-Tübingen locations.
- The active Tübingen or closely related ids observed live are:
  - `611` `Mensa Wilhelmstraße`
  - `621` `Mensa Morgenstelle`
  - `623` `Mensa & Cafeteria Prinz Karl`
  - `715` `Cafeteria Wilhelmstraße`
  - `724` `Cafeterien MMHSZSanTT`
- `724` is a shared cafeteria feed rather than a one-location-only endpoint.
- Some Tübingen cafeteria pages expose address and map links but no visible `data-canteen` widget, so the product model should separate:
  - `locations`
  - `meal sources`

### Exact Wilhelmstraße contract

HAR verification date: 2026-04-06
Live recheck date: 2026-04-23

- Public page: `https://www.my-stuwe.de/mensa/mensa-wilhelmstrasse-tuebingen/`
- Page HTML exposes `data-canteen='611'`
- Observed HAR request:
  - `GET https://www.my-stuwe.de//wp-json/mealplans/v1/canteens/611?lang=de&v=...`
  - headers included `accept: application/json, text/plain, */*`, `referer: https://www.my-stuwe.de/mensa/mensa-wilhelmstrasse-tuebingen/`, and `x-requested-with: XMLHttpRequest`
- Live public route also works without the cache-busting `v` query:
  - `GET https://www.my-stuwe.de/wp-json/mealplans/v1/canteens/611?lang=de`
- Response contract:
  - top-level JSON object keyed by canteen id, here `"611"`
  - canteen payload fields:
    - `canteenId`
    - `canteen`
    - `menus`
  - menu payload fields observed live:
    - `id`
    - `menuLine`
    - `menuDate`
    - `menu`
    - `meats`
    - `studentPrice`
    - `guestPrice`
    - `pupilPrice`
    - `icons`
    - `filtersInclude`
    - `allergens`
    - `additives`
    - `co2`
    - `photo`

## Highest-Value Food Features

### 1. Multi-canteen menu API

Why it matters:

- the bulk endpoint already supports it
- menus carry student and guest pricing, allergens, additives, diet icons, and optional CO2 values
- this is immediately useful every weekday

Suggested wrapper surface:

- `GET /api/food/canteens`
- `GET /api/food/canteens/{id}`
- `GET /api/food/menus?date=YYYY-MM-DD&location=tuebingen`

### 2. Diet, allergen, and budget filters

Why it matters:

- the upstream schema already exposes the right fields
- this is stronger product value than just showing raw menu text
- it fits well with dashboard cards and "what can I eat near my next lecture?" workflows

Suggested wrapper surface:

- `GET /api/food/menus?date=...&icon=vegan&exclude_allergen=ML&max_price=4.50`

### 3. Location-aware canteen directory

Why it matters:

- public canteen pages expose Google Maps deep links and route-specific slugs
- some pages are location-only, some are location plus meal feed
- students need opening context and navigation almost as much as the menu itself

Suggested wrapper surface:

- `GET /api/food/locations`
- `GET /api/food/locations/{slug}`

## Official University Plan Contracts

Verified public route structure from the official maps page:

| Route | Capability | Student value |
| --- | --- | --- |
| `/universitaet/standort-und-anfahrt/lageplaene/adressenliste/` | alphabetical building directory with building detail links | `very high` |
| `/universitaet/standort-und-anfahrt/lageplaene/barrierefreie-zugaenge/` | accessibility-oriented entrypoint | `high` |
| `/universitaet/standort-und-anfahrt/lageplaene/uebersichtsplan/` | overview map | `high` |
| `/universitaet/standort-und-anfahrt/lageplaene/karte-a-morgenstelle/` | Morgenstelle area map | `very high` |
| `/universitaet/standort-und-anfahrt/lageplaene/karte-b-wilhelmstrasse-talkliniken/` | Wilhelmstraße and Talkliniken area map | `very high` |
| `/universitaet/standort-und-anfahrt/lageplaene/karte-c-sand-aussenbereiche-innenstadt/` | Sand and outer-city locations | `medium` |
| `/universitaet/standort-und-anfahrt/lageplaene/karte-d-altstadt/` | Altstadt area map | `medium` |
| lecture-hall detail pages such as `/.../kupferbau/` and `/.../auf-der-morgenstelle-16/` | building-specific location pages | `high` |
| medical clinics overview on `medizin.uni-tuebingen.de` | clinic index | `medium` |

Notable details:

- the address-list page is not just a PDF landing page; it links directly to individual building detail pages
- building entries are alphabetized by street name
- lecture hall pages are already separated out as their own public routes
- the official page explicitly highlights barrier-free access, lecture hall buildings, and clinic navigation

## Highest-Value Plan Features

### 1. Searchable building directory

Why it matters:

- the official address list is already structured
- this solves "where is room X or building Y?" without forcing full map browsing
- it complements Alma timetable locations and my-stuwe canteen locations

Suggested wrapper surface:

- `GET /api/places/buildings`
- `GET /api/places/buildings/{slug}`
- `GET /api/places/search?q=...`

### 2. Campus-area maps tied to student workflows

Why it matters:

- the official map taxonomy already matches how students move through campus
- `Morgenstelle` and `Wilhelmstraße/Talkliniken` are especially high-value because they overlap with lecture halls and mensa sites

Suggested wrapper surface:

- `GET /api/places/maps`
- `GET /api/places/maps/{area}`

### 3. Accessibility-aware routing and location overlays

Why it matters:

- the university already publishes barrier-free access as a first-class plan category
- this is a better first accessibility increment than inventing location heuristics in-app

Suggested wrapper surface:

- `GET /api/places/accessibility`
- `GET /api/places/buildings/{slug}/accessibility`

## Best Combined Product Additions

These two data sources fit together unusually well.

### 1. Campus food dashboard

- today's nearby menus
- diet and allergen filters
- price-aware sorting
- direct navigation links to the canteen

### 2. Building and room finder

- search by building name or street
- jump from Alma lecture locations to official map pages
- expose lecture-hall shortcuts like Kupferbau or Hörsaalzentrum Morgenstelle

### 3. Lecture-to-lunch planning

- combine timetable location, campus area, and canteen menus
- answer questions such as "what is open near Morgenstelle after my lecture?"

### 4. Accessibility-aware campus helper

- barrier-free entrypoints
- building details
- clinic and lecture-hall location support

## Recommended Build Order

1. `my-stuwe` multi-canteen menu API and filters.
2. canteen location directory with map links.
3. official building directory and campus-area map routes.
4. combined lecture-to-lunch and place-search workflows.
5. accessibility overlays and clinic or lecture-hall shortcuts.

## Confidence Notes

- High confidence:
  - `my-stuwe` bulk and per-canteen mealplan endpoints
  - canteen widget ids in public HTML
  - official map entry routes and address-list structure
- Medium confidence:
  - exact mapping from shared cafeteria endpoint `724` to every smaller Tübingen cafeteria page
  - how much building metadata is present on each individual detail page without a second crawl
