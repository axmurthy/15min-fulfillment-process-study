"""Discrete-event simulation of the order-to-door process.

Process map (see docs/process_map.md):

    order accepted -> picking queue -> picking -> packing --\\
                                                              >-- handoff -> travel
    order accepted -> courier assignment -> courier at MFC --/              -> building access
                                                                            -> delivered
                                                                            -> courier return (repositioning)

Key modelling choices:
- Courier ASSIGNMENT overlaps preparation (it does not add to it). Under the
  default "assign_at_accept" policy a courier is reserved when the order is
  accepted and may idle-wait for the pack to be ready; "assign_at_ready" reserves
  a courier only once the order is packed. Both are provided so Phase 6 can
  compare dispatch rules.
- Courier RETURN / repositioning travel keeps the courier busy after delivery,
  so it consumes capacity and cost even though it is not part of the customer's
  delivery clock.
- No order is silently dropped. Every order ends in exactly one state:
  completed, cancelled, unfulfilled_stockout, or unfulfilled_horizon.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import simpy

from . import distributions as dist


class OrderState(str, Enum):
    PENDING = "pending"                         # still in system (becomes unfulfilled_horizon at cutoff)
    COMPLETED = "completed"                      # delivered to the door
    CANCELLED = "cancelled"                      # customer abandoned before courier pickup
    UNFULFILLED_STOCKOUT = "unfulfilled_stockout"  # could not be fulfilled (inventory)
    UNFULFILLED_HORIZON = "unfulfilled_horizon"  # still unfinished when the sim window ended


@dataclass
class Order:
    id: int
    t_accept: float
    items: int
    distance_km: float
    fulfillable: bool
    state: OrderState = OrderState.PENDING

    # milestone timestamps (minutes); None until reached
    t_pick_start: float | None = None
    t_pack_end: float | None = None
    t_courier_assigned: float | None = None
    t_ready: float | None = None          # pack complete AND courier present -> ready to hand off
    t_handoff_start: float | None = None
    t_handoff_end: float | None = None
    t_delivered: float | None = None
    t_resolved: float | None = None       # when a failed order resolved

    # durations used for utilisation / cost accounting
    pick_pack_min: float = 0.0
    courier_active_min: float = 0.0       # load + travel + access + return

    @property
    def order_to_door_min(self) -> float | None:
        if self.t_delivered is None:
            return None
        return self.t_delivered - self.t_accept


@dataclass
class RunResult:
    orders: list[Order]
    config_snapshot: dict = field(default_factory=dict)
    seed: int | None = None


def _prep(env, order: Order, pickers: simpy.Resource, cfg, rng):
    """Picking + packing; releases the picker automatically."""
    with pickers.request() as req:
        yield req
        order.t_pick_start = env.now
        ppt = dist.pick_pack_time(cfg, order.items, rng)
        order.pick_pack_min = ppt
        yield env.timeout(ppt)
        order.t_pack_end = env.now


def _do_delivery(env, order: Order, cfg, rng):
    """Load -> travel -> access -> delivered -> return. Courier stays busy throughout."""
    load = float(cfg.courier.load_min)
    out = dist.travel_time_min(order.distance_km, float(cfg.courier.speed_kmh))
    access = dist.access_time(cfg, rng)
    back = dist.travel_time_min(order.distance_km, float(cfg.courier.return_speed_kmh))

    order.t_handoff_start = env.now
    yield env.timeout(load)
    order.t_handoff_end = env.now
    yield env.timeout(out)
    yield env.timeout(access)
    order.t_delivered = env.now
    # return / repositioning -- not part of the delivery clock, but occupies the courier
    yield env.timeout(back)
    order.courier_active_min = load + out + access + back


def _order_process(env, order: Order, pickers, couriers, cfg, rng):
    """Full lifecycle for one order."""
    if not order.fulfillable:
        order.state = OrderState.UNFULFILLED_STOCKOUT
        order.t_resolved = env.now
        return

    deadline = order.t_accept + float(cfg.patience.cancel_after_min)
    policy = cfg.courier.dispatch_policy

    prep_proc = env.process(_prep(env, order, pickers, cfg, rng))

    if policy == "assign_at_accept":
        # Reserve a courier immediately; this overlaps preparation.
        req = couriers.request()
        result = yield req | env.timeout(float(cfg.patience.cancel_after_min))
        if req not in result:
            req.cancel()
            order.state = OrderState.CANCELLED
            order.t_resolved = env.now
            return
        order.t_courier_assigned = env.now
        yield prep_proc  # wait for packing to finish
    elif policy == "assign_at_ready":
        yield prep_proc  # pack first, then look for a courier
        remaining = deadline - env.now
        if remaining <= 0:
            order.state = OrderState.CANCELLED
            order.t_resolved = env.now
            return
        req = couriers.request()
        result = yield req | env.timeout(remaining)
        if req not in result:
            req.cancel()
            order.state = OrderState.CANCELLED
            order.t_resolved = env.now
            return
        order.t_courier_assigned = env.now
    else:  # pragma: no cover - guarded by config
        raise ValueError(f"unknown dispatch policy: {policy}")

    # Both the pack and a courier are now available.
    order.t_ready = env.now
    if env.now > deadline:
        # Customer ran out of patience before pickup could start.
        couriers.release(req)
        order.state = OrderState.CANCELLED
        order.t_resolved = env.now
        return

    try:
        yield from _do_delivery(env, order, cfg, rng)
        order.state = OrderState.COMPLETED
    finally:
        couriers.release(req)


def _source(env, cfg, rng, pickers, couriers, orders: list[Order]):
    """Generate orders at their arrival instants and launch their processes."""
    times = dist.arrival_times(cfg, rng)
    prev = 0.0
    avail_p = float(cfg.inventory.availability_prob)
    for i, t in enumerate(times):
        yield env.timeout(t - prev)
        prev = t
        order = Order(
            id=i,
            t_accept=env.now,
            items=dist.basket_size(cfg, rng),
            distance_km=dist.customer_distance_km(cfg, rng),
            fulfillable=bool(rng.uniform() < avail_p),
        )
        orders.append(order)
        env.process(_order_process(env, order, pickers, couriers, cfg, rng))


def run_once(cfg, seed: int) -> RunResult:
    """Run a single replication and return every order with its final state."""
    rng = np.random.default_rng(seed)
    env = simpy.Environment()
    pickers = simpy.Resource(env, capacity=int(cfg.picking.n_pickers))
    couriers = simpy.Resource(env, capacity=int(cfg.courier.n_couriers))
    orders: list[Order] = []

    env.process(_source(env, cfg, rng, pickers, couriers, orders))
    env.run(until=float(cfg.simulation.horizon_min))

    # Anything still pending at the cutoff is unfinished -- counted, never dropped.
    for o in orders:
        if o.state == OrderState.PENDING:
            o.state = OrderState.UNFULFILLED_HORIZON
            o.t_resolved = float(cfg.simulation.horizon_min)

    return RunResult(orders=orders, config_snapshot=dict(cfg), seed=seed)
