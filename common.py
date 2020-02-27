from enum import Enum
import os

def safe_pop(l: list):
    try:
        l.pop()
    except IndexError:
        pass

def ensure_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

# configuration of the game
class GameConfig:
    """
    N: Number worlds
    P: Number of players
    """
    def __init__(self, num_worlds, num_players, num_wolves, num_seers, num_villagers):
        self.num_worlds = num_worlds
        self.num_players = num_players
        self.num_wolves = num_wolves
        self.num_seers = num_seers
        self.num_villagers = num_villagers
        self.num_roles = num_wolves + 2
        self.role_dist = [num_villagers, num_seers]
        self.role_dist.extend([1] * self.num_wolves)

# quick index to get access to all wolves
class Roles:
    def __init__(self, num_wolves):
        class _role_enum_class(Enum):
            """Enum used to identify which roles belong in which column in the one-hot encoded Vector.
            Dead is a virtual role and will not count to the number of roles in the code.
            """
            # every werewolf is its own role. The kills will be resolved with priority, e.g.
            # Werewolf 1 kills normally, if Werewolf 1 is dead, then Werewolf 2 does the killings etc...
            VILLAGER = 0
            SEER = 1
            WEREWOLF_FIRST = 2
            WEREWOLF_LAST = WEREWOLF_FIRST + num_wolves - 1
            WOLVES = list(range(WEREWOLF_FIRST, WEREWOLF_LAST + 1))
            DEAD = WEREWOLF_LAST + 1  # must be the last ROLE!
        self.Roles = _role_enum_class

    def __getattr__(self, role):
        return getattr(self.Roles, role)

