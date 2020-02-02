import os
from game import Game

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


def empty():
    print("Invalid.")
    pass


def load_game():
    # present a menu for game loading
    # load configuration and game
    # start game
    pass


def start_new_game():
    # ask for player names
    # ask for name of game
    # ask for number of villagers, seer, players
    # save to configuration
    pass


def play_game(game: Game):
    # actually play the game
    # divide into day and night phases
    # include some measure of when the game is finished
    while True:
        night_phase(game)
        day_phase(game)
        # check if game is finished
    pass


def night_phase(game: Game):
    pass


def day_phase(game: Game):
    pass


def perform_ww_kill(game: Game):
    pass


def perform_seer_check(game: Game):
    pass


def overview_menu():
    while True:
        print(_MENU_OVERVIEW_TEXT)
        command = input("Please input your next action: ")
        # dispatches on input to different functions
        switcher = {
            "1": empty,
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
