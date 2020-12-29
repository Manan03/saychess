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
thread = Thread()
thread_stop_event = Event()
playthread = Thread()
playthread_stop_event = Event()

board = chess.Board()


def bestmove_comvscom() -> None:
    engine = chess.engine.SimpleEngine.popen_uci("stockfish\\stockfish.exe")
    global board
    # thread_stop_event.
    thread_stop_event.clear()
    while not board.is_game_over() and (not thread_stop_event.is_set()):
        result = engine.play(board, chess.engine.Limit(time=0.4))
        board.push(result.move)
        print(result.move)
        socketio.emit("move", {"bestmove": str(result.move)}, namespace="/comvscom")
        socketio.sleep(3)
    # print(board.result())
    print("Quitting Engine")
    engine.quit()


@app.route("/comvscom")
def comvscom():
    # only by sending this page first will the client be connected to the socketio instance
    return render_template("comvscom.html")


@app.route("/login")
def login():
    # only by sending this page first will the client be connected to the socketio instance
    return render_template("login.html")


@app.route("/playcom")
def playcom():
    # only by sending this page first will the client be connected to the socketio instance
    return render_template("playcom.html")


@app.route("/welcome")
def welcome():
    # only by sending this page first will the client be connected to the socketio instance
    return render_template("welcome.html")


@app.route("/")
def index():
    # only by sending this page first will the client be connected to the socketio instance
    return render_template("index.html")


@socketio.on("connect", namespace="/comvscom")
def comvscom_connect():
    # need visibility of the global thread object

    print("Client connected")


@socketio.on("disconnect", namespace="/comvscom")
def comvscom_disconnect():
    global board
    print("Client disconnected")


@socketio.on("btn", namespace="/comvscom")
def play_comvscom(data):
    global thread
    if not thread.isAlive():
        print("Starting Thread")
        try:
            thread = socketio.start_background_task(bestmove_comvscom)
        except:
            thread_stop_event.set()


@socketio.on("stop", namespace="/comvscom")
def stop_com(data):
    global thread
    global board
    board.reset()
    if thread.isAlive():
        thread_stop_event.set()


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
            socketio.sleep(3)
    # print(board.result())
    print("Quitting Engine")
    engine.quit()


@socketio.on("connect", namespace="/playcom")
def playcom_connect():
    # need visibility of the global playthread object

    print("Client connected")


@socketio.on("disconnect", namespace="/playcom")
def playcom_disconnect():
    global board
    print("Client disconnected")


@socketio.on("btn", namespace="/playcom")
def play_playcom(data):
    global playthread
    if not playthread.isAlive():
        print("Starting playthread")
        try:
            playthread = socketio.start_background_task(bestmove_playcom)
        except:
            playthread_stop_event.set()


@socketio.on("stop", namespace="/playcom")
def stop_playcom(data):
    global playthread
    global board
    board.reset()
    if playthread.isAlive():
        playthread_stop_event.set()


@socketio.on("mymove", namespace="/playcom")
def mymove_playcom(my_move):
    global playthread
    global board
    print(my_move)
    board.push_san(my_move["data"])
    print(board.fen())


if __name__ == "__main__":
    socketio.run(app, use_reloader=True)