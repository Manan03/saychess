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

board = chess.Board()

def bestmove() -> None:
    engine = chess.engine.SimpleEngine.popen_uci(
        "stockfish\\stockfish.exe"
    )
    global board
    #thread_stop_event.
    thread_stop_event.clear()
    while not board.is_game_over() and (not thread_stop_event.is_set()):
        result = engine.play(board, chess.engine.Limit(time=0.4))
        board.push(result.move)
        print(result.move)
        socketio.emit("move", {"bestmove": str(result.move)}, namespace="/test")
        socketio.sleep(1)
    # print(board.result())
    print("Quitting Engine")
    engine.quit()


@app.route("/")
def index():
    # only by sending this page first will the client be connected to the socketio instance
    return render_template("index.html")


@socketio.on("connect", namespace="/test")
def test_connect():
    # need visibility of the global thread object

    print("Client connected")


@socketio.on("disconnect", namespace="/test")
def test_disconnect():
    global board
    print("Client disconnected")


@socketio.on("btn", namespace="/test")
def play(data):
    global thread
    if not thread.isAlive():
        print("Starting Thread")
        try:
            thread = socketio.start_background_task(bestmove)
        except:
            thread_stop_event.set()

@socketio.on("stop", namespace="/test")
def stop(data):
    global thread
    global board
    board.reset()
    if thread.isAlive():
        thread_stop_event.set()


if __name__ == "__main__":
    socketio.run(app, use_reloader=True)
