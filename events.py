from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Tuple, TYPE_CHECKING

from abstractions import AbstractGameEntity

if TYPE_CHECKING:
    from entities import Bullet


class EventQueue:
    def __init__(self):
        self._events = []
        self._next_tick_events = []
        self._handlers = defaultdict(list)

    def register_handler(self, handler):
        for event_type in handler.event_types:
            self._handlers[event_type].append(handler)

    def queue_events_at_tail(self, events):
        for event in events:
            self.queue_event_at_tail(event)

    def queue_event_at_head(self, event):
        self._events.insert(0, event)

    def queue_event_at_tail(self, event):
        self._events.append(event)

    def queue_event_on_next_tick(self, event):
        self._next_tick_events.append(event)

    def broadcast_queued(self):
        while self._events:
            event = self._events.pop()
            self.broadcast_event(event)

        self._events, self._next_tick_events = self._next_tick_events, []

    def broadcast_event(self, event):
        #print(f"Broadcasting {event}")
        for listener in self._listeners_for(event):
            listener.handle_event(event)

    def broadcast_events(self, events):
        for event in events:
            self.broadcast_event(event)

    def _listeners_for(self, event):
        return self._handlers[type(event)]


class GameEvent:
    pass


@dataclass
class KeyHeldEvent(GameEvent):
    key: str


@dataclass
class KeyReleasedEvent(GameEvent):
    key: str


@dataclass
class ControlEvent(GameEvent):
    entity: AbstractGameEntity


@dataclass
class FireControlEvent(ControlEvent):
    entity: AbstractGameEntity


@dataclass
class MoveControlEvent(GameEvent):
    entity: AbstractGameEntity
    direction: AbstractGameEntity


@dataclass
class MoveStopControlEvent(GameEvent):
    entity: AbstractGameEntity


@dataclass
class FireBulletEvent(GameEvent):
    source: AbstractGameEntity
    bullet: Bullet


@dataclass
class DropControlEvent(ControlEvent):       # new subclass for the action of dropping bombs
    entity: AbstractGameEntity


@dataclass
class DropBombEvent(GameEvent):             # new subclass for actually dropping bombs
    source: AbstractGameEntity
    bomb: Bomb


@dataclass
class BombExplodeEvent(GameEvent):          # new subclass for bomb explosion
    entity: AbstractGameEntity
    explosion: Explosion


@dataclass
class MoveToEvent(GameEvent):
    entity: AbstractGameEntity
    coords: Tuple[int, int]


@dataclass
class CollisionEvent(GameEvent):
    collider: AbstractGameEntity
    collided_others: List[AbstractGameEntity]


@dataclass
class DeathEvent(GameEvent):
    entity: AbstractGameEntity


@dataclass
class AddEntityEvent(GameEvent):
    entity: AbstractGameEntity


@dataclass
class RemoveEntityEvent(GameEvent):
    entity: AbstractGameEntity


@dataclass
class SimultaneousMoveEvent(GameEvent):
    entities: List[AbstractGameEntity]


@dataclass
class DamageEntityEvent(GameEvent):
    attacker: AbstractGameEntity
    defender: AbstractGameEntity


@dataclass
class DamageResultEvent(GameEvent):
    entity: AbstractGameEntity
    damage: int
