import pygame
from random import randint, random
from Graph import *
from Character import *
from State import *
import g

INITIAL_STATE = 'seeking'

DEFAULT_PATH = 3
MAX_PATH_VALUE_TO_CONSIDER_TO_SWITCH_PATH = 0.5
PATHS_TO_CONSIDER_TO_SWITCH_TO = [0,1,2,3]

LOW_HP = 75
# HIGH_HP = 200

HEALING_NO_ENEMY_RADIUS = 150
HEALING_PROJECTILE_RETREAT_RADIUS = 200
HEALING_ENEMY_RETREAT_RADIUS = 200

BASE_ATTACKING_PROJECTILE_RETREAT_RADIUS = 0
BASE_ATTACKING_ENEMY_RETREAT_RADIUS = 150

ATTACKING_PROJECTILE_RETREAT_RADIUS = 140
ATTACKING_ENEMY_RETREAT_RADIUS = 185

SEEKING_PROJECTILE_RETREAT_RADIUS = 140

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
        full_control_state = ArcherStateFullControl_TeamA(self)
        healing_state = ArcherStateHealing_TeamA(self)
        base_attacking_state = ArcherStateBaseAttacking_TeamA(self)
        attacking_state = ArcherStateAttacking_TeamA(self)
        seeking_state = ArcherStateSeeking_TeamA(self)
        ko_state = ArcherStateKO_TeamA(self)
        self.brain.add_state(full_control_state)
        self.brain.add_state(healing_state)
        self.brain.add_state(base_attacking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(seeking_state)
        self.brain.add_state(ko_state)
        self.brain.set_state(INITIAL_STATE)

    def render(self, surface):
        Character.render(self, surface)

    def process(self, time_passed):
        Character.process(self, time_passed)
        if self.can_level_up():
            self.level_up('ranged cooldown')

    # Helper Functions
    def get_friendly_base(self):
        return g.get_friendly_base(self)

    def get_enemy_base(self):
        return g.get_enemy_base(self)

    def nearest_projectile_in_sight(self):
        return g.get_nearest_non_friendly_projectile_that_is(self,
            lambda entity: g.in_sight_with_target(self, entity))
    
    def nearest_enemy_in_sight(self):
        return g.get_nearest_enemy_that_is(self,
            lambda entity: g.in_sight_with_target(self, entity))

    def nearest_preaimed_enemy_in_sight(self):
        return g.get_nearest_enemy_that_is(self,
            lambda entity: g.in_sight_with_preaimed_target(self, entity))

    def pos_away_from(self, target):
        return g.position_away_from_target_using_path(self, target)

    def pos_towards(self, target):
        return g.position_towards_target_using_path(self, target)

    def move_away_from(self, target):
        g.set_move_target(self, self.pos_away_from(target))

    def move_towards(self, target):
        g.set_move_target(self, self.pos_towards(target))

    def dont_move(self):
        g.set_move_target(self, None)

    def update_velocity(self):
        g.update_velocity(self)

    def near_to(self, target, radius=None):
        '''Use projectile_range if radius is None'''
        return target and g.within_range_of_target_edge(self, target, radius)

    def common_check_conditions(self):
        enemy_base = self.get_enemy_base()
        enemy = self.nearest_enemy_in_sight()
        enemy2 = self.nearest_preaimed_enemy_in_sight()
        low_hp = self.current_hp <= LOW_HP
        if low_hp and not self.near_to(enemy, HEALING_NO_ENEMY_RADIUS):
            return 'healing'
        elif self.near_to(enemy_base):
            return 'base_attacking'
        elif self.near_to(enemy2):
            return 'attacking'
        else:
            return 'seeking'

class ArcherStateHealing_TeamA(State):
    def __init__(self, archer: Archer_TeamA):
        State.__init__(self, 'healing')
        self.archer = archer

    def entry_actions(self):
        pass

    def do_actions(self):
        self.archer.heal()
        projectile = self.archer.nearest_projectile_in_sight()
        enemy = self.archer.nearest_enemy_in_sight()
        enemy_base = self.archer.get_enemy_base()
        if self.archer.near_to(projectile, HEALING_PROJECTILE_RETREAT_RADIUS):
            self.archer.move_away_from(projectile)
        elif self.archer.near_to(enemy, HEALING_ENEMY_RETREAT_RADIUS):
            self.archer.move_away_from(enemy)
        else:
            self.archer.move_towards(enemy_base)
        self.archer.update_velocity()

    def check_conditions(self):
        state = self.archer.common_check_conditions()
        return None if state == 'healing' else state

class ArcherStateBaseAttacking_TeamA(State):
    def __init__(self, archer: Archer_TeamA):
        State.__init__(self, 'base_attacking')
        self.archer = archer

    def entry_actions(self):
        pass

    def do_actions(self):
        projectile = self.archer.nearest_projectile_in_sight()
        enemy = self.archer.nearest_enemy_in_sight()
        enemy_base = self.archer.get_enemy_base()
        if enemy_base:
            self.archer.ranged_attack(enemy_base.position)
        if self.archer.near_to(projectile, BASE_ATTACKING_PROJECTILE_RETREAT_RADIUS):
            self.archer.move_away_from(projectile)
        elif self.archer.near_to(enemy, BASE_ATTACKING_ENEMY_RETREAT_RADIUS):
            self.archer.move_away_from(enemy)
        else:
            self.archer.dont_move()
        self.archer.update_velocity()

    def check_conditions(self):
        state = self.archer.common_check_conditions()
        return None if state == 'base_attacking' else state

class ArcherStateAttacking_TeamA(State):
    def __init__(self, archer: Archer_TeamA):
        State.__init__(self, 'attacking')
        self.archer = archer

    def entry_actions(self):
        pass

    def do_actions(self):
        projectile = self.archer.nearest_projectile_in_sight()
        enemy = self.archer.nearest_enemy_in_sight()
        enemy2 = self.archer.nearest_preaimed_enemy_in_sight()
        if enemy2:
            preaim_pos = g.preaim_entity(self.archer, enemy2)
            self.archer.ranged_attack(preaim_pos)
        if self.archer.near_to(projectile, ATTACKING_PROJECTILE_RETREAT_RADIUS):
            self.archer.move_away_from(projectile)
        elif self.archer.near_to(enemy, ATTACKING_ENEMY_RETREAT_RADIUS):
            self.archer.move_away_from(enemy)
        else:
            self.archer.dont_move()
        self.archer.update_velocity()

    def check_conditions(self):
        state = self.archer.common_check_conditions()
        return None if state == 'attacking' else state

class ArcherStateSeeking_TeamA(State):
    def __init__(self, archer: Archer_TeamA):
        State.__init__(self, 'seeking')
        self.archer = archer

    def entry_actions(self):
        g.try_switch_path(self.archer, DEFAULT_PATH)

    def consider_which_path_to_switch_to(self):
        if g.hero_path_value(self.archer) < MAX_PATH_VALUE_TO_CONSIDER_TO_SWITCH_PATH:
            enemies = g.get_enemy_heroes(self.archer)
            if enemies:
                paths = g.paths_sorted_by_entities_most_on_then_nearest_to_base(
                    self.archer, enemies)
                path = g.find_first_of(
                    paths, lambda path: path in PATHS_TO_CONSIDER_TO_SWITCH_TO)
                return path
        return None

    def do_actions(self):
        path = self.consider_which_path_to_switch_to()
        if path is not None:
            g.try_switch_path(self.archer, path)
        #
        projectile = self.archer.nearest_projectile_in_sight()
        enemy_base = self.archer.get_enemy_base()
        if self.archer.near_to(projectile, SEEKING_PROJECTILE_RETREAT_RADIUS):
            self.archer.move_away_from(projectile)
        else:
            self.archer.move_towards(enemy_base)
        self.archer.update_velocity()

    def check_conditions(self):
        state = self.archer.common_check_conditions()
        return None if state == 'seeking' else state

class ArcherStateKO_TeamA(State):
    def __init__(self, archer: Archer_TeamA):
        State.__init__(self, "ko")
        self.archer = archer

    def entry_actions(self):
        g.ko_entry_actions(self.archer)

    def do_actions(self):
        g.ko_do_actions(self.archer)

    def check_conditions(self):
        return g.ko_check_conditions(self.archer, INITIAL_STATE)

class ArcherStateFullControl_TeamA(State):
    def __init__(self, archer):
        State.__init__(self, 'full_control')
        self.archer = archer

    def entry_actions(self):
        g.try_switch_path(self.archer, DEFAULT_PATH)
    
    def do_actions(self):
        # Pathfinding
        path = None
        if g.hero_path_value(self.archer) < MAX_PATH_VALUE_TO_CONSIDER_TO_SWITCH_PATH:
            enemies = g.get_enemy_heroes(self.archer)
            if enemies:
                paths = g.paths_sorted_by_entities_most_on_then_nearest_to_base(
                    self.archer, enemies)
                path = g.find_first_of(
                    paths, lambda path: path in PATHS_TO_CONSIDER_TO_SWITCH_TO)
        if path is not None:
            g.try_switch_path(self.archer, path)
        # Functions
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
            target and g.within_range_of_target_edge(self.archer, target, radius)
        # Variables
        enemy_base = g.get_enemy_base(self.archer)
        projectile = g.get_nearest_non_friendly_projectile_that_is(self.archer,
            lambda entity: g.in_sight_with_target(self.archer, entity))
        enemy = g.get_nearest_enemy_that_is(self.archer,
            lambda entity: g.in_sight_with_target(self.archer, entity))
        enemy2 = g.get_nearest_enemy_that_is(self.archer,
            lambda entity: g.in_sight_with_preaimed_target(self.archer, entity))
        low_hp = self.archer.current_hp <= LOW_HP
        # Heal
        if low_hp and not near_to(enemy, HEALING_NO_ENEMY_RADIUS):
            self.archer.heal()
            if near_to(projectile, HEALING_PROJECTILE_RETREAT_RADIUS):
                move_away_from(projectile)
            elif near_to(enemy, HEALING_ENEMY_RETREAT_RADIUS):
                move_away_from(enemy)
            else:
                move_towards(enemy_base)
        # Attack Base
        elif near_to(enemy_base, None):
            self.archer.ranged_attack(enemy_base.position)
            if near_to(projectile, BASE_ATTACKING_PROJECTILE_RETREAT_RADIUS):
                move_away_from(projectile)
            elif near_to(enemy, BASE_ATTACKING_ENEMY_RETREAT_RADIUS):
                move_away_from(enemy)
            else:
                dont_move()
        # Attack Enemy
        elif near_to(enemy2, None):
            preaim_pos = g.preaim_entity(self.archer, enemy2)
            self.archer.ranged_attack(preaim_pos)
            if near_to(projectile, ATTACKING_PROJECTILE_RETREAT_RADIUS):
                move_away_from(projectile)
            elif near_to(enemy, ATTACKING_ENEMY_RETREAT_RADIUS):
                move_away_from(enemy)
            else:
                dont_move()
        # Seek
        else:
            if near_to(projectile, SEEKING_PROJECTILE_RETREAT_RADIUS):
                move_away_from(projectile)
            else:
                move_towards(enemy_base)
        # Update Velocity
        g.update_velocity(self.archer)

    def check_conditions(self):
        return None