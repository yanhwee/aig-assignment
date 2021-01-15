# Imports
import g
from Globals import (
    UP_PERCENTAGE_RANGED_DAMAGE, 
    UP_PERCENTAGE_RANGED_COOLDOWN,
    ARCHER_RANGED_COOLDOWN, 
    ARCHER_RANGED_DAMAGE)
import matplotlib.pyplot as plt
# Constants
LEVEL_START = 0
LEVEL_END = 5
POINTS = 100
DAMAGE_0 = ARCHER_RANGED_DAMAGE
DAMAGE_RATIO = 1 + UP_PERCENTAGE_RANGED_DAMAGE / 100
COOLDOWN_0 = ARCHER_RANGED_COOLDOWN
COOLDOWN_RATIO = 1 - UP_PERCENTAGE_RANGED_COOLDOWN / 100
# Functions
dps = lambda damage, cooldown: damage / cooldown
seq = lambda a1, r: lambda k: a1 * r ** k
d_seq = seq(DAMAGE_0, DAMAGE_RATIO)
c_seq = seq(COOLDOWN_0, COOLDOWN_RATIO)
d_dps = lambda k: dps(d_seq(k), COOLDOWN_0)
c_dps = lambda k: dps(DAMAGE_0, c_seq(k))
# Generate
xs = g.linspace(LEVEL_START, LEVEL_END, POINTS)
dys = list(map(d_dps, xs))
cys = list(map(c_dps, xs))
plt.plot(xs, dys, label='damage')
plt.plot(xs, cys, label='cooldown')
plt.title('DPS Comparison: Stacking Damage vs Cooldown')
plt.ylabel('Damage Per Second (DPS)')
plt.xlabel('Level Ups')
plt.legend()
plt.show()