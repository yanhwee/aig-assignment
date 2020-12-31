import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *
import g

class Wizard_TeamA(Character):

    def __init__(self, world, image, projectile_image, base, position, explosion_image = None):

        Character.__init__(self, world, "wizard", image)

        self.projectile_image = projectile_image
        self.explosion_image = explosion_image
        
        self.base = base
        self.position = position
        #Initializes hero with more custom variables
        g.init_hero(self)
        seeking_state = WizardStateSeeking_TeamA(self)
        attacking_state = WizardStateSkirmishing_TeamA(self)
        ko_state = WizardStateKO_TeamA(self)
        healing_state = WizardStateHealing_TeamA(self)

        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)
        self.brain.add_state(healing_state)

        self.brain.set_state("seeking")

    def render(self, surface):

        Character.render(self, surface)


    def process(self, time_passed):
        
        Character.process(self, time_passed)

        best = get_best_score(self, 
        lambda entity:health_level_up_evaluate(entity),
        lambda entity:damage_level_up_evaluate(entity)  )
        

        level_up_stats = ["hp", "speed", "ranged damage", "ranged cooldown", "projectile range"]
        if self.can_level_up():
            choice = randint(0, len(level_up_stats) - 1)
            self.level_up(level_up_stats[choice])      



class WizardStateSeeking_TeamA(State):

    def __init__(self, wizard):

        State.__init__(self, "seeking")
        self.wizard = wizard

    def entry_actions(self):

        if g.switchable_to_path(self.wizard, 3):
            g.switch_to_path(self.wizard, 3)
        else:
            path_index, path_value = \
                g.most_probable_path_that_target_is_on(
                    self.wizard, self.wizard)
            g.switch_to_path(self.wizard, path_index)

    def do_actions(self):
        #Get enemy base
        #moves towards it
        enemy_base = g.get_enemy_base(self.wizard)
        path_pos = g.position_towards_target_using_path(self.wizard, enemy_base)
        g.set_move_target(self.wizard, path_pos)
        g.update_velocity(self.wizard)
       

    def check_conditions(self):

        # healing takes priority over skirmishing 
        if self.wizard.current_hp < 0.5 * (self.wizard.max_hp):
            return "healing"

        enemy = g.get_nearest_enemy_that_is(self.wizard,
            lambda entity: g.within_range_of_target(self.wizard, entity),
            lambda entity: g.in_sight_with_preaimed_target(self.wizard, entity))
        if enemy:
            return 'skirmishing'


        return None

       

    
class WizardStateSkirmishing_TeamA(State):

    def __init__(self, wizard):

        State.__init__(self, "skirmishing")
        self.wizard = wizard
        self.enemy = None


    def entry_actions(self):
        pass

    def do_actions(self):
        
        self.enemy = g.get_nearest_enemy_that_is(self.wizard,
            lambda entity: g.within_range_of_target(self.wizard, entity),
            lambda entity: g.in_sight_with_preaimed_target(self.wizard, entity))

    
        if self.enemy:
            preaim_position = g.preaim_entity(self.wizard, self.enemy)

            #send the explosive to that direction
            self.wizard.ranged_attack(preaim_position, self.wizard.explosion_image)
            path_pos = g.position_away_from_target_using_path(self.wizard, self.enemy)
            g.set_move_target(self.wizard, path_pos)
            g.update_velocity(self.wizard)


    def check_conditions(self):

        # target is within sight AND is within the range of the target
        #enemy = g.get_nearest_enemy_that_is(self.wizard,
        #    lambda entity: g.within_range_of_target(self.wizard, entity),
        #    lambda entity: g.in_sight_with_preaimed_target(self.wizard, entity))

        if self.enemy is None:
            return 'seeking'

        return None
            
    def exit_actions(self):
        self.enemy = None
       

class WizardStateKO_TeamA(State):

    def __init__(self, wizard):

        State.__init__(self, "ko")
        self.wizard = wizard

  
    def do_actions(self):
        return g.ko_do_actions(self.wizard)

    def check_conditions(self):
        return g.ko_check_conditions(self.wizard, 'seeking')

    def entry_actions(self):
        return g.ko_entry_actions(self.wizard)


class WizardStateHealing_TeamA(State):
    def __init__(self, wizard):

        State.__init__(self, "healing")
        self.wizard = wizard

    def do_actions(self):

        #Run away and heal if the enemy is close to the wizard
        enemy = g.get_nearest_enemy_that_is(self.wizard,
            lambda entity: g.within_range_of_target(self.wizard, entity),
            lambda entity: g.in_sight_with_preaimed_target(self.wizard, entity))

        if enemy:
            path_pos = g.position_away_from_target_using_path(self.wizard, enemy)
            g.set_move_target(self.wizard, path_pos)
            g.update_velocity(self.wizard)
        else:
            #Stand put at position
            self.wizard.velocity = Vector2(0,0)


        #heal while standing or moving 
        self.wizard.heal()
        
    def check_conditions(self):

        if self.wizard.current_hp >= self.wizard.max_hp:
            return "seeking"
        return None

    def entry_actions(self):
        pass



'''
    Experimental features
    Uses goal based design 
    Evaluates which goal is the most impt
'''
class character_feature(object):
    """
    Calculates ratings for the different level up attributes
    Note: This is an experimentation, equation is subject to change

    """
    def get_rating_health(character:Character)->int:
        health = (character.current_hp / character.max_hp) * 1
        return min(1, health)

    def get_weapon_damage_per_second(character:Character)->int:
        
        rating = (character.ranged_damage/character.ranged_cooldown)/character.ranged_damage
        return min(1, rating)


def health_level_up_evaluate(character:Character) -> int:
    '''How powerful is the bot feeling?'''
    tweaker = 0.1 #how important is this level up attribute to the hero

    desire = tweaker * ((1-character_feature.get_rating_health(character))/character.healing_cooldown)
    return [min(1,desire), 'hp']


def damage_level_up_evaluate(character:Character) -> int:
    '''How far is it from the base?'''
    tweaker = 0.25

    #nearer to the base to more I want to upgrade my damage output
    enemy_base = g.get_enemy_base(character)
    dist_base_and_enemy_base = g.distance_between(g.get_friendly_base(character).position, enemy_base.position)
    dist = g.distance_between(character.position, enemy_base.position)
    desire = (tweaker  *(1- character_feature.get_weapon_damage_per_second(character)))/(dist/dist_base_and_enemy_base)
    return [min(1,desire), 'ranged damage']



def get_best_score(
    hero: Character,
    *predicates):
    ''' ooo functional programming ehuehue'''
    print([pred(hero) for pred in predicates])
    return [max(pred(hero) for pred in predicates)]
