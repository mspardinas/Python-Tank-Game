import random
from pygame import Rect


def get_random_coords(width, height, body_width=0, body_height=0, invalid_areas=None):
    if not invalid_areas:
        unified_invalid_areas = None
    else:
        if len(invalid_areas) == 1:
            unified_invalid_areas = invalid_areas[0]
        else:
            unified_invalid_areas = Rect.unionall(
                invalid_areas[0], invalid_areas[1:])

    while True:
        coords = (
            random.randrange(0, width - body_width),
            random.randrange(0, height - body_height),
        )

        if (not unified_invalid_areas) or (not unified_invalid_areas.collidepoint(coords)):
            break

    return coords


def get_entity_rects(entities):
    return [entity.rect for entity in entities]
