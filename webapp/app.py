from diart import SpeakerDiarization, SpeakerDiarizationConfig
from diart.sources import WebSocketAudioSource
from diart.inference import StreamingInference
from diart.models import SegmentationModel, EmbeddingModel
from diart.sinks import Observer, RTTMWriter, _extract_prediction

from flask import Flask, render_template, request, Response

from websockets.sync.client import connect

from huggingface_hub import login

import json
import threading
import datetime


HOST = "127.0.0.1"
PORT_FLASK = 5000
PORT_WEBSOCKET = 7007

class WSAggregationObserver(Observer):

    def __init__(self, source) -> None:
        super().__init__()
        self.source = source

    def on_next(self, value) -> None:
        prediction = _extract_prediction(value)
        print(prediction)
        chart = prediction.chart()
        if len(chart) > 0:
            self.source.send(json.dumps(chart))


app = Flask(__name__)

def is_running():
    try:
        with connect(f"ws://{HOST}:{PORT_WEBSOCKET}"):
            return True
    except Exception as e:
        return False 
    
def init():
    #login("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")
    app._inference = None
    app._config = SpeakerDiarizationConfig(
        segmentation=SegmentationModel.from_pretrained("pyannote/segmentation-3.0"), 
        embedding=EmbeddingModel.from_pretrained("pyannote/embedding"),
        rho_update=0.2,
        delta_new=0.9
    )

init()

@app.route("/")
def index():
    return render_template("streaming.html")

@app.route("/speequal/start")
def start():
    if is_running():
        return "Model is already running", 400

    pipeline = SpeakerDiarization(app._config)
    source = WebSocketAudioSource(44100, HOST, PORT_WEBSOCKET)

    app._inference = StreamingInference(
        pipeline=pipeline,
        source=source, 
        do_profile=False, 
        do_plot=False, 
        show_progress=False
    )

    time_index = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    app._inference.attach_observers(RTTMWriter("mic://localhost", f"data/derived/webapp/{time_index}.rttm"))
    app._inference.attach_observers(WSAggregationObserver(source))

    def inference_runner():
        print("Waiting for signal..")
        app._inference()

    thread = threading.Thread(target=inference_runner)
    thread.start()

    return Response(status = 200)

@app.route("/speequal/stop")
def stop():
    if not is_running():
        return "Model is not running", 400
        
    app._inference.source.close()
    init()

    return Response(status = 200)

@app.route("/speequal/status")
def status():
    return {"status": is_running()}

@app.route("/speequal/reset")
def reset():
    if not is_running():
        return "Model is not running", 400

    app._inference.pipeline.reset()

    return Response(status = 200)

@app.route("/speequal/config/get")
def get_config():
    return {
        "tau_active": app._config.tau_active,
        "rho_update": app._config.rho_update,
        "delta_new": app._config.delta_new,
        "max_speakers": app._config.max_speakers
    }

@app.route("/speequal/config/update")
def update_config():
    if "tau_active" in request.args:
        app._config.tau_active = float(request.args["tau_active"])

    if "rho_update" in request.args:
        app._config.rho_update = float(request.args["rho_update"])

    if "delta_new" in request.args:
        app._config.delta_new = float(request.args["delta_new"])

    if "max_speakers" in request.args:
        app._config.max_speakers = int(request.args["max_speakers"])
            
    return Response(status = 200)


if __name__ == "__main__":  
   app.run(host=HOST, port=PORT_FLASK)  
