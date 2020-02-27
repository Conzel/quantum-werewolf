import os
import pandas as pd
from game import Game
from common import GameConfig, safe_pop, ensure_dir
import json

_ASSETS_FOLDER = "assets"


def load_asset(filename: str) -> str:
    asset = os.path.join(_ASSETS_FOLDER, filename)
    try:
        with open(asset, "r") as f:
            return f.read()
    except FileNotFoundError as e:
        print("Warning: File not found: " + filename)
    return ""


_MENU_OVERVIEW_TEXT = load_asset("menu-overview.txt")
_GAME_MENU_DAY_TEXT = load_asset("game_menu_day.txt")
_GAME_MENU_NIGHT_TEXT = load_asset("game_menu_night.txt")


def empty():
    print("Invalid.")
    pass


def load_game():
    # present a menu for game loading
    i = 1
    games = []
    for game in os.listdir("games"):
        print("(%02d) %s" % (i, game))
        games.append(game)
        i += 1
    # load configuration and game
    try:
        game_num = int(input("Please select a game: ")) - 1
        game = games[game_num]
    except (ValueError, IndexError):
        print("Wrong input value(s)")
        return
    game_dir = os.path.join("games", game)
    states = []
    i = 1
    for state in os.listdir(game_dir):
        # skip config
        if "config" in state:
            continue
        print("(%02d) % s" % (i, state))
        states.append(state)
        i += 1
    try:
        state_num = int(input("Please select a state: ")) - 1
        state = states[state_num]
    except (ValueError, IndexError):
        print("Wrong input value(s)")
        return
    with open(os.path.join(game_dir, "config"), "r") as f:
        raw_cfg = json.load(f)
    num_days = int(state[:2])
    night = state[2] == "N"
    config = dict_to_game_config(raw_cfg)
    game = Game.load_game(config, os.path.join(game_dir, state))
    play_game(game, raw_cfg, night, num_days)


def start_new_game():
    # ask for player names
    try:
        # ask for name of game
        game_name = input("Enter name of game (names with the same name will be overwritten): ")
        # ask for number of worlds
        num_worlds = int(
            input("Enter number of worlds (the less, the earlier the complete wavefunction collapse will happen): "))
        #
        i = 1
        name = "temp"
        print(
            "Entering names of player. Press enter without a name if you're finished. If you need to make changes later,"
            "you can opt to edit the configuration directly")
        player_names = []
        while name != "":
            print()
            name = input("Please enter name of player %02d: " % i)
            if name != "":
                player_names.append(name)
            i += 1
        # ask for number of villagers, seer, players
        while True:
            num_villagers = int(input("Enter number of villagers: "))
            num_wolves = int(input("Enter number of wolves: "))
            num_seers = int(input("Enter number of seers: "))
            if (num_seers + num_wolves + num_villagers) != len(player_names):
                print("Number of players / number of roles mismatch.")
            else:
                break
    except ValueError:
        print("Invalid input. Please repeat the setup process.")
        start_new_game()
        return

    # save to configuration
    game_config = {
        "name": game_name,
        "num_worlds": num_worlds,
        "players": player_names,
        "num_villagers": num_villagers,
        "num_wolves": num_wolves,
        "num_seers": num_seers
    }
    game_dir = os.path.join("games", game_name)
    ensure_dir(game_dir)
    game_config["game_dir"] = game_dir

    with open(os.path.join(game_dir, "config"), "w+") as f:
        json.dump(game_config, f, indent=2)
    print("Setup completed successfully.")

    # load game from config
    game = Game(dict_to_game_config(game_config))
    play_game(game, game_config, True, 0)


def dict_to_game_config(d: dict):
    return GameConfig(d["num_worlds"], len(d["players"]), d["num_wolves"], d["num_seers"], d["num_villagers"])


def play_game(game: Game, game_config: dict, night: bool, num_day: int):
    print("Starting game!")
    # actually play the game
    # divide into day and night phases
    # include some measure of when the game is finished
    while True:
        print("Currently in phase %s at day %d" % ("Night" if night else "Day", num_day))
        game.save_game(
            os.path.join(game_config["game_dir"], "%02d%s_" % (num_day, "N" if night else "D") + game_config["name"]))
        if night:
            night_phase(game, game_config)
            num_day += 1
        if not night:
            day_phase(game, game_config)
        # flip phase
        night = not night
        # check if game is finished
    pass

def night_phase(game: Game, game_config: dict):
    night_actions = []
    while True:
        print(_GAME_MENU_NIGHT_TEXT)
        command = input("Please input your next action: ")
        switcher = {
            "1": lambda: perform_ww_kill(game, game_config),
            "2": lambda: perform_seer_check(game, game_config),
            "3": lambda: see_actions(night_actions),
            "4": lambda: safe_pop(night_actions),
            "5": lambda: night_actions.clear(),
            "6": lambda: see_role_dist(game, game_config),
            "7": None,
            "8": exit
        }
        action = switcher.get(command, empty)
        if action is not None:
            night_action = action()
            if night_action is not None:
                night_actions.append(night_action)
        else:
            # unrolls all actions
            for act in night_actions:
                act()
            break


def see_actions(actions: list):
    for a in actions:
        print(a)


def day_phase(game: Game, game_config: dict):
    while True:
        print(_GAME_MENU_DAY_TEXT)
        command = input("Please input your next action: ")
        switcher = {
            "1": lambda: see_role_dist(game, game_config),
            "2": lambda: lynch(game, game_config),
            "3": None,
            "4": exit
        }
        action = switcher.get(command, empty)
        if action is not None:
            lynch_act = action()
            if lynch_act is not None:
                lynch_act()
                break
        else:
            break
    pass


def see_role_dist(game: Game, game_config: dict):
    wolf_names = ["WOLF %d" % (i + 1) for i in range(game_config["num_wolves"])]
    df = pd.DataFrame(data=game._role_dist, index=game_config["players"],
                      columns=(["VILLAGER", "SEER"] + wolf_names + ["DEAD"]))
    print(df)


def lynch(game: Game, game_config: dict):
    """
    Also returns curried lambda
    """
    print("Performing lynch: ")
    i = 1
    for p in game_config["players"]:
        print("(%02d) %s" % (i, p))
        i += 1
        # include measure to check if player is dead or definitely not a wolf
    try:
        victim = int(input("Choose who to lynch: ")) - 1
        if game.is_dead(victim):
            raise ValueError
    except ValueError:
        print("Wrong input value(s)")
        return None
    return lambda: game.lynch(victim)


def perform_ww_kill(game: Game, game_config: dict):
    """
    Returns curried lambda that performs ww kill from attacker to source
    """
    print("Performing kill:")
    i = 1
    for p in game_config["players"]:
        print("(%02d) %s" % (i, p))
        i += 1
        # include measure to check if player is dead or definitely not a wolf
    try:
        attacker = int(input("Choose attacker: ")) - 1
        target = int(input("Choose target: ")) - 1
        if attacker == target or attacker < 0 or target < 0 or attacker > len(game_config["players"]) or target > len(
                game_config["players"]) or game.is_dead(attacker) or game.is_dead(target):
            raise ValueError
    except ValueError:
        print("Wrong input value(s)")
        return None
    return WWKill(attacker, target, game, game_config)


def perform_seer_check(game: Game, game_config: dict):
    """
    Analog to perform_ww_kill
    """
    print("Performing seer check.")
    i = 1
    for p in game_config["players"]:
        print("(%02d) %s" % (i, p))
        i += 1
        # include measure to check if player is dead or definitely not a seer
    try:
        seer = int(input("Choose seer: ")) - 1
        target = int(input("Choose target: ")) - 1
        if seer == target or seer < 0 or target < 0 or seer > len(game_config["players"]) or target > len(
                game_config["players"]) or game.is_dead(target) or game.is_dead(seer):
            raise ValueError
    except ValueError:
        print("Wrong input value(s).")
        return
    return SeerCheck(seer, target, game, game_config)


class NightAction:
    def __init__(self, source, target, game: Game, game_config):
        self._source = source
        self._target = target
        self._game = game
        self._game_config = game_config

    def translate_player(self, num):
        return self._game_config["players"][num]


class WWKill(NightAction):
    def __init__(self, source, target, game: Game, game_config: dict):
        super().__init__(source, target, game, game_config)

    def __call__(self, *args, **kwargs):
        self._game.ww_kill(self._source, self._target)

    def __repr__(self):
        return "%s kills %s" % (self.translate_player(self._source), self.translate_player(self._target))


class SeerCheck(NightAction):
    def __init__(self, source, target, game: Game, game_config: dict):
        super().__init__(source, target, game, game_config)

    def __call__(self, *args, **kwargs):
        self._game.seer_check(self._source, self._target)

    def __repr__(self):
        return "%s sees %s" % (self.translate_player(self._source), self.translate_player(self._target))


def overview_menu():
    while True:
        print(_MENU_OVERVIEW_TEXT)
        command = input("Please input your next action: ")
        # dispatches on input to different functions
        switcher = {
            "1": start_new_game,
            "2": load_game,
            # we use None to signal that we exit
            "3": None
        }
        action = switcher.get(command, empty)
        if action is not None:
            action()
        else:
            break


if __name__ == '__main__':
    overview_menu()
