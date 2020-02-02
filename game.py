from worlds import sample_worlds
import numpy as np
from common import N, P, R, NUM_WOLVES, ROLE_DIST, Roles


# one coin flip, returns True with probability p
def flip(p):
    return np.random.uniform() <= p


# function decorator for game actions, ensures cleanup
def action(f):
    def wrapper(*args):
        ret = f(*args)
        args[0]._update_role_distributions()
        return ret

    return wrapper


class Game:
    def __init__(self, world=None):
        if world is None:
            self._world = sample_worlds(N, P, R, ROLE_DIST)
        else:
            self._world = world

        self._role_dist = None
        self._update_role_distributions()

    def save_game(self, filename):
        np.save(filename, self._world)

    @staticmethod
    def load_game(filename):
        world = np.load(filename)
        return Game(world)

    def game_finished(self) -> bool:
        """Returns true if the game is finished (either only wolves or only villagers alive."""
        pass

    # prints all dead characters
    def print_dead(self):
        players = self._world[:, :, Roles.DEAD.value] == 1
        for i in range(P):
            print("Player %d is %s" % (i, "DEAD" if players[:, i].all() else "ALIVE"))

    def worlds_collapse(self) -> bool:
        """Returns true if all worlds collapse, i.d. there is only a single world remaining.
        """
        return self._world.shape[0] == 1

    # represents the action that a werewolf starts a kill
    @action
    def ww_kill(self, p1: int, p2: int):
        # we must drop the universes where both players are werewolves
        mask_p1_ww = self._player_is_wolf(p1)
        mask_p2_ww = self._player_is_wolf(p2)
        mask_elim = np.logical_and(mask_p1_ww, mask_p2_ww)
        self._world = self._world[np.logical_not(mask_elim)]

        # mask that indicates in which worlds p1 is the currently highest ranking werewolf
        mask = self._get_highest_ranking_werewolf() == p1
        # i think this is the fastest, sadly, we will see this more often
        # sets player 2 dead in every world where p1 is the currently highest ranking werewolf
        for i in range(mask.size):
            if mask[i]:
                self._world[i, p2, Roles.DEAD.value] = 1

    @action
    def seer_check(self, p1: int, p2: int) -> bool:
        """
        Player 1 checks player 2.
        :return: True if player 2 is seen as evil, false otherwise.
        """
        # check which role p2 could be having
        evil = flip(self._role_dist[p2, Roles.WOLVES.value].sum())  # True if p1 sees p2 as evil
        # eliminiation
        mask_p1_seer = self._world[:, p1,
                       Roles.SEER.value] == 1  # elim all universes where p1 is seer and p2 is not werewolf
        if evil:  # elim all universes where p2 is not evil
            mask_p2_villager = self._world[:, p2, Roles.VILLAGER.value]
            mask_p2_seer = self._world[:, p2, Roles.SEER.value]
            mask_p2 = np.logical_or(mask_p2_seer, mask_p2_villager)
        else:  # elim all universes where p2 is evil
            mask_p2 = self._player_is_wolf(p2)
        mask_elim = np.logical_and(mask_p1_seer, mask_p2)
        self._world = self._world[np.logical_not(mask_elim)]
        return evil

    @action
    def lynch(self, player: int):
        # kills player
        role = np.random.choice(R, p=self._role_dist[player, :-1])  # samples using the role dist array
        print("Player %i was Role %i" % (player, role))
        # eliminates all universes where the player did not have that role
        mask_role = self._world[:, player, role] != 1
        # remove all universes where the character was already dead
        mask_dead = self._world[:, player, Roles.DEAD.value] == 1
        mask_elim = np.logical_or(mask_role, mask_dead)
        self._world = self._world[np.logical_not(mask_elim)]
        self._world[:, player, Roles.DEAD.value] = 1  # sets player to dead in all universes that remain

    def _get_highest_ranking_werewolf(self) -> np.ndarray:
        """Returns array with the highest ranking werewolf per world.
        This is an unholy spaghetti function.
        """
        wolve_roles = self._world[:, :, Roles.WOLVES.value] == 1
        wolves_alive = (self._world[:, :, Roles.DEAD.value] == 0)[:, :, None]  # evil numpy magic
        # manually helping numpy broadcasting here
        alive_wolves = np.logical_and(wolve_roles, wolves_alive)
        # only the columns left where the wolf is still alive
        cols_where_wolf_type_still_alive = alive_wolves.any(axis=1)[:, None, :].astype(float)
        # deliberately sets the values to nan if no wolf there
        cols_where_wolf_type_still_alive[cols_where_wolf_type_still_alive == 0] = np.nan
        alive_wolves = alive_wolves * cols_where_wolf_type_still_alive
        temp = np.hstack([alive_wolves, np.zeros(alive_wolves.shape)])
        highest_ranking_wolf: np.ndarray = np.nanargmax(temp, axis=1).astype(float)  # contains highest ranking wolf now
        highest_ranking_wolf[highest_ranking_wolf == P] = np.nan
        highest_ranking_wolf += np.arange(0, P * NUM_WOLVES, P)  # we abuse that NaN + a = NaN.
        highest_ranking_wolf = np.nanmin(highest_ranking_wolf, axis=1)  # ignores nan
        assert highest_ranking_wolf.size == self._world.shape[0], "Internal logical error"
        return np.mod(highest_ranking_wolf, P)

    # returns a mask of worlds where the player is a wolf
    def _player_is_wolf(self, p1: int) -> np.ndarray:
        return (self._world[:, p1, Roles.WOLVES.value] == 1).any(axis=1)

    def _update_role_distributions(self):
        self._role_dist = self._world.mean(axis=0)


game = Game()
game.lynch(1)
game.lynch(2)
# game.lynch(3)
# game.lynch(4)
# game.lynch(5)
ww = game._get_highest_ranking_werewolf()
# game.ww_kill(0, 2)
# game.lynch(3)
