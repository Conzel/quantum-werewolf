from enum import Enum
from typing import List
from common import Roles
import numpy as np
import random

# Layout of the worlds:
# The whole game is a NxPxR tensor, with N being the number of worlds, P being the amount of players and R being
# the number of roles available. The roles are one-hot encoded, that means if we are in world 1, player 1, the
# role vector is vector that has a 1 at the corresponding role they have.

def sample_worlds(N: int, P: int, R: int, role_dist: List[int]) -> np.ndarray:
    """
    :param N: Number of worlds
    :param P: Number of players
    :param R: Number of roles (exclude the 'DEAD' role)
    :param role_dist: Distribution of roles (e.g. role 1 has 4 members, role 2 has 1 member, role 3 has 1 member
    -> we would pass the list [4, 1, 1]. Exclude 'DEAD' role
    :return: Sampled world array (size N x P x (R + 1))
    """
    worlds = np.zeros([N, P, R + 1])
    assert sum(role_dist) == P, "The role distribution was not valid"
    for n in range(N):
        one_hot_roles = np.hstack((one_hot_from_role_dist(role_dist), np.zeros((P, 1))))
        worlds[n, :, :] = one_hot_roles
    return worlds


def one_hot_from_role_dist(role_dist) -> np.ndarray:
    i = 0
    # holds the number of the role x times, according to role_dist
    role_encoding = []
    for num_role in role_dist:
        role_encoding.extend([i] * num_role)
        i += 1
    random.shuffle(role_encoding)  # mutates in place
    one_hot_roles = one_hot_encode(np.array(role_encoding))
    return one_hot_roles


def one_hot_encode(vec: np.ndarray) -> np.ndarray:
    ret = np.zeros((vec.size, vec.max() + 1))
    ret[np.arange(vec.size), vec] = 1
    return ret

