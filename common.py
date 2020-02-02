from enum import Enum

# we will later just read these from the global configurations
N = 20
P = 6
NUM_WOLVES = 3
# each wolf counts as a separate role
R = NUM_WOLVES + 2

# every werewolf is its own role. The kills will be resolved with priority, e.g.
# Werewolf 1 kills normally, if Werewolf 1 is dead, then Werewolf 2 does the killings etc...
# convention: last roles are all werewolf. We will always need at least one werewolf
ROLE_DIST = [1, 2]
ROLE_DIST.extend([1] * NUM_WOLVES)


class Roles(Enum):
    """Enum used to identify which roles belong in which column in the one-hot encoded Vector.
    Dead is a virtual role and will not count to the number of roles in the code.
    """
    VILLAGER = 0
    SEER = 1
    WEREWOLF_FIRST = 2
    WEREWOLF_LAST = WEREWOLF_FIRST + NUM_WOLVES - 1
    WOLVES = list(range(WEREWOLF_FIRST, WEREWOLF_LAST + 1))
    DEAD = WEREWOLF_LAST + 1  # must be the last ROLE!

# quick index to get access to all wolves
