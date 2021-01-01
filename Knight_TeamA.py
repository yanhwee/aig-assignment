import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *
import g

DEFAULT_PATH = 3
KNIGHT_SENSING_RADIUS = KNIGHT_MIN_TARGET_DISTANCE

class Knight_TeamA(Character):

    def __init__(self, world, image, base, position):

        Character.__init__(self, world, "knight", image)

        self.base = base
        self.position = position
        self.target = None #temp fix

        g.init_hero(self)

        #State Machine
        seeking_state = KnightStateSeeking_TeamA(self)
        attacking_state = KnightStateAttacking_TeamA(self)
        ko_state = KnightStateKO_TeamA(self)
        retreating_state = KnightStateRetreating_TeamA(self)
        healing_state = KnightStateHealing_TeamA(self)

        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)
        self.brain.add_state(retreating_state)
        self.brain.add_state(healing_state)

        self.brain.set_state("seeking")
        

    def render(self, surface):

        Character.render(self, surface)


    def process(self, time_passed):
        
        Character.process(self, time_passed)

        level_up_stats = ["hp", "speed", "melee damage", "melee cooldown"]
        if self.can_level_up():
            choice = randint(0, len(level_up_stats) - 1)
            #self.level_up(level_up_stats[choice])
            self.level_up('hp')

   


class KnightStateSeeking_TeamA(State):

    def __init__(self, knight):

        State.__init__(self, "seeking")
        self.knight = knight

        #self.knight.path_graph = self.knight.world.paths[randint(0, len(self.knight.world.paths)-1)]


    def entry_actions(self):

        if g.switchable_to_path(self.knight, DEFAULT_PATH):
            g.switch_to_path(self.knight, DEFAULT_PATH)
        else:
            path_index, path_value = \
                g.most_probable_path_that_target_is_on(
                    self.knight, self.knight)
            g.switch_to_path(self.knight, path_index)

    def do_actions(self): #rush
        enemy_base = g.get_enemy_base(self.knight)
        path_pos = g.position_towards_target_using_path(self.knight,enemy_base)
        g.set_move_target(self.knight,path_pos)
        g.update_velocity(self.knight)

    def check_conditions(self):
       
        #check if hp is full
        if self.knight.current_hp != self.knight.max_hp:
            return "healing"

        # check if opponent is in range
        enemy = g.get_nearest_enemy_that_is(self.knight,
            lambda entity: g.within_range_of_target(self.knight, entity, KNIGHT_SENSING_RADIUS),
            lambda entity: g.in_sight_with_target(self.knight, entity))

        if enemy:
            return "attacking"
            
        return None


class KnightStateAttacking_TeamA(State):

    def __init__(self, knight):

        State.__init__(self, "attacking")
        self.knight = knight

    def entry_actions(self):

        return None
    
    def do_actions(self):

        #check enemy
        enemy = g.get_nearest_enemy_that_is(self.knight,
            lambda entity: g.within_range_of_target(self.knight, entity, KNIGHT_SENSING_RADIUS),
            lambda entity: g.in_sight_with_target(self.knight, entity))

        if enemy:
            self.knight.target = enemy
            g.set_move_target(self.knight,enemy)
            # colliding with target
            if g.touching_target(self.knight,enemy):
                g.set_move_target(self.knight,None)
                self.knight.melee_attack(enemy)

        g.update_velocity(self.knight)



    def check_conditions(self):

        # target is gone
        enemy = g.get_nearest_enemy_that_is(self.knight,
            lambda entity: g.within_range_of_target(self.knight, entity, KNIGHT_SENSING_RADIUS),
            lambda entity: g.in_sight_with_target(self.knight, entity))
        if enemy is None:
            return "seeking"
        
        if self.knight.current_hp/self.knight.max_hp *100 <= 30:
            return "retreating"

        return None



class KnightStateKO_TeamA(State):

    def __init__(self, knight):

        State.__init__(self, "ko")
        self.knight = knight

    def entry_actions(self):

        return g.ko_entry_actions(self.knight)

    def do_actions(self):

        return g.ko_do_actions(self.knight)


    def check_conditions(self):
            
        return g.ko_check_conditions(self.knight, 'seeking')



class KnightStateRetreating_TeamA(State):

    def __init__(self, knight):

        State.__init__(self,"retreating")
        self.knight = knight

    def entry_actions(self):
        
        return None

    def do_actions(self):

        #retreat
        enemy = g.get_nearest_enemy_that_is(self.knight,
            lambda entity: g.within_range_of_target(self.knight, entity, KNIGHT_SENSING_RADIUS),
            lambda entity: g.in_sight_with_target(self.knight, entity))
        enemy_projectile = g.get_nearest_non_friendly_projectile_that_is(self.knight,
            lambda entity: g.within_range_of_target(self.knight,entity, KNIGHT_SENSING_RADIUS),
            lambda entity: g.in_sight_with_target(self.knight,entity))
        if enemy_projectile:
            path_pos = g.position_away_from_target_using_path(self.knight,enemy_projectile)
            g.set_move_target(self.knight, path_pos)
        elif enemy:
            path_pos = g.position_away_from_target_using_path(self.knight,enemy)
            g.set_move_target(self.knight, path_pos)
        g.update_velocity(self.knight)



    def check_conditions(self):

        #check if retreat until home base
        # friendly_base = g.get_friendly_base(self.knight)
        # if g.touching_target(self.knight,friendly_base):
        #     return "attacking"
        
        #check if hp is full
        if self.knight.current_hp != self.knight.max_hp:
            return "healing"
        else:
            return "seeking"

class KnightStateHealing_TeamA(State):

    def __init__(self, knight):

        State.__init__(self,"healing")
        self.knight = knight

    def entry_actions(self):
        
        return None

    def do_actions(self):
        #heal
        self.knight.heal()


    def check_conditions(self):

        # target is gone
        enemy = g.get_nearest_enemy_that_is(self.knight,
            lambda entity: g.within_range_of_target(self.knight, entity, KNIGHT_SENSING_RADIUS),
            lambda entity: g.in_sight_with_target(self.knight, entity))
        if enemy:
            return "retreating"
        else:
            return "seeking"

