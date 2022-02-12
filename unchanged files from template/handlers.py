from __future__ import annotations

import pygame
import pygame.locals

from abstractions import (
    AbstractGameEntity,
    DamageableTrait,
    IControllable,
    IEventHandler,
)
from constants import Control, Direction
from entities import Bullet, DamageText, Tank, Wall
from events import (
    AddEntityEvent,
    CollisionEvent,
    DamageEntityEvent,
    DamageResultEvent,
    FireBulletEvent,
    FireControlEvent,
    KeyHeldEvent,
    KeyReleasedEvent,
    MoveControlEvent,
    MoveStopControlEvent,
    MoveToEvent,
    RemoveEntityEvent,
    SimultaneousMoveEvent,
)
from utils import get_entity_rects


class EngineEventMapper:

    def supported_keys(self):
        return list(range(32, 128)) + [
            pygame.locals.K_UP,
            pygame.locals.K_DOWN,
            pygame.locals.K_LEFT,
            pygame.locals.K_RIGHT,
        ]

    def convert_events(self, events):
        ret = []

        for event in events:
            if event.type == pygame.locals.KEYUP:
                ret.append(KeyReleasedEvent(key=pygame.key.name(event.key)))

        press_data = pygame.key.get_pressed()
        pressed_keys = [pygame.key.name(code)
                        for code in self.supported_keys() if press_data[code]]

        for key in pressed_keys:
            ret.append(KeyHeldEvent(key=key))

        return ret


class MovementEventHandler(IEventHandler):

    def __init__(self, event_queue, entity_manager, width, height):
        self._event_queue = event_queue
        self._entity_manager = entity_manager
        self._width = width
        self._height = height

    @property
    def event_types(self):
        return [SimultaneousMoveEvent, MoveToEvent]

    def handle_event(self, event):
        if isinstance(event, SimultaneousMoveEvent):
            old_positions = {
                id(entity): entity.rect.topleft for entity in event.entities}

            for entity in event.entities:
                self._move_entity_simultaneous(entity)

            self._undo_colliding_tank_movements(event.entities, old_positions)
            self._emit_collisions_for_entities(event.entities)

        elif isinstance(event, MoveToEvent):
            self._move_entity_to(event.entity, event.coords)
            self._emit_collisions_for_entity(event.entity)

    def _undo_colliding_tank_movements(self, entities_to_move, old_positions):
        tanks = [
            entity for entity in entities_to_move if isinstance(entity, Tank)]

        while True:
            undone_tanks = set()

            for tank in tanks:
                collided_entities = self._entity_manager.get_collided_with(
                    tank)

                for collided_entity in collided_entities:
                    if isinstance(collided_entity, Wall) or isinstance(collided_entity, Tank):
                        tank.rect.topleft = old_positions[id(tank)]
                        undone_tanks.add(tank)
                        break

            if undone_tanks:
                for tank in undone_tanks:
                    entities_to_move.remove(tank)
            else:
                break

    def _move_entity_simultaneous(self, entity):
        if isinstance(entity, Tank):
            entity.move_by_current_facing()
            self._limit_movement_within_screen(entity)

        elif isinstance(entity, Bullet):
            entity.move_by_current_facing()
            self._delete_fully_outside_screen(entity)

    def _delete_fully_outside_screen(self, entity):
        if entity.is_fully_outside_screen(self._width, self._height):
            self._event_queue.queue_event_at_tail(
                RemoveEntityEvent(entity=entity))

    def _limit_movement_within_screen(self, entity):
        if entity.rect.left < 0:
            entity.rect.left = 0
        if entity.rect.top < 0:
            entity.rect.top = 0
        if entity.rect.right > self._width:
            entity.rect.right = self._width
        if entity.rect.bottom > self._height:
            entity.rect.bottom = self._height

    def _move_entity_to(self, entity, coords):
        if isinstance(entity, Tank):
            entity.move_to(coords)
            self._limit_movement_within_screen(entity)
        elif isinstance(entity, Bullet):
            entity.move_to(coords)

    def _emit_collisions_for_entity(self, collider):
        collided_with = self._entity_manager.get_collided_with(collider)
        if collided_with:
            event = CollisionEvent(
                collider=collider,
                collided_others=collided_with,
            )
            self._event_queue.broadcast_event(event)

    def _emit_collisions_for_entities(self, colliders):
        for collider in colliders:
            self._emit_collisions_for_entity(collider)


class KeyToEntityControlHandler(IEventHandler):

    def __init__(self, event_queue):
        self._event_queue = event_queue
        self._mapping = {}

    @property
    def event_types(self):
        return [KeyHeldEvent, KeyReleasedEvent]

    def map_keys(self, entity_dict, keymap):
        for player_id, mapping in keymap.items():
            entity = entity_dict[player_id]

            for control, key in mapping.items():
                control_to_direction = {
                    Control.MOVE_UP: Direction.UP,
                    Control.MOVE_DOWN: Direction.DOWN,
                    Control.MOVE_LEFT: Direction.LEFT,
                    Control.MOVE_RIGHT: Direction.RIGHT,
                }

                if control in control_to_direction:
                    self.map_key(entity, key, MoveControlEvent,
                                 direction=control_to_direction[control])

                elif control == Control.FIRE_BULLET:
                    self.map_key(entity, key, FireControlEvent)

    def map_key(self, entity, key, control_event_type, **kwargs):
        event = None

        if control_event_type == MoveControlEvent:
            event = MoveControlEvent(
                entity=entity, direction=kwargs["direction"])
        elif control_event_type == FireControlEvent:
            event = FireControlEvent(entity=entity)

        if event:
            self._mapping[key] = event

    def handle_event(self, event):
        if isinstance(event, KeyHeldEvent):
            if event.key in self._mapping:
                mapped_event = self._mapping[event.key]
                self._event_queue.broadcast_event(mapped_event)

        elif isinstance(event, KeyReleasedEvent):
            if event.key in self._mapping:
                mapped_event = self._mapping[event.key]

                if isinstance(mapped_event, MoveControlEvent):
                    entity = mapped_event.entity
                    self._event_queue.broadcast_event(
                        MoveStopControlEvent(entity=entity))


class ControlEventHandler(IEventHandler):

    @property
    def event_types(self):
        return [FireControlEvent, MoveStopControlEvent, MoveControlEvent]

    def handle_event(self, event):
        if isinstance(event, FireControlEvent):
            if isinstance(event.entity, IControllable):
                event.entity.do_fire_control()

        elif isinstance(event, MoveControlEvent):
            if isinstance(event.entity, IControllable):
                event.entity.do_move_control(direction=event.direction)

        elif isinstance(event, MoveStopControlEvent):
            if isinstance(event.entity, IControllable):
                event.entity.do_move_stop_control()


class InteractionEventHandler(IEventHandler):

    def __init__(self, event_queue):
        self._event_queue = event_queue

    @property
    def event_types(self):
        return [CollisionEvent]

    def handle_event(self, event):
        if isinstance(event, CollisionEvent):
            self._handle_collision(event.collider, event.collided_others)

    def _handle_collision(self, collider, collided_others):
        if isinstance(collider, Bullet):
            self._handle_bullet_collider(collider, collided_others)

    def _handle_bullet_collider(self, collider, collided_others):
        walls = self._get_entities_with_type(collided_others, Wall)
        tanks = self._get_entities_with_type(collided_others, Tank)
        if collider.owner in tanks:
            tanks.remove(collider.owner)
        other_bullets = self._get_entities_with_type(collided_others, Bullet)

        for other_bullet in other_bullets:
            self._queue_entity_removal(other_bullet)

        for wall in walls:
            self._queue_entity_damaging(collider, wall)

        for tank in tanks:
            self._queue_entity_damaging(collider, tank)

        if walls or tanks or other_bullets:
            self._queue_entity_removal(collider)

    def _queue_entity_removal(self, entity):
        self._event_queue.queue_event_at_tail(RemoveEntityEvent(entity=entity))

    def _queue_entity_damaging(self, attacker, defender):
        self._event_queue.queue_event_at_tail(
            DamageEntityEvent(attacker=attacker, defender=defender))

    def _get_entities_with_type(self, entities, entity_type):
        ret = []

        for entity in entities:
            if isinstance(entity, entity_type):
                ret.append(entity)

        return ret


class FireBulletHandler(IEventHandler):

    def __init__(self, event_queue):
        self._event_queue = event_queue

    @property
    def event_types(self):
        return [FireBulletEvent]

    def handle_event(self, event):
        if isinstance(event, FireBulletEvent):
            self._event_queue.queue_event_at_tail(
                AddEntityEvent(entity=event.bullet))


class EntityLifetimeEventHandler(IEventHandler):

    def __init__(self, event_queue, entity_manager):
        self._event_queue = event_queue
        self._entity_manager = entity_manager

    @property
    def event_types(self):
        return [AddEntityEvent, RemoveEntityEvent]

    def handle_event(self, event):
        if isinstance(event, AddEntityEvent):
            self._entity_manager.register_entity(event.entity)
        elif isinstance(event, RemoveEntityEvent):
            self._entity_manager.unregister_entity(event.entity)


class DamageEventHandler(IEventHandler):

    def __init__(self, event_queue):
        self._event_queue = event_queue

    @property
    def event_types(self):
        return [DamageEntityEvent, DamageResultEvent]

    def handle_event(self, event):
        if isinstance(event, DamageEntityEvent):
            if isinstance(event.attacker, Bullet):
                self._do_damage(event.attacker, event.defender,
                                event.attacker.damage)
        elif isinstance(event, DamageResultEvent):
            self._handle_display_damage(event.entity, event.damage)

    def _handle_display_damage(self, entity, damage):
        self._event_queue.queue_event_at_tail(
            AddEntityEvent(entity=DamageText(self._event_queue, entity.rect.center, damage)))

    def _do_damage(self, attacker, defender, damage):
        if isinstance(defender, DamageableTrait):
            defender.on_damage(damage, attacker)

            if isinstance(defender, AbstractGameEntity):
                self._event_queue.queue_event_at_tail(
                    DamageResultEvent(entity=defender, damage=damage))

            if defender.is_dead():
                defender.on_death()
                self._queue_entity_removal(defender)

    def _queue_entity_removal(self, entity):
        self._event_queue.queue_event_at_tail(RemoveEntityEvent(entity=entity))
