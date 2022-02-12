from enum import Enum, IntEnum

import pygame


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0,  1)
    LEFT = (-1,  0)
    RIGHT = (1,  0)

    @classmethod
    def are_opposite(cls, a, b):
        return (a == cls.UP and b == cls.DOWN) and \
            (a == cls.DOWN and b == cls.UP) and \
            (a == cls.LEFT and b == cls.RIGHT) and \
            (a == cls.RIGHT and b == cls.LEFT)


class Control(IntEnum):
    MOVE_UP = 1
    MOVE_DOWN = 2
    MOVE_LEFT = 3
    MOVE_RIGHT = 4
    FIRE_BULLET = 5
    DROP_BOMB = 6           #added a new logical game control for dropping bombs


pygame.init()
pygame.font.init()

FONT = pygame.font.SysFont('Arial', 24)
BOMB_FONT = pygame.font.SysFont('Arial', 16)            #added a pygame font object to accomodate smaller bomb text
