import pygame
from random import randint, random
from Graph import *
from Character import *
from State import *
import g

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
        ko_state = ArcherStateKO_TeamA(self)
        self.brain.add_state(seeking_state)
        self.brain.add_state(skirmishing_state)
        self.brain.add_state(ko_state)
        self.brain.set_state("seeking")

    def render(self, surface):
        Character.render(self, surface)

    def process(self, time_passed):
        Character.process(self, time_passed)
        level_up_stats = ["hp", "speed", "ranged damage", "ranged cooldown", "projectile range"]
        if self.can_level_up():
            choice = randint(0, len(level_up_stats) - 1)
            self.level_up(level_up_stats[choice])

class ArcherStateSeeking_TeamA(State):
    def __init__(self, archer):
        State.__init__(self, 'seeking')
        self.archer = archer

    def entry_actions(self):
        g.switch_to_path(self.archer, 3)

    def do_actions(self):
        enemy_base = g.get_enemy_base(self.archer)
        path_pos = g.position_towards_target_using_path(self.archer, enemy_base)
        g.set_move_target(self.archer, path_pos)
        g.update_velocity(self.archer)

    def check_conditions(self):
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
        enemy = g.get_nearest_enemy_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity),
            lambda entity: g.in_sight_with_preaimed_target(self.archer, entity))
        if enemy:
            preaim_position = g.preaim_entity(self.archer, enemy)
            self.archer.ranged_attack(preaim_position)
            path_pos = g.position_away_from_target_using_path(self.archer, enemy)
            g.set_move_target(self.archer, path_pos)
            g.update_velocity(self.archer)

    def check_conditions(self):
        enemy = g.get_nearest_enemy_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity),
            lambda entity: g.in_sight_with_preaimed_target(self.archer, entity))
        if enemy is None:
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