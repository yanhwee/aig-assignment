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
        attacking_state = ArcherStateAttacking_TeamA(self)
        ko_state = ArcherStateKO_TeamA(self)
        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
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
        State.__init__(self, "seeking")
        self.archer = archer
        self.archer.path_graph = self.archer.world.paths[randint(0, len(self.archer.world.paths)-1)]

    def do_actions(self):
        g.update_velocity(self.archer)

    def check_conditions(self):
        # check if opponent is in range
        enemy = g.get_nearest_enemy_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity),
            lambda entity: g.in_sight_with_target(self.archer, entity))
        if enemy:
            return 'attacking'
        # move towards enemy base
        enemy_base = g.get_enemy_base(self.archer)
        path_pos = g.position_towards_target_using_path(self.archer, enemy_base)
        g.set_move_target(self.archer, path_pos)
        return None

    def entry_actions(self):

        g.switch_to_path(self.archer, 3)
        
        # nearest_node = self.archer.path_graph.get_nearest_node(self.archer.position)
        # self.path = pathFindAStar(self.archer.path_graph, \
        #                           nearest_node, \
        #                           self.archer.path_graph.nodes[self.archer.base.target_node_index])
        # make_node = lambda pos: Node(None, None, *pos)
        # make_conn = lambda from_pos, to_pos: Connection(None, None, make_node(from_pos), make_node(to_pos))
        # self.path = [make_conn(a, b) for a, b in g.pairwise(self.archer.paths[0])]
        # self.path_length = len(self.path)
        # if (self.path_length > 0):
        #     self.current_connection = 0
        #     g.set_move_target(self.archer, self.path[0].fromNode.position)
        # else:
        #     self.archer.move_target.position = self.archer.path_graph.nodes[self.archer.base.target_node_index].position

class ArcherStateAttacking_TeamA(State):
    def __init__(self, archer):
        State.__init__(self, "attacking")
        self.archer = archer

    def do_actions(self):
        # check if opponent is in range
        enemy = g.get_nearest_enemy_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity),
            lambda entity: g.in_sight_with_target(self.archer, entity))
        if enemy:
            preaim_position = g.preaim_entity(self.archer, enemy)
            self.archer.ranged_attack(preaim_position)
            path_pos = g.position_away_from_target_using_path(self.archer, enemy)
            g.set_move_target(self.archer, path_pos)
            g.update_velocity(self.archer)

    def check_conditions(self):
        # Check if enemy is out of range
        enemy = g.get_nearest_enemy_that_is(self.archer,
            lambda entity: g.within_range_of_target(self.archer, entity),
            lambda entity: g.in_sight_with_target(self.archer, entity))
        if enemy is None:
            return 'seeking'
        return None

    def entry_actions(self):
        g.set_move_target(self.archer, None)
        g.update_velocity(self.archer)
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