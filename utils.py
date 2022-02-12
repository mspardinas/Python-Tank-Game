import random
import math
from pygame import Rect, Color


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

def get_random_color():                                                                 # helper function for RandomColorTank
    return Color(random.randint(0,255), random.randint(0,255), random.randint(0,255))

def collision(rect, center, radius):                                                    # improvised circle-rectangle collision function (full explanation is included in the image file)
    max_distance_from_circle_center = math.sqrt((radius**2) + (rect.width**2))
    left = rect.left
    right = rect.left + rect.width
    top = rect.top
    bottom = rect.top + rect.height

    centerx = center[0]
    centery = center[1]

    topleft = [left, top]
    bottomleft = [left, bottom]
    bottomright = [right, bottom]
    topright = [right, top]

    relevant_coords = [(topleft, bottomleft), (bottomleft, bottomright), (bottomright, topright), (topright, topleft)]

    q = [centerx, centery]

    for coord in relevant_coords:
        distance_from_circle_center1 = math.dist(coord[0], q)
        distance_from_circle_center2 = math.dist(coord[1], q)
        if distance_from_circle_center1 <= max_distance_from_circle_center and distance_from_circle_center2 <= max_distance_from_circle_center:         # hard case
            return True
        if distance_from_circle_center1 <= radius:                                                            # easy case
            return True

    return False
