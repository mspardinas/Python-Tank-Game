from __future__ import annotations

import random                           # imported random to randomize the bomb timer
import pygame
from pygame import Surface

from abstractions import AbstractGameEntity, IControllable, DamageableTrait
from constants import Direction, FONT, BOMB_FONT                                          # import BOMB_FONT
from events import FireBulletEvent, DropBombEvent, BombExplodeEvent, RemoveEntityEvent    # import DropBombEvent and BombExplodeEvent
from utils import get_random_color, collision                                             # import helper functions get_random_color for RandomColorTank and collision for rect-circle collision


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
        local_entities2 = []                                                            # create new empty list for entities which fall within (circle/radius) explosion collision

        if isinstance(entity, Bomb):                                                    # differentiate Bomb Explosion's collision with Bullet collision
            for local_entity in local_entities:
                if collision(local_entity.rect, entity.center, entity.radius):
                    local_entities2.append(local_entity)                                # append entity to the said empty list when a (rect-circle) collision happens
            return local_entities2                                                      # return entities which fall within rect-circle collision
        else:                                                                           # else rect-rect collision
            return pygame.sprite.spritecollide(entity, local_entities, dokill=False)


class Tank(DamageableTrait, AbstractGameEntity, IControllable):
    WIDTH = 50
    HEIGHT = 50

    def __init__(self, event_queue, player_id, coords, color, hp=10, speed=5, firing_delay=20, bombing_delay = 60):         # added bombing_delay for bomb cooldowns
        super().__init__(event_queue=event_queue, hp=hp)

        self._player_id = player_id
        self._speed = speed
        self._firing_delay = firing_delay
        self._bombing_delay = bombing_delay                     # added new attribute _bombing_delay set to bombing delay
        self._facing = Direction.UP
        self._firing_tick_cooldown = 0
        self._bombing_tick_cooldown = 0                         # added a new attribute _bombing_tick_cooldown initially set to 0
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

    def can_bomb(self):                             # new method that checks if a tank can drop bombs based on the cooldown
        return self._bombing_tick_cooldown == 0

    def do_drop_control(self):                      # new method that drops a bomb
        if self.can_bomb():
            self._bombing_tick_cooldown = self._bombing_delay + 1
            bomb = self.bomb_to_drop()
            self.queue_event_at_tail(
                DropBombEvent(source=self, bomb=bomb))

    def bomb_to_drop(self):                         # new method that returns a bomb instance
        return Bomb(
            event_queue=self._event_queue,
            center=self.rect.center,
            owner=self
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

        if self._bombing_tick_cooldown > 0:         # added one for bomb cooldown
            self._bombing_tick_cooldown -= 1

    @property
    def surf(self):
        return self._surf

    @property
    def rect(self):
        return self._rect


class FastFiringTank(Tank):                                                                                 # a Tank subclass with a method that decreases the fire_delay
    def __init__(self, event_queue, player_id, coords, color):                                              # to 5, increasing the fire rate to 12 bullets/second
        super().__init__(event_queue=event_queue, player_id=player_id, coords=coords, color=color)
        self.fast_fire_rate()

    def fast_fire_rate(self):
        self._firing_delay = 5


class BigBulletTank(Tank):                                                                                  # a Tank subclass that modifies the original bullet_to_fire
    def __init__(self, event_queue, player_id, coords, color):                                              # method to return a different instance of Bullet
        super().__init__(event_queue=event_queue, player_id=player_id, coords=coords, color=color)

    def bullet_to_fire(self):
        bullet = Bullet(
            event_queue=self._event_queue,
            center=self.rect.center,
            owner=self,
            direction=self.facing,
            color=self.color,
            damage = 3,
            speed = 6,
            width = 30,
            height = 30
        )
        return bullet


class AlwaysMovingTank(Tank):                                                                               # a Tank subclass with methods that increases speed from 5
    def __init__(self, event_queue, player_id, coords, color):                                              # to 10, and changes is_moving_simultaneously to true making
        super().__init__(event_queue=event_queue, player_id=player_id, coords=coords, color=color)          # the tank unstoppable even with user movement inputs.
        self.i_am_speed()
        self.is_moving_simultaneously = True

    def i_am_speed(self):
        self._speed = 10

    def do_move_stop_control(self):
        self.is_moving_simultaneously = True


class RandomColorTank(Tank):                                                                                # a Tank subclass with methods that randomly changes the
    def __init__(self, event_queue, player_id, coords, color):                                              # tank's color every 1/5 of a second (200 ms), and rerenders
        super().__init__(event_queue=event_queue, player_id=player_id, coords=coords, color=color)          # said color into the tank after one tick
        self.color_timer = 0

    def change_color(self):
        if pygame.time.get_ticks() - self.color_timer > 200:
            self.color_timer = pygame.time.get_ticks()
            self._color = get_random_color()

    def on_tick_end(self):
        self.change_color()
        self.rerender()


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


class Bomb(DamageableTrait, AbstractGameEntity):                    # new Bomb class
    COLOR = "red"

    def __init__(self, event_queue, center, owner, damage = 0, hp = 3, width=20, height=20, radius = 100):       # hardcode radius to be 100, and initially set bomb damage to zero (will be changed during actual explosion)
        super().__init__(event_queue=event_queue, hp=hp)

        self._owner = owner
        self._damage = damage
        self._center = center
        self._width = width
        self._height = height
        self._timer = float(random.randint(3,10))                   # converts randint to float for easier processing
        self._radius = radius

        self._surf = Surface((self._width, self._height))           #
        self._surf.fill(self.COLOR)                                 #
                                                                    # declare bomb dimensions and coordinates
        self._rect = self._surf.get_rect()                          #
        self._rect.center = center                                  #
        self.rerender()

        self._is_moving_simultaneously = True                       # added an _is_moving_attribute set to True to queue in SimultaneousEvent array

    def rerender(self):                                             # method to update display text
        self._surf.fill(self.COLOR)
        timer_text = BOMB_FONT.render(str(round(self._timer,1)), True, "white")
        timer_rect = timer_text.get_rect(center=self._surf.get_rect().center)
        self._surf.blit(timer_text, timer_rect)

    def on_tick_end(self):                                          # if bomb is dead (health == 0 or timer == 0), explode it, otherwise re-render the display timer text
        if self.is_dead():
            self.on_death()
        else:
            self.rerender()

    def on_tick_start(self):                                        # updates self._timer at each tick start
        if self._timer > 0:
            self._timer = round(self._timer - 0.02, 2)

    def is_dead(self):                                              # check if the bomb is dead/to be exploded
        return self._hp == 0 or self._timer == 0

    def on_death(self):                                             # executes explosion animation
        self._damage = 3                                            # change the damage to 3 on explosion
        explosion = self.animation_to_use()
        self.queue_event_at_tail(                                   # queue a BombExplodeEvent with an included Explosion instance
            BombExplodeEvent(entity=self, explosion=explosion))

    def animation_to_use(self):                                     # returns an Explosion instance
        return Explosion(
            event_queue=self._event_queue,
            center=self._rect.center
        )

    @property
    def damage(self):
        return self._damage

    @property
    def owner(self):
        return self._owner

    @property
    def center(self):
        return self._center

    @property
    def radius(self):
        return self._radius

    @property
    def surf(self):
        return self._surf

    @property
    def rect(self):
        return self._rect

class Explosion(AbstractGameEntity):                # new Explosion animation class
    WIDTH = 200                                     #
    HEIGHT = 200                                    # hardcoded dimensions and
    RADIUS = 100                                    # color based on specifications
    COLOR = "yellow"                                #

    def __init__(self, event_queue, center, tick_length=30):            # Explosion animation duration set to be the same as the Damage Text class
        super().__init__(event_queue)

        self._ticks_left = tick_length

        self._surf = Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA, 32)
        self._surf = self._surf.convert_alpha()

        self._circ = pygame.draw.circle(self._surf, self.COLOR, (100,100), self.RADIUS)
        self._circ.center = center

    def  on_tick_start(self):                                   # decrement animation duration (30 ms) on each tick start
        self._ticks_left -= 1

        if self._ticks_left <= 0:                                       # remove the animation at ticks_left <= 0
            self.queue_event_at_tail(RemoveEntityEvent(entity=self))

    @property
    def surf(self):
        return self._surf

    @property
    def rect(self):
        return self._circ
