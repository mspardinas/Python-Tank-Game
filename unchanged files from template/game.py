import random

import pygame

from constants import Control
from entities import GameEntityManager, Tank, Tree, Wall
from events import EventQueue
from handlers import (
    ControlEventHandler,
    DamageEventHandler,
    EngineEventMapper,
    EntityLifetimeEventHandler,
    FireBulletHandler,
    InteractionEventHandler,
    KeyToEntityControlHandler,
    MovementEventHandler,
    SimultaneousMoveEvent,
)
from utils import get_entity_rects, get_random_coords

pygame.init()


class TerrainEntityGenerator:
    def __init__(self, width: int, height: int, wall_chance: float, tree_min: int, tree_max: int, tree_chance: float):
        self._width = width
        self._height = height
        self._wall_chance = wall_chance
        self._tree_chance = tree_chance
        self._tree_min = tree_min
        self._tree_max = tree_max

    def generate_walls(self, event_queue, invalid_areas):
        walls = []

        for y in range(0, self._height, Wall.HEIGHT):
            for x in range(0, self._width, Wall.WIDTH):
                if random.random() < self._wall_chance:
                    wall = Wall(event_queue, (x, y))
                    if wall.rect.collidelist(invalid_areas) == -1:
                        walls.append(wall)

        return walls

    def _create_tree(self, event_queue):
        return Tree(event_queue, get_random_coords(self._width, self._height))

    def generate_trees(self, event_queue):
        trees = []

        for _ in range(self._tree_min):
            trees.append(self._create_tree(event_queue))

        for _ in range(self._tree_min + 1, self._tree_max + 1):
            if random.random() < self._tree_chance:
                trees.append(self._create_tree(event_queue))

        return trees


class TankGenerator:
    def _get_color(self, player_id):
        mapping = {
            1: "maroon",
            2: "forestgreen",
        }

        return "gray" if player_id not in mapping else mapping[player_id]

    def generate_tanks(self, event_queue, num_tanks, width, height):
        tanks = []

        for player_id in range(1, num_tanks + 1):
            while True:
                coords = get_random_coords(
                    width // Tank.WIDTH, height // Tank.HEIGHT)
                coords = (coords[0] * Tank.WIDTH, coords[1] * Tank.HEIGHT)

                tank = Tank(event_queue, player_id, coords,
                            self._get_color(player_id))
                if not pygame.sprite.spritecollideany(tank, tanks):
                    tanks.append(tank)
                    break

        return tanks


class GameSequence:

    def __init__(self, display, entity_manager, event_queue, engine_event_mapper):
        self._entity_manager = entity_manager
        self._event_queue = event_queue
        self._display = display
        self._engine_event_mapper = engine_event_mapper

    def start_game(self, fps=60):
        clock = pygame.time.Clock()

        while True:
            self._entity_manager.notify_tick_start()

            self._broadcast_input_events()
            self._broadcast_simultaneous_movement()
            self._event_queue.broadcast_queued()

            self._entity_manager.notify_tick_end()

            self._display.fill("black")
            self._entity_manager.refresh_display()
            pygame.display.flip()

            clock.tick(fps)

    def _convert_pending_input_events(self):
        events = [event for event in pygame.event.get()]
        return self._engine_event_mapper.convert_events(events)

    def _broadcast_input_events(self):
        input_events = self._convert_pending_input_events()
        self._event_queue.broadcast_events(input_events)

    def _broadcast_simultaneous_movement(self):
        event = SimultaneousMoveEvent(
            entities=self._entity_manager.get_entities(
                lambda entity: entity.is_moving_simultaneously),
        )
        self._event_queue.broadcast_event(event)


class GameInitializer:

    def initialize_game(self, width=1000, height=800, num_tanks=2, wall_chance=0.3, tree_min=1, tree_max=10, tree_chance=0.5):
        display = pygame.display.set_mode((width, height))

        event_queue = EventQueue()
        entity_manager = GameEntityManager(display)

        print("Generating terrain...")
        terrain_generator = TerrainEntityGenerator(
            width, height, wall_chance, tree_min, tree_max, tree_chance)
        trees = terrain_generator.generate_trees(event_queue)
        walls = terrain_generator.generate_walls(
            event_queue, get_entity_rects(trees))

        print("Generating tanks...")
        tanks = TankGenerator().generate_tanks(event_queue, num_tanks, width, height)

        self._remove_walls_under_tanks(walls, tanks)

        print("Registering entities...")
        entity_manager.register_entities(walls)
        entity_manager.register_entities(tanks)
        entity_manager.register_entities(trees)

        print("Registering handlers...")
        self._register_default_handlers(
            event_queue, entity_manager, width, height)

        engine_event_mapper = EngineEventMapper()

        return GameSequence(display, entity_manager, event_queue, engine_event_mapper)

    def _get_default_handlers(self, event_queue, entity_manager, width, height):
        return [
            MovementEventHandler(event_queue, entity_manager, width, height),
            self._setup_key_to_entity_control_handler(
                event_queue, entity_manager),
            ControlEventHandler(),
            InteractionEventHandler(event_queue),
            FireBulletHandler(event_queue),
            EntityLifetimeEventHandler(event_queue, entity_manager),
            DamageEventHandler(event_queue),
        ]

    def _get_default_keymap(self):
        return {
            1: {
                Control.MOVE_UP: "w",
                Control.MOVE_DOWN: "s",
                Control.MOVE_LEFT: "a",
                Control.MOVE_RIGHT: "d",
                Control.FIRE_BULLET: "space",
            },
            2: {
                Control.MOVE_UP: "up",
                Control.MOVE_DOWN: "down",
                Control.MOVE_LEFT: "left",
                Control.MOVE_RIGHT: "right",
                Control.FIRE_BULLET: ".",
            },
        }

    def _setup_key_to_entity_control_handler(self, event_queue, entity_manager):
        tank_list = entity_manager.get_entities(
            lambda entity: isinstance(entity, Tank))
        tank_dict = {tank.player_id: tank for tank in tank_list}

        handler = KeyToEntityControlHandler(event_queue)
        handler.map_keys(tank_dict, self._get_default_keymap())

        return handler

    def _register_default_handlers(self, event_queue, entity_manager, width, height):
        for handler in self._get_default_handlers(event_queue, entity_manager, width, height):
            event_queue.register_handler(handler)

    def _remove_walls_under_tanks(self, walls, tanks):
        for wall in walls[:]:
            if pygame.sprite.spritecollideany(wall, tanks):
                walls.remove(wall)


if __name__ == "__main__":
    print("Initializing game...")
    game = GameInitializer().initialize_game()

    print("Starting game...")
    game.start_game()
