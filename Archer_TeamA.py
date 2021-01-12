import pygame
from random import randint, random
from Graph import *
from Character import *
from State import *
import g

DEFAULT_PATH = 3

LOW_HP = 199
HIGH_HP = 200

HEALING_NO_ENEMY_RADIUS = 160
HEALING_PROJECTILE_RETREAT_RADIUS = 150
HEALING_ENEMY_RETREAT_RADIUS = 220

BASE_ATTACKING_PROJECTILE_RETREAT_RADIUS = 150
BASE_ATTACKING_ENEMY_RETREAT_RADIUS = 155

ATTACKING_PROJECTILE_RETREAT_RADIUS = 150
ATTACKING_ENEMY_RETREAT_RADIUS = 155

SEEKING_PROJECTILE_RETREAT_RADIUS = 150

class Archer_TeamA(Character):
    def __init__(self, world, image, projectile_image, base, position):
        ## Immutable
        Character.__init__(self, world, "archer", image)
        self.projectile_image = projectile_image
        self.base = base
        self.position = position
        ## Mutable
        # G Init
        g.init_hero(self)
        # State Machine
        skirmishing_state = ArcherStateSkirmishing_TeamA(self)
        ko_state = ArcherStateKO_TeamA(self)
        self.brain.add_state(skirmishing_state)
        self.brain.add_state(ko_state)
        self.brain.set_state('skirmishing')

    def render(self, surface):
        Character.render(self, surface)

    def process(self, time_passed):
        Character.process(self, time_passed)
        if self.can_level_up():
            self.level_up('ranged cooldown')

class ArcherStateSkirmishing_TeamA(State):
    def __init__(self, archer):
        State.__init__(self, 'skirmishing')
        self.archer = archer

    def entry_actions(self):
        if g.switchable_to_path(self.archer, DEFAULT_PATH):
            g.switch_to_path(self.archer, DEFAULT_PATH)
        else:
            path_index, path_value = \
                g.most_probable_path_that_target_is_on(
                    self.archer, self.archer)
            g.switch_to_path(self.archer, path_index)
    
    def do_actions(self):
        # Functions
        near_projectile = lambda radius: \
            g.get_nearest_non_friendly_projectile_that_is(self.archer,
                lambda entity: g.within_range_of_target(
                    self.archer, entity, radius),
                lambda entity: g.in_sight_with_target(
                    self.archer, entity))
        near_enemy = lambda radius: \
            g.get_nearest_enemy_that_is(self.archer,
                lambda entity: g.within_range_of_target(
                    self.archer, entity, radius),
                lambda entity: g.in_sight_with_target(
                    self.archer, entity))
        pos_away_from = lambda target: \
            g.position_away_from_target_using_path(
                self.archer, target)
        pos_towards = lambda target: \
            g.position_towards_target_using_path(
                self.archer, target)
        move_away_from = lambda target: \
            g.set_move_target(self.archer, pos_away_from(target))
        move_towards = lambda target: \
            g.set_move_target(self.archer, pos_towards(target))
        dont_move = lambda: g.set_move_target(self.archer, None)
        near_to = lambda target, radius: \
            target and g.within_range_of_target(self.archer, target, radius)
        # Variables
        enemy_base = g.get_enemy_base(self.archer)
        enemy = g.get_nearest_enemy_that_is(self.archer,
            lambda entity: g.in_sight_with_target(self.archer, entity))
        low_hp = self.archer.current_hp <= LOW_HP
        # Heal
        if low_hp and not near_to(enemy, HEALING_NO_ENEMY_RADIUS):
            self.archer.heal()
            projectile = near_projectile(HEALING_PROJECTILE_RETREAT_RADIUS)
            enemy = near_enemy(HEALING_ENEMY_RETREAT_RADIUS)
            if projectile:
                move_away_from(projectile)
            elif enemy:
                move_away_from(enemy)
            else:
                move_towards(enemy_base)
        # Attack Base
        elif near_to(enemy_base, None):
            self.archer.ranged_attack(enemy_base.position)
            projectile = near_projectile(BASE_ATTACKING_PROJECTILE_RETREAT_RADIUS)
            enemy = near_enemy(BASE_ATTACKING_ENEMY_RETREAT_RADIUS)
            if projectile:
                move_away_from(projectile)
            elif enemy:
                move_away_from(enemy)
            else:
                dont_move()
        # Attack Enemy
        elif near_to(enemy, None):
            preaim_pos = g.preaim_entity(self.archer, enemy)
            self.archer.ranged_attack(preaim_pos)
            projectile = near_projectile(ATTACKING_PROJECTILE_RETREAT_RADIUS)
            enemy = near_enemy(ATTACKING_ENEMY_RETREAT_RADIUS)
            if projectile:
                move_away_from(projectile)
            elif enemy:
                move_away_from(enemy)
            else:
                dont_move()
        # Seek
        else:
            projectile = near_projectile(SEEKING_PROJECTILE_RETREAT_RADIUS)
            if projectile:
                move_away_from(projectile)
            else:
                move_towards(enemy_base)
        # Update Velocity
        g.update_velocity(self.archer)

    def check_conditions(self):
        return None

class ArcherStateKO_TeamA(State):
    def __init__(self, archer):
        State.__init__(self, "ko")
        self.archer = archer

    def entry_actions(self):
        g.ko_entry_actions(self.archer)

    def do_actions(self):
        g.ko_do_actions(self.archer)

    def check_conditions(self):
        return g.ko_check_conditions(self.archer, 'skirmishing')