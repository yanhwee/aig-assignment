import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *
import g

DEFAULT_PATH = 3
HEALTH_PERCENTAGE = 0.8

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

        self.brain.add_state(seeking_state)
        self.brain.add_state(attacking_state)
        self.brain.add_state(ko_state)

        self.brain.set_state("seeking")

    def render(self, surface):

        Character.render(self, surface)


    def process(self, time_passed):
        
        Character.process(self, time_passed)

        if self.can_level_up():
            self.level_up("ranged cooldown")

      




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
       
        if self.wizard.current_hp < HEALTH_PERCENTAGE * (self.wizard.max_hp):
            self.wizard.heal()
    def check_conditions(self):

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
        
        self.enemy  =  get_enemy_for_cluster_bomb(self.wizard)
    
        if self.enemy and (self.wizard.current_hp >= HEALTH_PERCENTAGE * (self.wizard.max_hp)):
            if self.enemy.name == "base":
                self.wizard.ranged_attack(self.enemy.spawn_position, self.wizard.explosion_image)
            else:
                preaim_position = g.preaim_entity(self.wizard, self.enemy)
                #send the explosive to that direction
                self.wizard.ranged_attack(preaim_position, self.wizard.explosion_image)
              
        if self.wizard.current_hp < HEALTH_PERCENTAGE * (self.wizard.max_hp):
            self.wizard.heal()
        
        if self.enemy:
            path_pos = g.position_away_from_target_using_path(self.wizard, self.enemy)
            g.set_move_target(self.wizard, path_pos)
            g.update_velocity(self.wizard)

    def check_conditions(self):


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




def within_collision_range_of_target(
    hero: Character, 
    target, 
    radius) -> bool:

    # we just use the explosion radius so as to comabt 
    # larger entities from having more collisions
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

def get_enemy_for_cluster_bomb(character:Character):

    #get all close enemies within the range
    list_entities = g.get_entities_that_are(character,
                    lambda entity: g.entity_type_of_any(
                            entity, arrow=False, fireball=False, archer=True, 
                            knight=True, wizard=True, orc=True, tower=True, base=True),
                    lambda entity: g.entity_not_ko(entity),
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
        close_allies = g.get_entities_that_are(ent,
                        lambda entity: g.entity_type_of_any(
                                entity, arrow=False, fireball=False, archer=True, 
                                knight=True, wizard=True, orc=True, tower=True, base=True),
                        lambda entity: g.entity_not_ko(entity),
                        lambda entity: g.friendly_between(entity, ent),
                        lambda entity: within_collision_range_of_target(ent, entity, _range))
        dict_entities[ent] = len(close_allies) - 1 #as helper funcs return all entities includeding its own
    
    if dict_entities:
        #print(dict_entities)
        return max(dict_entities, key=dict_entities.get)




