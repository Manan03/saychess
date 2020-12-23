# Start with a basic flask app webpage.
from flask_socketio import SocketIO, emit
from flask import Flask, render_template
from time import sleep
from threading import Thread, Event
import chess.engine

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
app.config["DEBUG"] = True

# turn the flask app into a socketio app
socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)

# random number Generator Thread
playthread = Thread()
playthread_stop_event = Event()

board = chess.Board()


def bestmove_playcom() -> None:
    engine = chess.engine.SimpleEngine.popen_uci("stockfish\\stockfish.exe")
    global board
    # thread_stop_event.
    playthread_stop_event.clear()
    while not board.is_game_over() and (not playthread_stop_event.is_set()):
        if not board.turn:
            result = engine.play(board, chess.engine.Limit(time=0.4))
            board.push(result.move)
            print(result.move)
            socketio.emit("move", {"bestmove": str(result.move)}, namespace="/playcom")
            socketio.sleep(1)
    # print(board.result())
    print("Quitting Engine")
    engine.quit()


@app.route("/")
def index():
    # only by sending this page first will the client be connected to the socketio instance
    return render_template("playcom.html")


@socketio.on("connect", namespace="/playcom")
def playcom_connect():
    # need visibility of the global playthread object

    print("Client connected")


@socketio.on("disconnect", namespace="/playcom")
def playcom_disconnect():
    global board
    print("Client disconnected")


@socketio.on("btn", namespace="/playcom")
def play(data):
    global playthread
    if not playthread.isAlive():
        print("Starting playthread")
        try:
            playthread = socketio.start_background_task(bestmove_playcom)
        except:
            playthread_stop_event.set()


@socketio.on("stop", namespace="/playcom")
def stop(data):
    global playthread
    global board
    board.reset()
    if playthread.isAlive():
        playthread_stop_event.set()


@socketio.on("mymove", namespace="/playcom")
def mymove(my_move):
    global playthread
    global board
    print(my_move)
    board.push_san(my_move["data"])
    print(board.fen())


if __name__ == "__main__":
    socketio.run(app, use_reloader=True)
