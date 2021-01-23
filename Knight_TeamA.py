import pygame

from random import randint, random
from Graph import *

from Character import *
from State import *
import g

DEFAULT_PATH = 3
MAX_PATH_VALUE_TO_CONSIDER_TO_SWITCH_PATH = 0.5
PATHS_TO_CONSIDER_TO_SWITCH_TO = [0,1,2,3]

KNIGHT_SENSING_RADIUS = KNIGHT_MIN_TARGET_DISTANCE
KNIGHT_HEALING_THRESHOLD_LIST = [40,70,65,60]
KNIGHT_HEALING_THRESHOLD = KNIGHT_HEALING_THRESHOLD_LIST[0]

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
        level = 1
        if self.can_level_up():
            level += 1
            if level < len(KNIGHT_HEALING_THRESHOLD_LIST):
                KNIGHT_HEALING_THRESHOLD = KNIGHT_HEALING_THRESHOLD_LIST[level-1]
            else:
                KNIGHT_HEALING_THRESHOLD = KNIGHT_HEALING_THRESHOLD_LIST[-1]
            self.level_up('healing') 


class KnightStateSeeking_TeamA(State):

    def __init__(self, knight):

        State.__init__(self, "seeking")
        self.knight = knight

    def entry_actions(self):
        g.try_switch_path(self.knight, DEFAULT_PATH)

    def path_consider_to_switch_to(self):
        if g.hero_path_value(self.knight) < MAX_PATH_VALUE_TO_CONSIDER_TO_SWITCH_PATH:
            enemies = g.get_enemy_heroes(self.knight)
            if enemies:
                paths = g.paths_sorted_by_entities_most_on_then_nearest_to_base(
                    self.knight,enemies)
                path = g.find_first_of(paths,
                    lambda path:path in PATHS_TO_CONSIDER_TO_SWITCH_TO)
                return path
        return None

    def do_actions(self):
        #check path to switch to
        path = self.path_consider_to_switch_to()
        if path is not None:
            g.try_switch_path(self.knight, path)

        #check if hp is full
        if self.knight.current_hp != self.knight.max_hp:
            self.knight.heal()
        
        #Move towards base
        enemy_base = g.get_enemy_base(self.knight)
        path_pos = g.position_towards_target_using_path(self.knight,enemy_base)
        g.set_move_target(self.knight,path_pos)
        g.update_velocity(self.knight)


    def check_conditions(self):
        # check if enemy is in range
        enemy = get_nearest_enemy(self.knight)

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
            enemy = get_nearest_enemy(self.knight)

            if enemy:
                g.set_move_target(self.knight,enemy)
                g.update_velocity(self.knight)
                # colliding with target
                if g.touching_target(self.knight,enemy):
                    #targets highest dps enemy among all the colliding targets
                    enemy = sort_touching_enemies_with_hdps(self.knight)
                    attack(self.knight,enemy)

    def check_conditions(self):

        enemy = get_nearest_enemy(self.knight)
        
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
        
        #stand at the spot and heal
        g.set_move_target(self.knight,None)
        g.update_velocity(self.knight)
        self.knight.heal()


    def check_conditions(self):

        enemy = get_nearest_enemy(self.knight)

        # target is gone
        if enemy is None:
            return "seeking"
        
        # if knight's health above a certain threshold, attack
        if self.knight.current_hp/self.knight.max_hp *100 > KNIGHT_HEALING_THRESHOLD:
            return "attacking"

# Helper Functions
def attack(hero:Character, enemy:GameEntity):
    g.set_move_target(hero, None)
    hero.melee_attack(enemy)
    g.update_velocity(hero)

def get_nearest_enemy(hero:Character):
    enemy = g.get_nearest_enemy_that_is(hero,
        lambda entity: g.within_range_of_target(hero, entity, KNIGHT_SENSING_RADIUS),
        lambda entity: g.in_sight_with_target(hero, entity))
    
    return enemy

#Target the highest dps enemy among all colliding enemies
def sort_touching_enemies_with_hdps(hero:Character):
    entities = g.get_entities_that_are(hero, 
        lambda entity: g.touching_target(hero,entity),
        lambda entity: g.enemy_between(entity, hero),
        lambda entity: g.entity_type_of_any(
            entity, arrow=False, fireball=False, archer=True, 
            knight=True, wizard=True, orc=True, tower=True, base=False),
        lambda entity: g.entity_not_ko(entity))
    highest_dps_enemy = max(entities,
        key= lambda entity: get_entity_damage(entity),
        default=None)

    return highest_dps_enemy

# Get the dps of each target
def get_entity_damage(entity:Character):
    melee_damage = getattr(entity, "melee_damage", None)
    ranged_damge = getattr(entity, "ranged_damage", None)

    if melee_damage:
        dps = melee_damage / entity.melee_cooldown
        return dps
    elif ranged_damge:
        dps = ranged_damge / entity.ranged_cooldown
        return dps
    else:
        raise Exception
