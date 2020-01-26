from worlds import sample_worlds
import numpy as np
from enum import Enum

# we will later just read these from the global configurations
N = 500
P = 4
R = 3
role_dist = [1, 2, 1]

class Roles(Enum):
    """Enum used to identify which roles belong in which column in the one-hot encoded Vector.
    Dead is a virtual role and will not count to the number of roles in the code.
    """
    WEREWOLF = 0
    VILLAGER = 1
    SEER = 2
    DEAD = 3  # must be the last ROLE!

# one coin flip, returns True with probability p
def flip(p):
    return np.random.uniform() <= p

# function decorator for game actions, ensures cleanup
def action(f):
    def wrapper(*args):
        f(*args)
        args[0]._update_role_distributions()
    return wrapper

class Game:
    def __init__(self):
        self._world = sample_worlds(N, P, R, role_dist)
        self._role_dist = None
        self._update_role_distributions()

    # represents the action that a werewolf starts a kill
    @action
    def ww_kill(self, p1: int,  p2: int):
        mask = self._world[:, p1, Roles.WEREWOLF.value] == 1
        # i think this is the fastest, sadly, we will see this more often
        # sets player 2 dead in every world where p1 is a werewolf
        for i in range(mask.size):
            if mask[i]:
                self._world[i, p2, Roles.DEAD.value] = 1
        # we must drop the universes where both players are werewolves
        mask_p2_ww = self._world[:, p2, Roles.WEREWOLF.value] == 1
        mask_elim = np.logical_and(mask, mask_p2_ww)
        self._world = self._world[np.logical_not(mask_elim)]

    @action
    def seer_check(self, p1: int, p2: int):
        # check which role p2 could be having
        evil = flip(self._role_dist[p2, Roles.WEREWOLF.value]) # True if p1 sees p2 as evil
        # eliminiation
        mask_p1_seer = self._world[:, p1, Roles.SEER.value] == 1 # elim all universes where p1 is seer and p2 is not werewolf
        if evil: # elim all universes where p2 is not evil
            mask_p2_villager = self._world[:, p2, Roles.VILLAGER.value]
            mask_p2_seer = self._world[:, p2, Roles.SEER]
            mask_p2 = np.logical_or(mask_p2_seer, mask_p2_seer)
        else: # elim all universes where p2 is evil
            mask_p2 = self._world[:, p2, Roles.WEREWOLF.value]
        mask_elim = np.logical_and(mask_p1_seer, mask_p2)
        self._world = self._world[np.logical_not(mask_elim)]
        return evil

    @action
    def lynch(self, player: int):
        # kills player
        role = np.random.choice(R, p=self._role_dist[player, :-1]) # samples using the role dist array
        print("Player %i was Role %i" % (player, role))
        # eliminates all universes where the player did not have that role
        mask_role = self._world[:, player, role] != 1
        # remove all universes where the character was already dead
        mask_dead = self._world[:, player, Roles.DEAD.value] == 1
        mask_elim = np.logical_or(mask_role, mask_dead)
        self._world = self._world[np.logical_not(mask_elim)]
        self._world[:, player, Roles.DEAD.value] = 1  # sets player to dead in all universes that remain

    # prints all dead characters
    def print_dead(self):
        players = self._world[:, :, Roles.DEAD.value] == 1
        for i in range(P):
            print("Player %d is %s" % (i, "DEAD" if players[:, i].all() else "ALIVE"))

    def _update_role_distributions(self):
        self._role_dist = self._world.mean(axis=0)

game = Game()
game.lynch(1)
game.ww_kill(0, 2)
game.ww_kill(2, 3)
game.lynch(3)
