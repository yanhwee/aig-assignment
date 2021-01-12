import pygame
from random import randint, random
from Graph import *
from Character import *
from State import *
import g

DEFAULT_PATH = 3
SKIRMISHING_PROJECTILE_RETREAT_RADIUS = 150
SKIRMISHING_ENEMY_RETREAT_RADIUS = 155
HEALING_NO_ENEMY_RADIUS = 160
HEALING_PROJECTILE_RETREAT_RADIUS = 150
HEALING_ENEMY_RETREAT_RADIUS = 220
LOW_HP = 199
HIGH_HP = 200

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
        healing_state = ArcherStateHealing_TeamA(self)
        ko_state = ArcherStateKO_TeamA(self)
        self.brain.add_state(skirmishing_state)
        self.brain.add_state(healing_state)
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
        # Switch to default path if possible else carry on with path
        if g.switchable_to_path(self.archer, DEFAULT_PATH):
            g.switch_to_path(self.archer, DEFAULT_PATH)
        else:
            path_index, path_value = \
                g.most_probable_path_that_target_is_on(
                    self.archer, self.archer)
            g.switch_to_path(self.archer, path_index)

    def do_actions(self):
        # Get Targets
        enemy_base = g.get_enemy_base(self.archer)
        enemy = g.get_nearest_enemy_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity),
            lambda entity: g.in_sight_with_preaimed_target(self.archer, entity))
        projectile = g.get_nearest_non_friendly_projectile_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity, SKIRMISHING_PROJECTILE_RETREAT_RADIUS),
            lambda entity: g.in_sight_with_target(self.archer, entity))
        # Attack
        if g.within_range_of_target(self.archer, enemy_base):
            self.archer.ranged_attack(enemy_base.position)
        elif enemy:
            preaim_position = g.preaim_entity(self.archer, enemy)
            self.archer.ranged_attack(preaim_position)
        # Move
        if projectile:
            path_pos = g.position_away_from_target_using_path(self.archer, projectile)
            g.set_move_target(self.archer, path_pos)
        elif enemy is None:
            path_pos = g.position_towards_target_using_path(self.archer, enemy_base)
            g.set_move_target(self.archer, path_pos)
        elif g.within_range_of_target(self.archer, enemy, SKIRMISHING_ENEMY_RETREAT_RADIUS):
            path_pos = g.position_away_from_target_using_path(self.archer, enemy)
            g.set_move_target(self.archer, path_pos)
        else:
            g.set_move_target(self.archer, None)
        g.update_velocity(self.archer)

    def check_conditions(self):
        if self.archer.current_hp <= LOW_HP:
            enemy = g.get_nearest_enemy_that_is(self.archer,
                lambda entity: g.within_range_of_target(self.archer, entity, HEALING_NO_ENEMY_RADIUS),
                lambda entity: g.in_sight_with_target(self.archer, entity))
            if enemy is None:
                return 'healing'
        return None

class ArcherStateHealing_TeamA(State):
    def __init__(self, archer):
        State.__init__(self, 'healing')
        self.archer = archer

    def entry_actions(self):
        pass

    def do_actions(self):
        self.archer.heal()
        # Get Targets
        enemy_base = g.get_enemy_base(self.archer)
        enemy = g.get_nearest_enemy_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity),
            lambda entity: g.in_sight_with_preaimed_target(self.archer, entity))
        projectile = g.get_nearest_non_friendly_projectile_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity, HEALING_PROJECTILE_RETREAT_RADIUS),
            lambda entity: g.in_sight_with_target(self.archer, entity))
        # Move
        if projectile:
            path_pos = g.position_away_from_target_using_path(self.archer, projectile)
            g.set_move_target(self.archer, path_pos)
        elif enemy is None:
            path_pos = g.position_towards_target_using_path(self.archer, enemy_base)
            g.set_move_target(self.archer, path_pos)
        elif g.within_range_of_target(self.archer, enemy, HEALING_ENEMY_RETREAT_RADIUS):
            path_pos = g.position_away_from_target_using_path(self.archer, enemy)
            g.set_move_target(self.archer, path_pos)
        g.update_velocity(self.archer)
    
    def check_conditions(self):
        if self.archer.current_hp >= HIGH_HP:
            return 'skirmishing'
        enemy = g.get_nearest_enemy_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity, HEALING_NO_ENEMY_RADIUS),
            lambda entity: g.in_sight_with_target(self.archer, entity))
        if enemy:
            return 'skirmishing'
        return None

class ArcherStateKO_TeamA(State):
    def __init__(self, archer):
        State.__init__(self, "ko")
        self.archer = archer

    def do_actions(self):
        return g.ko_do_actions(self.archer)

    def check_conditions(self):
        return g.ko_check_conditions(self.archer, 'skirmishing')

    def entry_actions(self):
        return g.ko_entry_actions(self.archer)