from abc import ABCMeta, abstractmethod

import pygame
from pygame.sprite import Sprite


class IEventHandler(metaclass=ABCMeta):

    @abstractmethod
    def handle_event(self, event):
        raise NotImplementedError

    @property
    @abstractmethod
    def event_types(self):
        raise NotImplementedError


class IControllable(metaclass=ABCMeta):

    @abstractmethod
    def do_fire_control(self):
        raise NotImplementedError

    @abstractmethod
    def do_move_control(self, direction):
        raise NotImplementedError

    @abstractmethod
    def do_move_stop_control(self):
        raise NotImplementedError

    @abstractmethod
    def do_drop_control(self):          #added an abstract method for dropping bombs
        raise NotImplementedError

class DamageableTrait(metaclass=ABCMeta):

    def __init__(self, hp, **kwargs):
        self._hp = hp
        super().__init__(**kwargs)

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        self._hp = max(0, value)

    def on_damage(self, damage, attacker):
        self.hp -= damage

    def on_death(self):
        pass

    def is_dead(self):
        return self.hp == 0


class AbstractGameEntity(Sprite, metaclass=ABCMeta):

    def __init__(self, event_queue):
        super().__init__()
        self._event_queue = event_queue
        self._to_be_removed = False
        self._is_moving_simultaneously = False

    def move_to(self, coords):
        self.rect.topleft = coords

    def move_by_direction(self, direction, speed):
        delta = self._compute_movement_delta(direction, speed)
        self.move_by_delta(delta)

    def move_by_delta(self, delta):
        self.rect.move_ip(delta)

    def _compute_movement_delta(self, direction, speed):
        return tuple(map(lambda v: v * speed, direction.value))

    def on_tick_start(self):
        pass

    def on_tick_end(self):
        pass

    @property
    @abstractmethod
    def surf(self):
        pass

    @property
    @abstractmethod
    def rect(self) -> pygame.Rect:
        pass

    @property
    def is_moving_simultaneously(self):
        return self._is_moving_simultaneously

    @is_moving_simultaneously.setter
    def is_moving_simultaneously(self, value):
        self._is_moving_simultaneously = value

    def on_display_refresh(self, display):
        display.blit(self.surf, self.rect)

    def queue_event_at_head(self, event):
        return self._event_queue.queue_event_at_head(event)

    def queue_event_at_tail(self, event):
        return self._event_queue.queue_event_at_tail(event)

    def queue_event_on_next_tick(self, event):
        return self._event_queue.queue_event_on_next_tick(event)

    def delete(self):
        from events import RemoveEntityEvent
        return self._event_queue.queue_event_on_next_tick(RemoveEntityEvent(entity=self))

    def is_partially_outside_screen(self, width, height):
        return self.rect.left < 0 \
            or self.rect.top < 0 \
            or self.rect.right > width \
            or self.rect.bottom > height

    def is_fully_outside_screen(self, width, height):
        return self.rect.right <= 0 \
            or self.rect.bottom <= 0 \
            or self.rect.left >= width \
            or self.rect.top >= height
