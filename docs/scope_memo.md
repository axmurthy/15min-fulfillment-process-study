# Phase 1 - Scope Memo and Neighborhood Recommendation

## What this study is (and is not)

This is a **simulation-based process-design study** of a 15-minute grocery
delivery service. It asks: *under what operating conditions could such a service
be reliable and economically viable in one Bay Area neighborhood?*

It is **not** an empirical diagnosis of Blinkit, Zepto, Gopuff, or any operator.
We do not have, and do not invent, order-level company data. The Blinkit/Zepto
model "cannot work in the US" is treated as a **hypothesis to investigate**, not
a conclusion.

Three things we refuse to conflate (see `data/sources_register.csv`):

1. **Population density is not order demand.** Dense tracts tell us where people
   are, not how many 15-minute grocery orders they place. Our arrival rates are
   transparent assumptions (`A02`, `A03`), not observations.
2. **Routing estimates are not observed delivery times.** Travel time comes from
   geometry and an assumed safe speed, not from GPS traces of real couriers.
3. **Grocery sales (AOV) are not revenue retained by the operator.** The operator
   keeps a margin + fees + ad revenue, not the whole basket value.

## Recommended neighborhood: San Francisco Mission District

**Recommendation: the Mission District, San Francisco** (roughly the 94110 area).

Rationale, judged on **data feasibility** (the deciding criterion), not on
guessing where demand is highest:

| Criterion | Why the Mission scores well |
|---|---|
| Residential density | Among the densest, most uniformly residential districts in the Bay Area, so Census ACS tract/block-group density (`S07`) is high and the "serve a compact disk" abstraction is reasonable. |
| Clean Census geography | Well-defined, contiguous tracts with large populations, giving small relative margins of error on ACS density estimates. |
| Compact, grid-like road network | OSM coverage (`S08`) is excellent and the near-grid street layout makes network-distance a defensible travel estimate over a ~1-2 km disk. |
| Flat terrain | Unlike hillier SF districts, the Mission is largely flat, so a constant safe e-bike speed assumption (`A08`) is less distorting. |
| Short-trip plausibility | A 1.0-2.0 km service radius covers a large, dense population, matching the "short trips ending back at the store" economics in the published q-commerce literature (`S04`). |

**Alternatives considered:** Downtown Oakland (good density/grid, slightly more
commercial/daytime-population skew), Downtown San Jose (lower residential
density, more car-oriented network). Both are viable fallbacks if the Phase 1
data-extension step (pulling live ACS/OSM) reveals a problem with the Mission.

**Honesty note:** we recommend the Mission on *data-feasibility* grounds. We are
**not** claiming it is the most profitable location; demand there is unknown and
is modelled as an assumption.

## Proposed scope

- One micro-fulfilment center (dark store) serving a disk of radius 1.0-2.0 km.
- Resources: pickers (pick + pack) and e-bike couriers (incl. return travel).
- Delivery clock: order accepted -> doorstep handoff; target 15 min.
- Two demand periods (off-peak, peak) over a 4-hour window per replication.
- Controllable factors for the DOE: service radius, picker count, courier count.
- Scenario factors (uncertain, not controlled): demand level, travel speed.

## Data gaps (explicitly unavailable, so simulated)

| Gap | Why unavailable | How we handle it |
|---|---|---|
| Order arrival rate & timing | Proprietary to operators | ASSUMPTION, swept via `demand_multiplier`; peak/off-peak split |
| Pick/pack times | Proprietary; no public time-and-motion data | ASSUMPTION with gamma variability |
| Actual courier GPS travel times | Not public | Geometry + assumed safe speed; congestion scenario |
| Basket composition | Proprietary | Over-dispersed count assumption |
| Operator cost structure | Partially public, mostly India-based | Published proxies (`S09`-`S11`) + assumptions, all swept in sensitivity |

Because the operational inputs are unavailable, this study is framed as a
**process-design simulation**, and every conclusion is **conditional** on the
assumptions in `config.yaml` and `data/sources_register.csv`.
