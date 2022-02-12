from __future__ import annotations

import pygame
from pygame import Surface

from abstractions import AbstractGameEntity, IControllable, DamageableTrait
from constants import Direction, FONT
from events import FireBulletEvent, RemoveEntityEvent


class GameEntityManager:

    def __init__(self, display):
        self._entities = []
        self._display = display

    def refresh_display(self):
        for entity in self._entities:
            entity.on_display_refresh(self._display)

    def register_entity(self, entity):
        self._entities.append(entity)

    def register_entities(self, entities):
        for entity in entities:
            self.register_entity(entity)

    def unregister_entity(self, entity):
        entity.remove()
        if entity in self._entities:
            self._entities.remove(entity)

    def unregister_all_inside(self, rect, predicate=None):
        for entity in self._entities[:]:
            if (not predicate or predicate(entity)) and entity.rect.colliderect(rect):
                self.unregister_entity(entity)

    def notify_tick_start(self):
        for entity in self._entities[:]:
            entity.on_tick_start()

    def notify_tick_end(self):
        for entity in self._entities[:]:
            entity.on_tick_end()

    def get_entities(self, predicate=None):
        if predicate is None:
            return self._entities.copy()

        return [entity for entity in self._entities if predicate(entity)]

    def get_collided_with(self, entity):
        local_entities = self._entities.copy()
        local_entities.remove(entity)

        return pygame.sprite.spritecollide(entity, local_entities, dokill=False)


class Tank(DamageableTrait, AbstractGameEntity, IControllable):
    WIDTH = 50
    HEIGHT = 50

    def __init__(self, event_queue, player_id, coords, color, hp=10, speed=5, firing_delay=20):
        super().__init__(event_queue=event_queue, hp=hp)

        self._player_id = player_id
        self._speed = speed
        self._firing_delay = firing_delay
        self._facing = Direction.UP
        self._firing_tick_cooldown = 0
        self._color = color

        self._surf = Surface((self.WIDTH, self.HEIGHT))
        self._rect = self._surf.get_rect()
        self._rect.topleft = coords
        self.rerender()

    @property
    def player_id(self):
        return self._player_id

    @property
    def facing(self):
        return self._facing

    @property
    def color(self):
        return self._color

    def rerender(self):
        self._surf.fill(self.color)
        hp_text = FONT.render(str(self._hp), True, "white")
        hp_rect = hp_text.get_rect(center=self._surf.get_rect().center)
        self._surf.blit(hp_text, hp_rect)

    def on_tick_end(self):
        self.rerender()

    @property
    def speed(self):
        return self._speed

    def can_fire(self):
        return self._firing_tick_cooldown == 0

    def do_fire_control(self):
        if self.can_fire():
            self._firing_tick_cooldown = self._firing_delay + 1
            bullet = self.bullet_to_fire()
            self.queue_event_at_tail(
                FireBulletEvent(source=self, bullet=bullet))

    def bullet_to_fire(self):
        return Bullet(
            event_queue=self._event_queue,
            center=self.rect.center,
            owner=self,
            direction=self.facing,
            color=self.color,
        )

    def do_move_control(self, direction: Direction):
        self.is_moving_simultaneously = True
        self._facing = direction

    def do_move_stop_control(self):
        self.is_moving_simultaneously = False

    def move_by_current_facing(self):
        return self.move_by_direction(self._facing, self._speed)

    def on_tick_start(self):
        if self._firing_tick_cooldown > 0:
            self._firing_tick_cooldown -= 1

    @property
    def surf(self):
        return self._surf

    @property
    def rect(self):
        return self._rect


class Bullet(AbstractGameEntity):

    def __init__(self, event_queue, center, owner, color, direction, damage=1, speed=10, width=10, height=10):
        super().__init__(event_queue)
        self._owner = owner
        self._damage = damage
        self._speed = speed
        self._color = color
        self._facing = direction
        self._width = width
        self._height = height

        self._surf = Surface((self._width, self._height))
        self._surf.fill(color)

        self._rect = self._surf.get_rect()
        self._rect.center = center

        self._is_moving_simultaneously = True

    def move_by_current_facing(self):
        self.move_by_direction(self._facing, self._speed)

    @property
    def damage(self):
        return self._damage

    @property
    def owner(self):
        return self._owner

    @property
    def surf(self):
        return self._surf

    @property
    def rect(self):
        return self._rect


class Wall(DamageableTrait, AbstractGameEntity):
    WIDTH = 30
    HEIGHT = 30
    COLOR = "brown"

    def __init__(self, event_queue, coords, hp=3):
        super().__init__(event_queue=event_queue, hp=hp)

        self._surf = Surface((self.WIDTH, self.HEIGHT))
        self._surf.fill(self.COLOR)

        self._rect = self._surf.get_rect()
        self._rect.topleft = coords

    def is_dead(self):
        return self.hp == 0

    @property
    def surf(self):
        return self._surf

    @property
    def rect(self):
        return self._rect


class Tree(AbstractGameEntity):
    WIDTH = 100
    HEIGHT = 100
    COLOR = "green"

    def __init__(self, event_queue, coords):
        super().__init__(event_queue)
        self._surf = Surface((self.WIDTH, self.HEIGHT))
        self._surf.fill(self.COLOR)

        self._rect = self._surf.get_rect()
        self._rect.center = coords

    @property
    def surf(self):
        return self._surf

    @property
    def rect(self):
        return self._rect


class DamageText(AbstractGameEntity):
    COLOR = "white"

    def __init__(self, event_queue, center, damage, speed=2, tick_length=30):
        super().__init__(event_queue)

        self._speed = speed
        self._ticks_left = tick_length

        self._surf = FONT.render(str(damage), True, "white")
        self._rect = self._surf.get_rect(center=center)

    def on_tick_start(self):
        self._ticks_left -= 1
        self._rect.move_ip((0, -self._speed))

        if self._ticks_left <= 0:
            self.queue_event_at_tail(RemoveEntityEvent(entity=self))

    @property
    def surf(self):
        return self._surf

    @property
    def rect(self):
        return self._rect
