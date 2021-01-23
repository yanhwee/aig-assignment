from copy import deepcopy
from math import sqrt, atan2, sin, cos
from operator import itemgetter
from itertools import tee, accumulate
from functools import reduce
from typing import Callable, Union, Tuple, List
import pygame
from pygame import Surface, Vector2, Rect, Mask
from Base import Base
from GameEntity import GameEntity
from HAL import World
from Graph import pathFindAStar
# from Character import Character

class MockEntity(pygame.sprite.Sprite):
    def __init__(self, **kwargs):
        pygame.sprite.Sprite.__init__(self)
        for key, value in kwargs.items():
            setattr(self, key, value)

# def mock_entity(**kwargs) -> GameEntity:
#     entity = GameEntity(None, None, None)
#     for key, value in kwargs.items():
#         setattr(entity, key, value)
#     return entity

class Character:
    def __init__(self):
        ## Immutable Attributes
        # In GameEntity Class
        self.mask: Mask
        self.rect: Rect
        self.position: Vector2
        # In HAL Class
        self.world: World
        # In Character Class
        self.base: Base
        self.team_id: int
        self.max_hp: float
        self.current_hp: float
        self.maxSpeed: float
        self.min_target_distance: float
        self.ko: bool
        self.can_level_up: Callable[[], bool]
        self.level_up: Callable[[str], []]
        # Knight Only
        self.melee_damage: float
        self.melee_cooldown: float
        # Archer Only
        self.projectile_range: float
        self.projectile_speed: float
        self.ranged_damage: float
        self.ranged_cooldown: float
        self.projectile_image: Surface
        # Wizard Only
        self.projectile_range: float
        self.projectile_speed: float
        self.ranged_damage: float
        self.ranged_cooldown: float
        self.projectile_image: Surface
        self.explosion_image: Surface
        ## Mutable Attributes
        self.velocity: Vector2
        self.move_target: Union[None, Vector2, GameEntity]
        self.attack_target: Union[None, Vector2, GameEntity]
        self.paths: List[List[Vector2]]
        self.path: List[Vector2]

###  Initialisation  ###
def init_hero(hero: Character) -> None:
    # Compatibility Fixes
    hero.target = None
    # if getattr(hero, 'projectile_range', False):
    #     hero.min_target_distance = hero.projectile_range
    # else: hero.min_target_distance = 0 # code not working because projectile_range is init in HAL
    # Init all mutable attributes
    hero.velocity = Vector2(0, 0)
    hero.move_target = None
    hero.attack_target = None
    hero.paths = get_paths(hero)
    hero.path = 0

###  Movement  ###
def set_move_target(
    hero: Character, 
    target: Union[None, Tuple[float, float], Vector2, GameEntity]) -> None:
    '''Public: Set where the hero should move to'''
    if isinstance(target, tuple):
        target = Vector2(target)
    hero.move_target = target

def update_velocity(hero: Character) -> None:
    '''Public: Update velocity based on move target'''
    target = hero.move_target
    if target is None:
        hero.velocity = Vector2(0, 0)
    elif isinstance(target, Vector2):
        update_velocity_towards(hero, target)
    elif isinstance(target, GameEntity):
        update_velocity_towards(hero, target.position)
    else:
        raise Exception

def update_velocity_towards(hero: Character, position: Vector2) -> None:
    '''Private: Update velocity based on target position'''
    velocity = position - hero.position
    if velocity: # If non-zero
        velocity.scale_to_length(hero.maxSpeed)
        hero.velocity = velocity
    else:
        hero.velocity = Vector2(0, 0)

###  Attacking  ###
def set_attack_target(
    hero: Character, 
    target: Union[None, Tuple[float, float], Vector2, GameEntity]) -> None:
    '''Depreacted: don't use'''
    if isinstance(target, tuple):
        target = Vector2(target)
    hero.attack_target = target

def calculate_preaim_collision(
    p1: Vector2, p2: Vector2, v: Vector2, s: Vector2) -> Vector2:
    '''Private: Calculate the intersection of two position and velocity with speed'''
    p = p2 - p1
    a = v.magnitude_squared() - s ** 2
    if a == 0:
        print('WARN: a is zero')
        return p2
    b = 2 * p.dot(v)
    c = p.magnitude_squared()
    d = b ** 2 - 4 * a * c
    if d < 0:
        print('WARN: No solution to find collision!')
        return p2
    t = (-b - sqrt(d)) / (2 * a)  # Seems Oddly Familiar
    x = p2 + t * v
    return x

def preaim_entity(hero: Character, entity: GameEntity) -> Vector2:
    '''Public: Calculate where the hero should shoot to hit a moving entity'''
    return calculate_preaim_collision(
        hero.position, entity.position, 
        entity.velocity, hero.projectile_speed)

###  Targetting  ###
def enemy_between(entityA: GameEntity, entityB: GameEntity) -> bool:
    return (entityA.team_id) == (1 - entityB.team_id)

def friendly_between(entityA: GameEntity, entityB: GameEntity) -> bool:
    return entityA.team_id == entityB.team_id

def entity_type_of_any(
    entity: GameEntity,
    arrow: bool=False,
    fireball: bool=False,
    archer: bool=False,
    knight: bool=False,
    wizard: bool=False,
    orc: bool=False,
    tower: bool=False, 
    base: bool=False) -> bool:
    check_names = [
        (arrow, 'projectile'),
        (fireball, 'explosion'),
        (archer, 'archer'),
        (knight, 'knight'),
        (wizard, 'wizard'),
        (orc, 'orc'),
        (tower, 'tower'),
        (base, 'base')]
    return any(
        (check and entity.name == name) for check, name in check_names)

def entity_not_ko(entity: GameEntity) -> bool:
    return not entity.ko

def get_entities_that_are(
    hero: Character,
    *predicates: Callable[[GameEntity], bool]) -> List[GameEntity]:
    '''Public: Retrives entities that fulfils all conditions'''
    return [
        entity for entity in hero.world.entities.values()
        if all(pred(entity) for pred in predicates)]

def get_enemy_heroes(hero: Character) -> List[GameEntity]:
    return get_entities_that_are(hero,
        lambda entity: enemy_between(entity, hero),
        lambda entity: entity_type_of_any(
            entity, archer=True, knight=True, wizard=True),
        lambda entity: entity_not_ko(entity))

def get_enemy_heroes_and_orcs(hero: Character) -> List[GameEntity]:
    return get_entities_that_are(hero,
        lambda entity: enemy_between(entity, hero),
        lambda entity: entity_type_of_any(
            entity, archer=True, knight=True, wizard=True, orc=True),
        lambda entity: entity_not_ko(entity))

def get_nearest_entity_that_is(
    hero: Character, 
    *predicates: Callable[[GameEntity], bool]) -> Union[None, GameEntity]:
    '''Public: Gets the nearest entity that fulfils all conditions'''
    return min(
        get_entities_that_are(hero, *predicates),
        key=lambda entity: distance_between(hero.position, entity.position),
        default=None)

def get_nearest_enemy_that_is(
    hero: Character, 
    *predicates: Callable[[GameEntity], bool]) -> Union[None, GameEntity]:
    '''Public: Gets the nearest enemy that fulfils all conditions'''
    return get_nearest_entity_that_is(hero,
        lambda entity: enemy_between(entity, hero),
        lambda entity: entity_type_of_any(
            entity, arrow=False, fireball=False, archer=True, 
            knight=True, wizard=True, orc=True, tower=True, base=True),
        lambda entity: entity_not_ko(entity),
        *predicates)

def get_nearest_enemy_projectile_that_is(
    hero: Character, 
    *predicates: Callable[[GameEntity], bool]) -> Union[None, GameEntity]:
    '''Public: Gets the nearest enemy projectile that fulfils all conditions'''
    return get_nearest_entity_that_is(hero,
        lambda entity: enemy_between(entity, hero),
        lambda entity: entity_type_of_any(
            entity, arrow=True, fireball=False, archer=False, 
            knight=False, wizard=False, orc=False, tower=False, base=False),
        *predicates)

def get_nearest_non_friendly_projectile_that_is(
    hero: Character, 
    *predicates: Callable[[GameEntity], bool]) -> Union[None, GameEntity]:
    '''Public: Gets the nearest enemy projectile that fulfils all conditions'''
    return get_nearest_entity_that_is(hero,
        lambda entity: not friendly_between(entity, hero),
        lambda entity: entity_type_of_any(
            entity, arrow=True, fireball=False, archer=False, 
            knight=False, wizard=False, orc=False, tower=False, base=False),
        *predicates)

def get_enemy_base(hero: Character) -> GameEntity:
    '''Public: Gets enemy base'''
    entity = get_first_of(get_entities_that_are(hero, 
        lambda entity: enemy_between(hero, entity),
        lambda entity: entity_type_of_any(entity, base=True)))
    if entity: return entity
    entity = get_first_of(get_entities_that_are(hero,
        lambda entity: enemy_between(hero, entity),
        lambda entity: entity_type_of_any(
            entity, arrow=False, fireball=False, archer=True, 
            knight=True, wizard=True, orc=True, tower=False, base=False)))
    if entity: return entity.base
    print('WARN: Cannot find enemy base')
    return MockEntity(
        position=Vector2(
            hero.world.graph.nodes[hero.base.target_node_index].position))

def get_friendly_base(hero: Character) -> GameEntity:
    '''Public: Gets friendly base'''
    return hero.base

# def get_nearest_enemy(hero: Character) -> Union[None, Character]:
#     enemy = hero.world.get_nearest_opponent(hero)
#     return enemy

def line_entity(
    a: Vector2, b: Vector2, bits: int=100, size: int=15) -> MockEntity:
    '''Private: Creates fake line entity'''
    if a == b:
        return MockEntity(
            rect=Rect(int(a.x), int(a.y), 1, 1),
            mask=Mask((1, 1), fill=True))
    # Handle line points
    v = b - a
    p, q = (
        (Vector2(abs(v.x), 0), Vector2(0, abs(v.y)))
        if (v.x < 0) ^ (v.y < 0) else
        (Vector2(0, 0), Vector2(abs(v.x), abs(v.y))))
    # Handle Padding
    size2 = size * 2
    width = int(abs(v.x)) + size2 + 1
    height = int(abs(v.y)) + size2 + 1
    p += Vector2(size)
    q += Vector2(size)
    # Create Mask
    mask = Mask((width, height))
    def set_line_bits(a: Vector2, b: Vector2) -> None:
        xs, ys = linspace(a.x, b.x, bits), linspace(a.y, b.y, bits)
        for x, y in zip(xs, ys):
            x, y = int(x), int(y)
            mask.set_at((x, y))
    offset = v.rotate(90).normalize() * size
    set_line_bits(p - offset, q - offset)
    set_line_bits(p + offset, q + offset)
    return MockEntity(
        rect=Rect(
            int(min(a.x, b.x) - size), 
            int(min(a.y, b.y) - size), 
            width, height),
        mask=mask)

def colliding_with_entities(
    this: GameEntity, others: List[GameEntity]) -> bool:
    '''Private: Checks if an entity collides with a group of entities'''
    collided_entities = pygame.sprite.spritecollide(
        this, others, False, pygame.sprite.collide_mask)
    return bool(collided_entities)

def in_sight_with_target(
    hero: Character, target: Union[Vector2, GameEntity], 
    bits: int=100, size: int=15) -> bool:
    '''Public: Checks if there is no obstacles between hero and target'''
    if isinstance(target, GameEntity): target = target.position
    return not colliding_with_entities(
        line_entity(hero.position, target, bits, size),
        hero.world.obstacles)

def in_sight_with_preaimed_target(
    hero: Character, target: Union[Vector2, GameEntity]) -> bool:
    '''Public: Checks if there is no obstacles between hero and preaimed target'''
    return in_sight_with_target(hero, preaim_entity(hero, target))

###  Proximity  ###
def point_entity(position: Vector2):
    p = position
    return MockEntity(
        rect=Rect(int(p.x), int(p.y), 1, 1),
        mask=Mask((1,1), fill=True))

def touching_target(
    hero: Character,
    target: Union[Vector2, GameEntity]) -> bool:
    '''Public: Checks if hero touches a point of an entity'''
    if isinstance(target, Vector2):
        return hero.rect.collidepoint(target.x, target.y)
    elif isinstance(target, GameEntity):
        return hero.rect.colliderect(target.rect)
    else:
        raise Exception

def within_range_of_target(
    hero: Character, 
    target: Union[Vector2, GameEntity], 
    radius: Union[None, float]=None) -> bool:
    '''Public: Legacy checking entity within range method'''
    return within_range_of_target_center(hero, target, radius)

def within_range_of_target_center(
    hero: Character, 
    target: Union[Vector2, GameEntity], 
    radius: Union[None, float]=None) -> bool:
    '''Public: Checks if target center is within hero's attack range'''
    if isinstance(target, GameEntity): target = target.position
    if radius is None:                 radius = hero.projectile_range
    return within_range_between_positions(hero.position, target, radius)

def within_range_of_target_edge(
    hero: Character,
    target: Union[Vector2, GameEntity],
    radius: Union[None, float]=None,
    allowance: float=5) -> bool:
    '''Public: Checks if target edge is within hero's attack range'''
    if radius is None:
        radius = hero.projectile_range
    return (
        within_range_of_entity(hero, target, radius, allowance)
        if isinstance(target, GameEntity) else
        within_range_of_position(hero, target, radius))

def within_range_of_entity(
    hero: Character, entity: GameEntity, 
    radius: float, allowance: float=5) -> bool:
    '''Public: Checks if entity box is within radius of hero when aimed directly at center of enemy'''
    direction = entity.position - hero.position
    if not direction: return True
    if direction.length() > radius:
        direction.scale_to_length(max(0, radius - allowance))
    target = hero.position + direction
    point = point_entity(target)
    return pygame.sprite.collide_mask(point, entity)

def within_range_of_position(
    hero: Character, position: Vector2, radius: float) -> bool:
    '''Public: Checks if a position is within radius of hero'''
    return within_range_between_positions(hero.position, position, radius)

def within_range_between_positions(
    a: Vector2, b: Vector2, radius: float) -> bool:
    '''Private: Checks if two points are within range'''
    return distance_between(a, b) <= radius

def distance_between(a: Vector2, b: Vector2):
    return (a - b).length()

###  Handle KO  ###
def ko_do_actions(hero: Character) -> Union[None, str]:
    pass

def ko_entry_actions(hero: Character) -> Union[None, str]:
    hero.current_hp = hero.max_hp
    hero.position = Vector2(hero.base.spawn_position)
    hero.velocity = Vector2(0, 0)
    
def ko_check_conditions(hero: Character, respawn_state_name: str) -> Union[None, str]:
    if hero.current_respawn_time <= 0:
        hero.current_respawn_time = hero.respawn_time
        hero.ko = False
        return respawn_state_name
    return None

###  Path Finding  ###
def get_paths(hero: Character) -> List[List[Vector2]]:
    first  = [1, 2, 3]
    second = [0, 8, 9, 10, 11, 4]
    third  = [0, 8, 12, 13, 11, 4]
    fourth = [5, 6, 7]
    return [[
            Vector2(hero.world.graph.nodes[x].position)
            for x in (xs[::-1] if hero.team_id == 1 else xs)]
        for xs in (first, second, third, fourth)]
    # return list(map(
    #     compose(
    #         lambda xs: xs[::-1] if hero.team_id == 1 else xs,
    #         lambda xs: list(map(
    #             lambda i: Vector2(hero.world.graph.nodes[i].position),
    #                 xs))),
    #         (first, second, third, fourth)))

def path_value_from_position(
    path: List[Vector2], position: Vector2) -> Tuple[float, float]:
    '''Private: Maps a position on a path to [0, 1] & returns loss'''
    assert(len(path) >= 2)
    p = position
    # Find distance from vertices
    vp_dists = [(p - v).length() for v in path]
    vp_min_dist_index = argmin(vp_dists)
    vp_min_dist = vp_dists[vp_min_dist_index]
    # Find distance from edges
    ab_pairs = list(pairwise(path))
    ab_dists = [(b - a).length() for a, b in ab_pairs]
    ab_projs = [proj(p - a, b - a) for a, b in ab_pairs]
    ba_projs = [proj(p - b, a - b) for a, b in ab_pairs]
    ab_rejs = [rej(p - a, b - a) for a, b in ab_pairs]
    abp_dists = [
        ab_rej
        if ab_proj < ab_dist and ba_proj < ab_dist
        else float('inf')
        for ab_dist, ab_proj, ba_proj, ab_rej
        in zip(ab_dists, ab_projs, ba_projs, ab_rejs)]
    abp_min_dist_index = argmin(abp_dists)
    abp_min_dist = abp_dists[abp_min_dist_index]
    # Compare which has smaller distance
    ab_acc_dists = list(accumulate(ab_dists))
    path_dist = ab_acc_dists[-1]
    v_acc_dist = lambda index: ab_acc_dists[index - 1] if index else 0
    p_dist = (
        v_acc_dist(vp_min_dist_index)
        if vp_min_dist <= abp_min_dist else
        (v_acc_dist(abp_min_dist_index) + ab_projs[abp_min_dist_index]))
    path_value = p_dist / path_dist
    return path_value, min(vp_min_dist, abp_min_dist)

def position_from_path_value(
    path: List[Vector2], value: float) -> Vector2:
    '''Private: Find the position of the path value on a path'''
    path_value = value
    ab_vectors = [b - a for a, b in pairwise(path)]
    ab_dists = [ab.length() for ab in ab_vectors]
    ab_acc_dists = list(accumulate(ab_dists))
    path_dist = ab_acc_dists[-1]
    p_dist = path_dist * path_value
    i = next(
        i for i, acc_dist in enumerate(ab_acc_dists) 
        if p_dist <= acc_dist)
    p_proj = p_dist - (ab_acc_dists[i - 1] if i else 0)
    scale_to_length = lambda v, length: v / v.length() * length
    p = path[i] + scale_to_length(ab_vectors[i], p_proj)
    return p

def path_value_of_target_from_path(
    hero: Character, target: Union[Vector2, GameEntity],
    path: Union[int, List[Vector2]]) -> float:
    '''Public: Returns path value of target on path'''
    if isinstance(target, GameEntity): target = target.position
    if isinstance(path, int): path = hero.paths[path]
    path_value, loss = path_value_from_position(path, target)
    return path_value

def best_path_value_from_position(
    paths: Tuple[List[Vector2]], position: Vector2) -> Tuple[int, float]:
    '''Private: Returns most probable path index & the path value of the position'''
    values, losses = zip(*
        [path_value_from_position(path, position) for path in paths])
    path_index = argmin(losses)
    return path_index, values[path_index]

def most_probable_path_that_target_is_on(
    hero: Character, target: Union[Vector2, GameEntity]) -> Tuple[int, float]:
    '''Public: Returns most probable path index & the path value of the target'''
    if isinstance(target, GameEntity): target = target.position
    return best_path_value_from_position(hero.paths, target)

def paths_sorted_by_entities_most_on_then_nearest_to_base(
    hero: Character, entities: List[GameEntity]) -> List[int]:
    '''Public: Returns path indices sorted by most entities on'''
    assert(len(entities) != 0)
    n_paths = len(hero.paths)
    base = get_friendly_base(hero)
    pis, pvs = zip(*[
        most_probable_path_that_target_is_on(hero, entity) 
        for entity in entities])
    base_pvs = [
        path_value_of_target_from_path(hero, base, i)
        for i in range(n_paths)]
    counts = [0] * n_paths
    proximities = [float('inf')] * n_paths
    for pi, pv in zip(pis, pvs):
        counts[pi] += 1
        proximities[pi] = min(proximities[pi], abs(pv - base_pvs[pi]))
    values = list(zip(range(n_paths), counts, proximities))
    values = multisort(
        values,
        keys=[itemgetter(1), itemgetter(2)],
        reverses=[True, False])
    return [value[0] for value in values]

def position_towards_target_using_path(
    hero: Character, target: Union[Vector2, GameEntity]) -> Vector2:
    '''Public: Returns a position on the path towards target'''
    if isinstance(target, GameEntity): target = target.position
    return path_position_a_to_b(
        hero.path, hero.position, target, towards=True)

def position_away_from_target_using_path(
    hero: Character, target: Union[Vector2, GameEntity]) -> Vector2:
    '''Public: Returns a position on the path away from target'''
    if isinstance(target, GameEntity): target = target.position
    return path_position_a_to_b(
        hero.path, hero.position, target, towards=False)

def path_position_a_to_b(
    path: List[Vector2], a: Vector2, b: Vector2, towards: bool,
    epsilon=1e-1, proximity_threshold=-1, loss_threshold=40) -> Vector2:
    '''Private: Returns a position on the path towards or away from target'''
    a_pv, a_loss = path_value_from_position(path, a)
    b_pv, b_loss = path_value_from_position(path, b)
    c_pv = a_pv + (b_pv - a_pv) * epsilon * (1 if towards else -1)
    if towards and (abs(a_pv - b_pv) <= proximity_threshold):
        return b
    if 0 <= c_pv <= 1:
        if a_loss <= loss_threshold:
            return position_from_path_value(path, c_pv)
        else:
            return position_from_path_value(path, a_pv)
    else:
        return b if towards else 2 * a - b

def switchable_to_path(
    hero: Character, path: Union[int, List[Vector2]]) -> bool:
    '''Public: Checks if hero can switch to a path'''
    if isinstance(path, int): path = hero.paths[path]
    pv, loss = path_value_from_position(path, hero.position)
    path_pos = position_from_path_value(path, pv)
    return in_sight_with_target(hero, path_pos, size=20)

def switch_to_path(
    hero: Character, path: Union[int, List[Vector2]]) -> None:
    '''Public: Updates hero to switch to a path'''
    if isinstance(path, int):
        assert(0 <= path < len(hero.paths))
        hero.path = deepcopy(hero.paths[path])
    elif isinstance(path, list):
        assert(len(path) and isinstance(path[0], Vector2))
        hero.path = deepcopy(path)
    else:
        raise Exception

def try_switch_path(hero: Character, path: Union[int, List[Vector2]]):
    if not switchable_to_path(hero, path):
        path, path_value = most_probable_path_that_target_is_on(hero, hero)
    switch_to_path(hero, path)

def hero_path_value(hero: Character):
    base_pv = path_value_of_target_from_path(
        hero, get_friendly_base(hero), hero.path)
    hero_pv = path_value_of_target_from_path(
        hero, hero, hero.path)
    return abs(hero_pv - base_pv)

def path_find_astar(
    hero: Character, src: Union[Vector2, GameEntity], 
    dest: Union[Vector2, GameEntity]) -> List[Vector2]:
    '''Public: Returns a list of positions from source to destination using AStar'''
    if isinstance(src, GameEntity): src = src.position
    if isinstance(dest, GameEntity): dest = dest.position
    graph = hero.world.graph
    nodes = graph.nodes.values()
    find_closest_node = lambda pos: min(
        nodes, key=lambda node: distance_between(pos, node.position))
    src_node = find_closest_node(src)
    dest_node = find_closest_node(dest)
    conns = pathFindAStar(graph, src_node, dest_node)
    path = [Vector2(conn.fromNode.position) for conn in conns]
    path.append(Vector2(conns[-1].toNode.position))
    return path

def path_find_astar_from_hero_to_target(
    hero: Character, dest: Union[Vector2, GameEntity]) -> List[Vector2]:
    '''Public: Returns a list of position from hero position to target using AStar'''
    return path_find_astar(hero, hero.position, dest)

###  Utils  ###
def compose(*fs):
    compose2 = lambda f, g: lambda *args, **kwargs: g(f(*args, **kwargs))
    return reduce(compose2, fs)

def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

def rej(a: Vector2, b: Vector2) -> float:
    return abs(a.cross(b.normalize()))

def proj(a: Vector2, b: Vector2) -> float:
    return a.dot(b.normalize())

def argmin(iterable, key=None):
    i, val = min(enumerate(iterable), key=lambda x: x[1])
    return i

def argmax(iterable, key=None):
    i, val = max(enumerate(iterable), key=lambda x: x[1])
    return i

def linspace(start: float, stop: float, num: int) -> List[float]:
    width = (stop - start) / (num - 1)
    return [start + width * i for i in range(num)]

def get_first_of(iterable):
    try:
        return next(iter(iterable))
    except StopIteration:
        return None

def find_first_of(iterable, predicate):
    return next(filter(predicate, iterable), None)

def item_unique(iterable, item):
    count = iterable.count(item)
    if count == 0: raise Exception
    return count == 1

def multisort(values, keys, reverses):
    values = values.copy()
    for key, reverse in zip(reversed(keys), reversed(reverses)):
        values.sort(key=key, reverse=reverse)
    return values

def mask_to_surface(mask: Mask, color=(0,0,0,255)) -> Surface:
    width, height = mask.get_size()
    surface = Surface((width, height)) # pylint: disable=too-many-function-args
    surface.fill((255,255,255,255))
    for x in range(width):
        for y in range(height):
            if mask.get_at((x, y)):
                surface.set_at((x, y), color)
    return surface

def render_line_of_sight(
    hero: Character, target: Union[Vector2, GameEntity], surface: Surface,
    bits: int=300, size: int=15) -> None:
    if isinstance(target, GameEntity): target = target.position
    line = line_entity(hero.position, target, bits=bits, size=size)
    line_surface = mask_to_surface(line.mask)
    surface.blit(line_surface, line.rect)

def vector_radian(v: Vector2) -> float:
    return atan2(v.y, v.x)

def box_radius(width, height, rad):
    cosr, sinr = cos(rad), sin(rad)
    brx = abs(width / cosr) if cosr else float('inf')
    bry = abs(height / sinr) if sinr else float('inf')
    return min(brx, bry)

###  Unused  ###
# def projection_length_signed(a: Vector2, b: Vector2) -> float:
#     v = a.dot(b.normalize())
#     return v.length() * sign_between_parallel_vectors(v, b)

# def sign_between_parallel_vectors(a: Vector2, b: Vector2) -> int:
#     neg = lambda x: True if x < 0 else False
#     x_neg = neg(a.x / b.x)
#     y_neg = neg(a.y / b.y)
#     if x_neg or y_neg:
#         return -1
#     else:
#         return 1