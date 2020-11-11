import json
import random
from typing import Dict, List, Union, Optional, Set
from secrets import token_hex

import bson
from bson import ObjectId
from flask import Flask
from flask_sockets import Sockets
from geventwebsocket import WebSocketError
from pymongo import MongoClient
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket.websocket import WebSocket

from cards import ALL_BASE_CARD_NAMES, ALL_CARD_INFO
from config import MONGODB_HOST
from game import init_game, Board, apply_move, check_win_condition
from conversions import board_to_str, str_to_board, notation_to_pos, get_card_from_name, get_cards_from_names
from structures import Player, GameState

app = Flask(__name__)
sockets = Sockets(app)

mongodb = MongoClient(MONGODB_HOST)
matches = mongodb.litama.matches

game_clients: Dict[str, Set[WebSocket]] = {}

StateDict = Dict[str, Union[bool, str, List[str], Dict[str, Union[List[str], str]]]]
CommandResponse = Dict[str, Union[bool, str]]


@sockets.route("/")
def game_socket(ws: WebSocket) -> None:
    while not ws.closed:
        message = ws.receive()
        if message is None:
            continue

        print(f"Received:`{message}`")
        msg_to_send: Union[StateDict, CommandResponse]
        broadcast_id: Optional[str] = None
        broadcast_only_to_sender = False
        match_id: str

        if message == "create":
            msg_to_send = game_create()
        elif message == "cards":
            msg_to_send = list_cards()
        elif message.startswith("join "):
            msg_to_send = game_join(message[5:])
            if msg_to_send["messageType"] != "error":
                match_id = msg_to_send["matchId"]
                broadcast_id = match_id
        elif message.startswith("state "):
            msg_to_send = game_state(message[6:])
        elif message.startswith("move "):
            split = message.split(" ")
            # Command format: move [match_id] [token] [card] [move]
            # Example: move 5f9c394ee71e1740c218587b iq2V39W9WNm0EZpDqEcqzoLRhSkdD3lY boar a1a2
            msg_to_send = game_move(split[1], split[2], split[3], split[4])
            if msg_to_send["messageType"] != "error":
                match_id = msg_to_send["matchId"]
                broadcast_id = match_id
        elif message.startswith("spectate "):
            msg_to_send = game_spectate(message[9:])
            if msg_to_send["messageType"] != "error":
                match_id = msg_to_send["matchId"]
                add_client_to_map(match_id, ws)
                broadcast_id = match_id
                broadcast_only_to_sender = True
        else:
            msg_to_send = error_msg("Invalid command sent", message)

        msg_to_send_str = to_json_str(msg_to_send)
        ws.send(msg_to_send_str)
        if broadcast_id is not None:
            if broadcast_only_to_sender:
                game_state_str = to_json_str(game_state(broadcast_id))
                ws.send(game_state_str)
            else:
                broadcast_state(broadcast_id, ObjectId(broadcast_id))


def error_msg(error: str, attempted_command: str, match_id=""):
    return {
        "messageType": "error",
        "matchId": match_id,
        "error": error,
        "command": attempted_command
    }


def to_json_str(d: Dict) -> str:
    return json.dumps(d, separators=(',', ':'))


def add_client_to_map(match_id: str, ws: WebSocket) -> None:
    if match_id not in game_clients:
        game_clients[match_id] = set()
    game_clients[match_id].add(ws)


def broadcast_state(match_id: str, object_id: ObjectId) -> None:
    state = generate_state_dict(matches.find_one({"_id": object_id}))
    state_json = to_json_str(state)

    if match_id in game_clients:
        removed_clients: List[WebSocket] = []
        for client in game_clients[match_id]:
            try:
                client.send(state_json)
            except WebSocketError:
                removed_clients.append(client)
        for client in removed_clients:
            game_clients[match_id].remove(client)


def generate_state_dict(match: Dict) -> StateDict:
    if match["gameState"] == GameState.WAITING_FOR_PLAYER.value:
        return {
            "messageType": "state",
            "matchId": str(match["_id"]),
            "gameState": match["gameState"]
        }

    return {
        "messageType": "state",
        "matchId": str(match["_id"]),
        "currentTurn": match["currentTurn"],
        "cards": match["cards"],
        "startingCards": match["startingCards"],
        "moves": match["moves"],
        "board": match["board"],
        "gameState": match["gameState"],
        "winner": match["winner"]
    }


def check_match_id(message_type):
    def decorator_wrapper(function):
        def wrapper(match_id, *args):
            try:
                return function(match_id, *args)
            except bson.errors.InvalidId:
                return error_msg("matchId was in an incorrect format", message_type, match_id)

        return wrapper

    return decorator_wrapper


def game_create() -> CommandResponse:
    token = token_hex(32)
    color: str = "Blue"
    enemy: str = "Red"
    if random.random() < 0.5:
        color = "Red"
        enemy = "Blue"
    insert = {
        f"token{color}": token,
        f"token{enemy}": "",
        "gameState": GameState.WAITING_FOR_PLAYER.value
    }
    match_id = str(matches.insert_one(insert).inserted_id)

    return {
        "messageType": "create",
        "matchId": match_id,
        "token": token,
        "color": color.lower()
    }

def list_cards() -> CommandResponse:
    return ALL_CARD_INFO


@check_match_id("join")
def game_join(match_id: str) -> CommandResponse:
    object_id = ObjectId(match_id)
    match = matches.find_one({"_id": object_id})
    if match is None:
        return error_msg("Match not found", "join", match_id)
    if match["gameState"] != GameState.WAITING_FOR_PLAYER.value:
        return error_msg("Not allowed to join", "join", match_id)

    token = token_hex(32)
    color: str = "red" if match["tokenRed"] == "" else "blue"
    board, blue_cards, red_cards, side_card = init_game()

    matches.find_one_and_update(
        {"_id": object_id},
        {"$set": {
            f"token{color.title()}": token,
            "gameState": GameState.IN_PROGRESS.value,
            "board": board_to_str(board),
            "moves": [],
            "currentTurn": side_card.color.value,
            "cards": {
                "blue": [i.name for i in blue_cards],
                "red": [i.name for i in red_cards],
                "side": side_card.name
            },
            "startingCards": {
                "blue": [i.name for i in blue_cards],
                "red": [i.name for i in red_cards],
                "side": side_card.name
            },
            "winner": Player.NONE.value
        }}
    )

    return {
        "messageType": "join",
        "matchId": match_id,
        "token": token,
        "color": color
    }


@check_match_id("spectate")
def game_spectate(match_id: str) -> CommandResponse:
    object_id = ObjectId(match_id)
    match = matches.find_one({"_id": object_id})
    if match is None:
        return error_msg("Match not found", "spectate", match_id)
    if match["gameState"] == GameState.ENDED.value:
        return error_msg("Game ended", "spectate", match_id)
    return {
        "messageType": "spectate",
        "matchId": match_id
    }


@check_match_id("state")
def game_state(match_id: str) -> Union[StateDict, CommandResponse]:
    object_id = ObjectId(match_id)
    match = matches.find_one({"_id": object_id})
    if match is None:
        return error_msg("Match not found", "state", match_id)
    return generate_state_dict(match)


@check_match_id("move")
def game_move(match_id: str, token: str, card_name: str, move: str) -> CommandResponse:
    object_id = ObjectId(match_id)
    match = matches.find_one({"_id": object_id})
    if match is None:
        return error_msg("Match not found", "move", match_id)
    if match["gameState"] == GameState.ENDED.value:
        return error_msg("Game ended", "move", match_id)

    if token == match["tokenBlue"]:
        color = "blue"
    elif token == match["tokenRed"]:
        color = "red"
    else:
        return error_msg("Token is incorrect", "move", match_id)

    if move[0] not in "abdce" or move[1] not in "12345" or move[2] not in "abcde" or move[3] not in "12345":
        move = "none"
    if card_name not in ALL_BASE_CARD_NAMES:
        card_name = "none"
    if move == "none" or card_name == "none":
        return error_msg("'move' or 'card' not given properly", "move", match_id)

    board = str_to_board(match["board"])
    piece_pos = notation_to_pos(move[:2])

    if board[piece_pos.y][piece_pos.x].color.value != color:
        return error_msg("Cannot move opponent's pieces or empty squares", "move", match_id)

    move_pos = notation_to_pos(move[2:])
    move_card = get_card_from_name(card_name)
    cards = get_cards_from_names(match["cards"][color])
    new_board: Optional[Board] = apply_move(piece_pos, move_pos, move_card, cards, board)

    if new_board is None:
        return error_msg("Invalid move", "move", match_id)

    winner = check_win_condition(new_board)
    state = GameState.ENDED.value if winner != Player.NONE else GameState.IN_PROGRESS.value

    moves = match["moves"]
    moves.append(f"{card_name}:{move}")
    side_card: str = match["cards"]["side"]
    new_cards: List[str] = match["cards"][color]
    new_cards[new_cards.index(card_name)] = side_card

    enemy = "red" if color == "blue" else "blue"
    enemy_cards = match["cards"][enemy]

    matches.find_one_and_update(
        {"_id": object_id},
        {"$set": {
            "board": board_to_str(new_board),
            "moves": moves,
            "currentTurn": "blue" if color == "red" else "red",
            "cards": {
                enemy: enemy_cards,
                color: new_cards,
                "side": card_name
            },
            "gameState": state,
            "winner": winner.value
        }}
    )

    return {
        "messageType": "move",
        "matchId": match_id
    }


@app.route("/")
def index():
    return "This is a WebSocket server. Connect to this address using the ws or wss protocol. " \
           "See the <a href=\"https://github.com/TheBlocks/Litama/wiki\">wiki</a> for more information."


if __name__ == "__main__":
    server = pywsgi.WSGIServer(('127.0.0.1', 5000), app, handler_class=WebSocketHandler)
    print("Running")
    server.serve_forever()
