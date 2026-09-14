# Ski Resort Financial Planning — Application Architecture

## 1. Purpose & Design Philosophy

This is a **decision-support / consulting deliverable**, not a modeling replacement for
Excel. The architecture optimizes for:

- **Clarity over configurability** — a small number of high-signal, business-level
  assumptions rather than hundreds of granular line items.
- **Scenario storytelling** — Baseline + named strategic alternatives (A/B/C/custom),
  each fully self-contained and comparable side-by-side.
- **Separation of concerns** — assumptions, capital projects, scenarios, financial
  calculations, capital structure, and presentation are independent, testable modules
  connected only through well-defined data contracts (dataclasses).
- **Streamlit as a thin presentation layer** — all business logic lives in a plain
  Python package (`src/skimodel`) with no Streamlit imports, so it can be unit tested,
  reused in a notebook, or swapped onto another UI framework later.

## 2. High-Level Architecture

```
                       ┌─────────────────────────────┐
                       │        Streamlit UI          │
                       │  ui/app.py + ui/pages/*.py    │
                       │  (rendering + widgets only)   │
                       └───────────────┬───────────────┘
                                       │ reads/writes
                       ┌───────────────▼───────────────┐
                       │   SessionStore (persistence)  │
                       │  wraps st.session_state,       │
                       │  JSON import/export            │
                       └───────────────┬───────────────┘
                                       │
        ┌─────────────┬───────────────┼───────────────┬─────────────┐
        ▼             ▼               ▼               ▼             ▼
 AssumptionSet  CapitalProject   ScenarioManager  Capital       Dashboard
 (assumptions)  Library          (scenarios)      Structure     (kpi/charts/
                (capital_projects)                (capital_stack) comparisons)
        │             │               │               │
        └─────────────┴───────┬───────┴───────────────┘
                               ▼
                   FinancialProjectionEngine
                        (projection)
                               │
                               ▼
                      ProjectionResults
              (consumed by Dashboard + comparisons)
```

**Data flow:** a `Scenario` bundles an `AssumptionSet`, a list of selected
`CapitalProject`s (with timing/cost overrides), and a `CapitalStructure`. The
`FinancialProjectionEngine` takes a `Scenario` and produces immutable
`ProjectionResults`, which the dashboard renders and the comparison module diffs
against other scenarios.

## 3. Folder / File Layout

```
ski-financial-model/
├── app.py                          # Streamlit entrypoint (thin, delegates to ui/)
├── requirements.txt
├── pyproject.toml
├── data/
│   └── default_capital_projects.json   # seed catalog for CapitalProjectLibrary
├── src/
│   └── skimodel/                       # framework-agnostic business logic
│       ├── __init__.py
│       ├── config.py                   # global constants (horizon, discount rate defaults)
│       ├── assumptions/
│       │   ├── models.py               # Demand/Pricing/Operational/Inflation/
│       │   │                           #   CapitalPhasing assumptions + AssumptionSet
│       │   └── defaults.py             # factory functions for baseline defaults
│       ├── capital_projects/
│       │   ├── models.py               # CapitalProject, ProjectCategory
│       │   └── library.py              # CapitalProjectLibrary (CRUD, timing, cost)
│       ├── scenarios/
│       │   ├── models.py               # Scenario
│       │   └── manager.py              # ScenarioManager (create/clone/delete/compare)
│       ├── capital_stack/
│       │   ├── models.py               # DebtTranche, EquityTranche, Grant,
│       │   │                           #   CapitalStructure
│       │   └── analyzer.py             # amortization schedules, funding gap,
│       │                               #   blended cost of capital
│       ├── projection/
│       │   ├── results.py              # ProjectionResults (immutable, to_dataframe)
│       │   └── engine.py               # FinancialProjectionEngine
│       ├── dashboard/
│       │   ├── kpi.py                  # build_kpi_cards()
│       │   ├── charts.py               # plotly figure builders
│       │   └── comparisons.py          # multi-scenario comparison tables
│       └── persistence/
│           └── store.py                # SessionStore (session_state + JSON I/O)
├── pages/                               # Streamlit's required location for multipage apps
│   ├── 1_Assumptions.py
│   ├── 2_Capital_Projects.py
│   ├── 3_Scenario_Builder.py
│   ├── 4_Executive_Dashboard.py
│   └── 5_Capital_Stack.py
├── ui/
│   ├── bootstrap.py                     # page_config + SessionStore wiring, shared by
│   │                                    #   app.py and every page
│   └── components/
│       └── forms.py                     # reusable widget builders bound to dataclasses
└── tests/
    ├── test_assumptions.py
    ├── test_capital_projects.py
    ├── test_scenarios.py
    ├── test_projection_engine.py
    └── test_capital_stack.py
```

## 4. Module Details

### 4.1 Assumption Engine (`skimodel.assumptions`)

Five focused dataclasses, each representing one high-level assumption category, composed
into a single `AssumptionSet`:

- `DemandAssumptions` — base visits, growth rate, market capture.
- `PricingAssumptions` — ticket price, price growth, ancillary spend, pass mix.
- `OperationalAssumptions` — fixed/variable opex, labor cost growth, maintenance capex %.
- `InflationAssumptions` — general/labor/energy inflation.
- `CapitalPhasingAssumptions` — planning horizon and phasing strategy (front-loaded,
  even, back-loaded, or custom per-year weights) applied to capital project timing.

`defaults.py` provides `default_assumption_set()` used to seed the Baseline scenario.

### 4.2 Capital Project Library (`skimodel.capital_projects`)

- `CapitalProject` — id, name, category, cost, start year offset, duration, revenue/opex
  impact, useful life, active flag.
- `CapitalProjectLibrary` — in-memory catalog with `add_project`, `remove_project`,
  `update_project`, `assign_timing`, `assign_cost`, `list_projects`, and
  `load_defaults()` (reads `data/default_capital_projects.json`). Scenarios reference
  projects **by id**, so editing the shared library doesn't retroactively change past
  scenario snapshots (scenarios store a shallow copy at selection time).

### 4.3 Scenario Builder (`skimodel.scenarios`)

- `Scenario` — id, name, description, `AssumptionSet`, selected project ids (with
  optional per-scenario overrides), `CapitalStructure`, `is_baseline` flag.
- `ScenarioManager` — owns the dict of scenarios, always guarantees exactly one
  `Baseline`; `create_scenario()`/`clone_scenario()` let users spin up Scenario A/B/C or
  any number of custom scenarios; `compare()` runs the projection engine for a set of
  scenario ids and returns `{scenario_name: ProjectionResults}`.

### 4.4 Financial Projection Engine (`skimodel.projection`)

`FinancialProjectionEngine(scenario, discount_rate, terminal_growth_rate).run()` returns
a `ProjectionResults` covering the full planning horizon:

1. Revenue = visits × ticket price × pass-mix/ancillary adjustments, grown by demand +
   pricing assumptions, adjusted for capital project revenue impacts once each project
   is online.
2. Operating expense = fixed + variable opex, grown by inflation/labor assumptions, plus
   project-driven opex deltas.
3. EBITDA = Revenue − Opex.
4. Capex = sum of active capital projects' costs phased per `CapitalPhasingAssumptions`.
5. Debt service = amortization schedules from `CapitalStructure` debt tranches
   (delegated to `capital_stack.analyzer.build_debt_schedule`).
6. Free Cash Flow = EBITDA − Capex − Debt Service − Maintenance Capex − Taxes (simple
   placeholder tax toggle).
7. NPV/IRR computed over the FCF stream (via `numpy_financial`), Enterprise Value via
   discounted terminal value (Gordon growth on final-year EBITDA or FCF).

`ProjectionResults` is an immutable dataclass with a `to_dataframe()` convenience method
for charting/export.

### 4.5 Executive Dashboard (`skimodel.dashboard`)

- `kpi.build_kpi_cards(results)` → list of `{label, value, delta, format}` dicts for KPI
  cards (Revenue CAGR, EBITDA Margin, NPV, IRR, Enterprise Value, Funding Gap).
- `charts.py` → Plotly figure builders: revenue/EBITDA trend, FCF waterfall, capex
  phasing Gantt-style bar, scenario comparison bar/line charts.
- `comparisons.compare_scenarios(results_by_name)` → tidy comparison `DataFrame` for
  side-by-side tables.

### 4.6 Capital Stack Module (`skimodel.capital_stack`)

- `DebtTranche`, `EquityTranche`, `Grant` — simple funding source dataclasses.
- `CapitalStructure` — aggregates tranches/grants against total project cost; exposes
  `total_debt()`, `total_equity()`, `total_grants()`, `funding_gap()`.
- `analyzer.py` — `build_debt_schedule()` (interest-only/amortizing/bullet), 
  `blended_cost_of_capital()`, `compute_funding_gap()` — feeds debt service back into the
  projection engine and funding-gap KPI into the dashboard.

### 4.7 Persistence (`skimodel.persistence`)

`SessionStore` wraps `st.session_state` so pages don't touch Streamlit state directly:
holds one `CapitalProjectLibrary` and one `ScenarioManager` per browser session, plus
`export_json()` / `import_json()` for saving/loading a full workbook-like snapshot
(assumptions + projects + scenarios + capital stack) — the closest analog to "Save As"
in Excel, without becoming a modeling replacement.

## 5. Class Summary (contracts)

| Module | Class | Responsibility |
|---|---|---|
| assumptions.models | `AssumptionSet` | Bundles the 5 assumption dataclasses |
| capital_projects.models | `CapitalProject` | One capital investment definition |
| capital_projects.library | `CapitalProjectLibrary` | CRUD + timing/cost assignment |
| scenarios.models | `Scenario` | Named bundle of assumptions + projects + capital stack |
| scenarios.manager | `ScenarioManager` | Create/clone/delete/list/compare scenarios |
| capital_stack.models | `CapitalStructure` | Debt + equity + grants + funding gap |
| capital_stack.analyzer | `CapitalStackAnalyzer` | Amortization, blended cost of capital |
| projection.engine | `FinancialProjectionEngine` | Runs a scenario → `ProjectionResults` |
| projection.results | `ProjectionResults` | Immutable projection output |
| dashboard.* | free functions | KPI cards, charts, comparison tables |
| persistence.store | `SessionStore` | Session-state + JSON persistence |

## 6. Extensibility Notes

- New capital project categories or assumption fields are additive (dataclass fields
  with defaults) — no breaking changes to the engine's public interface.
- Adding a new scenario is just `ScenarioManager.create_scenario(name=...)`; there is no
  hardcoded limit beyond Baseline/A/B/C, satisfying "unlimited custom scenarios."
- The engine is deterministic and pure (no I/O), enabling straightforward unit tests and
  potential reuse in a batch/CLI "board deck" export tool later.
