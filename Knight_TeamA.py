import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *
import g

DEFAULT_PATH = 3
KNIGHT_SENSING_RADIUS = KNIGHT_MIN_TARGET_DISTANCE
KNIGHT_HEALING_THRESHOLD_LEVEL1 = 50
KNIGHT_HEALING_THRESHOLD_LEVEL2 = 65
KNIGHT_HEALING_THRESHOLD = KNIGHT_HEALING_THRESHOLD_LEVEL1

class Knight_TeamA(Character):

    def __init__(self, world, image, base, position):

        Character.__init__(self, world, "knight", image)

        self.base = base
        self.position = position

        g.init_hero(self)

        #State Machine
        seeking_state = KnightStateSeeking_TeamA(self)
        attacking_state = KnightStateAttacking_TeamA(self)
        ko_state = KnightStateKO_TeamA(self)
        healing_state = KnightStateHealing_TeamA(self)

        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)
        self.brain.add_state(healing_state)

        self.brain.set_state("seeking")
        

    def render(self, surface):

        Character.render(self, surface)


    def process(self, time_passed):
        
        Character.process(self, time_passed)
        level = 0
        if self.can_level_up():
            level += 1
            if level >= 2:
                KNIGHT_HEALING_THRESHOLD = KNIGHT_HEALING_THRESHOLD_LEVEL2
            self.level_up('healing') 


class KnightStateSeeking_TeamA(State):

    def __init__(self, knight):

        State.__init__(self, "seeking")
        self.knight = knight

    def entry_actions(self):

        if g.switchable_to_path(self.knight, DEFAULT_PATH):
            g.switch_to_path(self.knight, DEFAULT_PATH)
        else:
            path_index, path_value = \
                g.most_probable_path_that_target_is_on(
                    self.knight, self.knight)
            g.switch_to_path(self.knight, path_index)

    def do_actions(self): 
        #Move towards base
        enemy_base = g.get_enemy_base(self.knight)
        path_pos = g.position_towards_target_using_path(self.knight,enemy_base)
        g.set_move_target(self.knight,path_pos)
        g.update_velocity(self.knight)


    def check_conditions(self):
       
        #check if hp is full
        if self.knight.current_hp != self.knight.max_hp:
            return "healing"

        # check if enemy is in range
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

        # check enemy base
        enemy_base = g.get_enemy_base(self.knight)

        # if knight touches the enemy base
        if g.touching_target(self.knight, enemy_base):
            attack(self.knight,enemy_base)
        # target and move to enemy base if within range
        elif g.within_range_of_target(self.knight,enemy_base,KNIGHT_SENSING_RADIUS):
            g.set_move_target(self.knight,enemy_base)
            g.update_velocity(self.knight)
        else:
            #check if other enemies exists 
            enemy = g.get_nearest_enemy_that_is(self.knight,
                lambda entity: g.within_range_of_target(self.knight, entity, KNIGHT_SENSING_RADIUS),
                lambda entity: g.in_sight_with_target(self.knight, entity))

            if enemy:
                g.set_move_target(self.knight,enemy)
                g.update_velocity(self.knight)
                # colliding with target
                if g.touching_target(self.knight,enemy):
                    attack(self.knight,enemy)

    def check_conditions(self):

        enemy = g.get_nearest_enemy_that_is(self.knight,
            lambda entity: g.within_range_of_target(self.knight, entity, KNIGHT_SENSING_RADIUS),
            lambda entity: g.in_sight_with_target(self.knight, entity))
        
        # target is gone        
        if enemy is None:
            return "seeking"
        
        # if knight's health below a certain threshold, heal
        if self.knight.current_hp/self.knight.max_hp *100 <= KNIGHT_HEALING_THRESHOLD:
            return "healing"

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


class KnightStateHealing_TeamA(State):

    def __init__(self, knight):

        State.__init__(self,"healing")
        self.knight = knight

    def entry_actions(self):
        
        return None

    def do_actions(self):

        #check if there is enemy
        enemy = g.get_nearest_enemy_that_is(self.knight,
            lambda entity: g.within_range_of_target(self.knight, entity, KNIGHT_SENSING_RADIUS),
            lambda entity: g.in_sight_with_target(self.knight, entity))

        #Set target to none to stand on the spot
        if enemy:
            g.set_move_target(self.knight,None)
            g.update_velocity(self.knight)
        
        #heal
        self.knight.heal()


    def check_conditions(self):

        enemy = g.get_nearest_enemy_that_is(self.knight,
            lambda entity: g.within_range_of_target(self.knight, entity, KNIGHT_SENSING_RADIUS),
            lambda entity: g.in_sight_with_target(self.knight, entity))

        # target is gone
        if enemy is None:
            return "seeking"
        
        # if knight's health above a certain threshold, attack
        if self.knight.current_hp/self.knight.max_hp *100 > KNIGHT_HEALING_THRESHOLD:
            return "attacking"


def attack(hero:Character, enemy:GameEntity):
    g.set_move_target(hero, None)
    hero.melee_attack(enemy)
    g.update_velocity(hero)