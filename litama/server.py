import json
from typing import Dict, List, Union, Set, Type, Any

from flask import Flask
from flask_sockets import Sockets
from geventwebsocket import WebSocketError
from pymongo import MongoClient
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket.websocket import WebSocket
from pymongo.collection import Collection

from commands.command import Command
from commands.create import Create
from commands.join import Join
from commands.message import Message
from commands.move import Move
from commands.spectate import Spectate
from commands.state import State
from config import MONGODB_HOST

app = Flask(__name__)
sockets = Sockets(app)

mongodb = MongoClient(MONGODB_HOST)
matches: Collection = mongodb.litama.matches

game_clients: Dict[str, Set[WebSocket]] = {}

StateDict = Dict[str, Union[bool, str, List[str], Dict[str, Union[List[str], str]]]]
CommandResponse = Dict[str, Union[bool, str]]

commands: List[Type[Command]] = [Create, Join, State, Move, Spectate]


@sockets.route("/")  # type: ignore
def game_socket(ws: WebSocket) -> None:
    while not ws.closed:
        query = ws.receive()
        if query is None:
            continue

        print(f"Received:`{query}`")

        messages: List[Message]
        for command in commands:
            if command.command_matches(query):
                messages = command.apply_command(matches, query[len(command.STARTS_WITH):])
                break
        else:
            messages = [Command.error_msg("Invalid command sent", query)]
            pass

        for message in messages:
            if message.add_sender_to_spectate_map:
                add_client_to_map(message.match_id, ws)

            msg_to_send_str = to_json_str(message.message)
            if message.reply_to_only_sender:
                ws.send(msg_to_send_str)
            else:
                removed_clients: List[WebSocket] = []
                for client in game_clients[message.match_id]:
                    try:
                        client.send(msg_to_send_str)
                    except WebSocketError:
                        removed_clients.append(client)
                for client in removed_clients:
                    game_clients[message.match_id].remove(client)


def to_json_str(d: Dict[str, Any]) -> str:
    return json.dumps(d, separators=(',', ':'))


def add_client_to_map(match_id: str, ws: WebSocket) -> None:
    if match_id not in game_clients:
        game_clients[match_id] = set()
    game_clients[match_id].add(ws)


@app.route("/")
def index() -> str:
    return "This is a WebSocket server. Connect to this address using the ws or wss protocol. " \
           "See the <a href=\"https://github.com/TheBlocks/Litama/wiki\">wiki</a> for more information."


if __name__ == "__main__":
    server = pywsgi.WSGIServer(('127.0.0.1', 5000), app, handler_class=WebSocketHandler)
    print("Running")
    server.serve_forever()
