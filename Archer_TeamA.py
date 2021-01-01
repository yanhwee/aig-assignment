import pygame
from random import randint, random
from Graph import *
from Character import *
from State import *
import g

DEFAULT_PATH = 3
PROJECTILE_RETREAT_RADIUS = 150
LOW_HP = 190

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
        seeking_state = ArcherStateSeeking_TeamA(self)
        skirmishing_state = ArcherStateSkirmishing_TeamA(self)
        retreating_state = ArcherStateRetreating_TeamA(self)
        healing_state = ArcherStateHealing_TeamA(self)
        ko_state = ArcherStateKO_TeamA(self)
        self.brain.add_state(seeking_state)
        self.brain.add_state(skirmishing_state)
        self.brain.add_state(retreating_state)
        self.brain.add_state(healing_state)
        self.brain.add_state(ko_state)
        self.brain.set_state("seeking")

    def render(self, surface):
        Character.render(self, surface)

    def process(self, time_passed):
        Character.process(self, time_passed)
        if self.can_level_up():
            self.level_up('ranged cooldown')

class ArcherStateSeeking_TeamA(State):
    def __init__(self, archer):
        State.__init__(self, 'seeking')
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
        # Go towards enemy base
        enemy_base = g.get_enemy_base(self.archer)
        if enemy_base:
            path_pos = g.position_towards_target_using_path(self.archer, enemy_base)
            g.set_move_target(self.archer, path_pos)
        # Updates Velocity
        g.update_velocity(self.archer)

    def check_conditions(self):
        # Checks for non-friendly (enemy and neutral) projectiles
        enemy_projectile = g.get_nearest_non_friendly_projectile_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity, radius=PROJECTILE_RETREAT_RADIUS),
            lambda entity: g.in_sight_with_target(self.archer, entity))
        if enemy_projectile:
            return 'retreating'
        # Checks for low hp
        if self.archer.current_hp <= LOW_HP:
            return 'healing'
        # Checks for enemy
        enemy = g.get_nearest_enemy_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity),
            lambda entity: g.in_sight_with_preaimed_target(self.archer, entity))
        if enemy:
            return 'skirmishing'
        return None

class ArcherStateSkirmishing_TeamA(State):
    def __init__(self, archer):
        State.__init__(self, 'skirmishing')
        self.archer = archer

    def entry_actions(self):
        pass

    def do_actions(self):
        # Checks for enemy
        enemy = g.get_nearest_enemy_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity),
            lambda entity: g.in_sight_with_preaimed_target(self.archer, entity))
        if enemy:
            # Preaim Enemy Position
            preaim_position = g.preaim_entity(self.archer, enemy)
            # Shoot projectile
            self.archer.ranged_attack(preaim_position)
            # Move Away from target
            path_pos = g.position_away_from_target_using_path(self.archer, enemy)
            g.set_move_target(self.archer, path_pos)
        # Update Velocity
        g.update_velocity(self.archer)

    def check_conditions(self):
        # Checks for non-friendly (enemy and neutral) projectiles
        enemy_projectile = g.get_nearest_non_friendly_projectile_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity, radius=PROJECTILE_RETREAT_RADIUS),
            lambda entity: g.in_sight_with_target(self.archer, entity))
        if enemy_projectile:
            return 'retreating'
        # Checks for low hp
        if self.archer.current_hp <= LOW_HP:
            return 'healing'
        # Checks for enemy
        enemy = g.get_nearest_enemy_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity),
            lambda entity: g.in_sight_with_preaimed_target(self.archer, entity))
        if enemy is None:
            return 'seeking'
        return None

class ArcherStateRetreating_TeamA(State):
    def __init__(self, archer):
        State.__init__(self, 'retreating')
        self.archer = archer

    def entry_actions(self):
        pass

    def do_actions(self):
        # Checks for non-friendly projectiles
        enemy_projectile = g.get_nearest_non_friendly_projectile_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity, radius=PROJECTILE_RETREAT_RADIUS),
            lambda entity: g.in_sight_with_target(self.archer, entity))
        if enemy_projectile:
            path_pos = g.position_away_from_target_using_path(self.archer, enemy_projectile)
            g.set_move_target(self.archer, path_pos)
        # Updates Velocity
        g.update_velocity(self.archer)

    def check_conditions(self):
        # Checks for low hp
        if self.archer.current_hp <= LOW_HP:
            return 'healing'
        # Checks for non-friendly projectiles
        enemy_projectile = g.get_nearest_non_friendly_projectile_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity, radius=PROJECTILE_RETREAT_RADIUS),
            lambda entity: g.in_sight_with_target(self.archer, entity))
        if enemy_projectile is None:
            return 'seeking'
        return None

class ArcherStateHealing_TeamA(State):
    def __init__(self, archer):
        State.__init__(self, 'healing')
        self.archer = archer

    def entry_actions(self):
        pass

    def do_actions(self):
        self.archer.heal()
    
    def check_conditions(self):
        # Checks for non-friendly projectiles
        enemy_projectile = g.get_nearest_non_friendly_projectile_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity, radius=PROJECTILE_RETREAT_RADIUS),
            lambda entity: g.in_sight_with_target(self.archer, entity))
        if enemy_projectile:
            return 'retreating'
        # Checks for enemy
        enemy = g.get_nearest_enemy_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity),
            lambda entity: g.in_sight_with_preaimed_target(self.archer, entity))
        if enemy:
            return 'skirmishing'
        else:
            return 'seeking'
        return None

class ArcherStateKO_TeamA(State):
    def __init__(self, archer):
        State.__init__(self, "ko")
        self.archer = archer

    def do_actions(self):
        return g.ko_do_actions(self.archer)

    def check_conditions(self):
        return g.ko_check_conditions(self.archer, 'seeking')

    def entry_actions(self):
        return g.ko_entry_actions(self.archer)