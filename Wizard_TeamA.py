import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *
import g

DEFAULT_PATH = 3

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
        retreating_state = WizardStateRetreating_TeamA(self)

        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)
        self.brain.add_state(healing_state)
        self.brain.add_state(retreating_state)

        self.brain.set_state("seeking")

        self.orderedSet = []

    def render(self, surface):

        Character.render(self, surface)


    def process(self, time_passed):
        
        Character.process(self, time_passed)

        best = get_best_score(self, 
        lambda entity:health_level_up_evaluate(entity),
        lambda entity:damage_level_up_evaluate(entity),
        lambda entity:speed_level_up_evaluate(entity))

        if best not in self.orderedSet:
            self.orderedSet.append(best)
        
        #print(self.orderedSet)
        #level_up_stats = ["hp", "speed", "ranged damage", "ranged cooldown", "projectile range"]
        if self.can_level_up():
            self.level_up(self.orderedSet.pop(0))




class WizardStateSeeking_TeamA(State):

    def __init__(self, wizard):

        State.__init__(self, "seeking")
        self.wizard = wizard

    def entry_actions(self):

        if g.switchable_to_path(self.wizard, DEFAULT_PATH):
            g.switch_to_path(self.wizard, DEFAULT_PATH)
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
        if self.wizard.current_hp < 0.8 * (self.wizard.max_hp):
            return "healing"

        enemy = get_enemy_for_cluster_bomb(self.wizard)
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
        
        #self.enemy = g.get_nearest_enemy_that_is(self.wizard,
        #    lambda entity: g.within_range_of_target(self.wizard, entity, self.wizard.min_target_distance),
        #    lambda entity: g.in_sight_with_preaimed_target(self.wizard, entity))
        self.enemy  =  get_enemy_for_cluster_bomb(self.wizard)
    
        if self.enemy:
            preaim_position = g.preaim_entity(self.wizard, self.enemy)
            #send the explosive to that direction
            self.wizard.ranged_attack(preaim_position, self.wizard.explosion_image)
            #path_pos = g.position_away_from_target_using_path(self.wizard, self.enemy)
            #g.set_move_target(self.wizard, path_pos)
            #g.update_velocity(self.wizard)


    def check_conditions(self):

        # target is within sight AND is within the range of the target
        #enemy = g.get_nearest_enemy_that_is(self.wizard,
        #    lambda entity: g.within_range_of_target(self.wizard, entity),
        #    lambda entity: g.in_sight_with_preaimed_target(self.wizard, entity))

        if self.wizard.current_hp < 0.8 * (self.wizard.max_hp):
            return "healing"

        if self.enemy:
            return "retreating"

        if self.enemy is None:
            return 'seeking'

        return None
            
    def exit_actions(self):
        self.enemy = None


class WizardStateRetreating_TeamA(State):

    def __init__(self, wizard):

        State.__init__(self, "retreating")
        self.wizard = wizard
        self.enemy = None


    def entry_actions(self):
        pass

    def do_actions(self):
        
        #self.enemy = g.get_nearest_enemy_that_is(self.wizard,
        #    lambda entity: g.within_range_of_target(self.wizard, entity, self.wizard.min_target_distance),
        #    lambda entity: g.in_sight_with_preaimed_target(self.wizard, entity))
        self.enemy  =  get_enemy_for_cluster_bomb(self.wizard)
    
        if self.enemy:
            path_pos = g.position_away_from_target_using_path(self.wizard, self.enemy)
            g.set_move_target(self.wizard, path_pos)
            g.update_velocity(self.wizard)


    def check_conditions(self):

        # target is within sight AND is within the range of the target
        #enemy = g.get_nearest_enemy_that_is(self.wizard,
        #    lambda entity: g.within_range_of_target(self.wizard, entity),
        #    lambda entity: g.in_sight_with_preaimed_target(self.wizard, entity))

       
        if self.enemy:
            return "skirmishing"

        if self.wizard.current_hp < 0.8 * (self.wizard.max_hp):
            return "healing"

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

        #print("healing")
        self.wizard.heal()
        
    def check_conditions(self):

        self.enemy = get_enemy_for_cluster_bomb(self.wizard)
        if self.enemy:
            return "retreating"

        elif self.enemy is None:
            return "seeking"
        
        return None

    def entry_actions(self):
        pass

    def exit_actions(self):
        self.enemy = None





def within_collision_range_of_target(
    hero: Character, 
    target, 
    radius) -> bool:
    return within_range_between_positions(hero, target, radius)

def within_range_between_positions(
    hero, target, radius) -> bool:


    # we just use the explosion radius so as to comabt 
    # so as to fix larger entities from having more collisions
    # as the wizard would always aim at the centre of the entity
    hero_radius = radius 

    target_radius = get_circumCircle_radius(target)
    dist_between_targets = g.distance_between(hero.position, target.position)

    if dist_between_targets <= (hero_radius + target_radius):
        return True

    return False


def get_circumCircle_radius(entity:GameEntity):

    '''
        Since we have no radius for rectangles and squares
        we can get them by using the formula

        diagonal of the subject is = squareRoot (length**2 plus width**2)
        r = diagonal of the subject over 2
    
    '''
    diagonal = sqrt(entity.image.get_width()**2 + entity.image.get_height() ** 2)
    radius = diagonal/2


    return radius

#cluster bomb code
def get_nearest_entity_that_is(
    hero: Character, 
    *predicates):
    '''Public: Gets the nearest entity that fulfils all conditions'''

    return g.get_entities_that_are(hero, *predicates)
        
'''
    Pass in predicates,
    Mostly to judge if the entities are friendly or hostile

'''
def get_entities_based_on_condition(
    hero: Character, 
    *predicates):
    '''Public: Gets the nearest enemy that fulfils all conditions'''
    return get_nearest_entity_that_is(hero,
        lambda entity: g.entity_type_of_any(
            entity, arrow=False, fireball=False, archer=True, 
            knight=True, wizard=True, orc=True, tower=True, base=True),
        lambda entity: g.entity_not_ko(entity),
        *predicates)


def get_enemy_for_cluster_bomb(character:Character):

    #get all close enemies within the range
    list_entities = get_entities_based_on_condition(character,
    lambda entity: g.within_range_of_target(character, entity, character.projectile_range),
    lambda entity: g.enemy_between(entity, character),
    lambda entity: g.in_sight_with_target(character, entity))


    '''
        _range = size of the cluster explosion radius
        note that this is the inner-radius of the square
        for eg a circle in a square that fits perfectly
    
    '''
    _range = 48 
    dict_entities= {}

    for ent in list_entities:

        #get all close allies within the explosion range
        close_allies = get_entities_based_on_condition(ent,
                        lambda entity: g.friendly_between(entity, ent),
                        lambda entity: within_collision_range_of_target(ent, entity, _range))
        dict_entities[ent] = len(close_allies) - 1 #as helper funcs return all entities includeding its own
    
    if dict_entities:
        #print(dict_entities)
        return max(dict_entities, key=dict_entities.get)




"""
    Experimental features
    Uses goal based design 
    Evaluates which goal is the most impt

    Calculates ratings for the different level up attributes
    Note: This is an experimentation, equation is subject to change

"""

class character_feature(object):

    '''
        Equation = current_hp over max_hp
    '''
    def get_rating_health(character:Character)->int:
        health = (character.current_hp / character.max_hp) * 1
        return min(1, health)


    '''
        Equation = (damage/cooldown)/damage
        percentage of ranged_damage it output per second
       
    '''
    def get_weapon_damage_per_second(character:Character)->int:
        
        rating = (character.ranged_damage/character.ranged_cooldown)/character.ranged_damage
        return min(1, rating)



    def get_rating_speed(character:Character)->int:

        '''
            To get a number between 0 and 1
            we used speed over dist which gives us 1/time
            the closer time is to 1 second the shorter it takes
            for the bot to reach the enemy base
        
        '''

        enemy_base = g.get_enemy_base(character)
        dist = g.distance_between(character.position, enemy_base.position)
        rating = (character.maxSpeed/dist)
        #print(rating)
        return min(1, rating)


def health_level_up_evaluate(character:Character) -> int:
    '''
        How healthy is the bot?
        Equation:

        tweaker * ( 1 - rating of the health of the character) multiplied by its healing cooldown 

        Thus if the bot is low in health and it cooldown is 4 seconds,
        it will desire to upgrade its healing more 
        than if the cooldown was 0.4 seconds
    '''
    tweaker = 0.2 #how important is this level up attribute to the hero

    desire = tweaker * ((1-character_feature.get_rating_health(character)) * character.healing_cooldown)
    return [min(1,desire), 'hp']


def damage_level_up_evaluate(character:Character) -> int:
    '''
        How far is it from the base?

        Equation: 
        (tweaker * ( 1 - rating of the damage of the character) * health) divided by the
        distance away from an enemy base)

        the closer to the enemy base the more it would want to upgrade
        its damage output
    '''
    tweaker = 0.25
    #nearer to the base to more I want to upgrade my damage output
    enemy_base = g.get_enemy_base(character)
    dist_base_and_enemy_base = g.distance_between(g.get_friendly_base(character).position, enemy_base.position)
    dist = g.distance_between(character.position, enemy_base.position)
    dist_normalized = dist/dist_base_and_enemy_base

    rating_health = character_feature.get_rating_health(character)
    rating_damage = character_feature.get_weapon_damage_per_second(character)

    desire = (tweaker * rating_health * (1-rating_damage))/dist_normalized
    return [min(1,desire), 'ranged damage']


def speed_level_up_evaluate(character:Character)->int:
    tweaker = 0.15
    desire = tweaker * (1- character_feature.get_rating_speed(character))
    return [min(1,desire), 'speed']


'''Returns a string after computing the max score'''
def get_best_score(
    hero: Character,
    *predicates)->str:
    ''' ooo functional programming ehuehue'''

    return [max(pred(hero) for pred in predicates)][0][1]
