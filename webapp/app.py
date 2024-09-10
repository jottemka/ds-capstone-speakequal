from diart import SpeakerDiarization, SpeakerDiarizationConfig
from diart.sources import WebSocketAudioSource
from diart.inference import StreamingInference
from diart.models import SegmentationModel, EmbeddingModel
from diart.sinks import Observer

from flask import Flask, render_template

from huggingface_hub import login

import json

HUGGING_FACE_TOKEN = "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"

class WSAggregationObserver(Observer):

    def __init__(self, source) -> None:
        super().__init__()
        self.source = source

    def on_next(self, value) -> None:
        annotation = value[0]
        if not annotation:
            return
        print(annotation)
        chart = annotation.chart()
        if len(chart) > 0:
            self.source.send(json.dumps(chart))


app = Flask(__name__)
app.pipeline = None
app.source = None

@app.route("/")
def index():
    return render_template("streaming.html")

@app.route("/service/start")
def start():
    #login(HUGGING_FACE_TOKEN)

    segmentation = SegmentationModel.from_pretrained("pyannote/segmentation")
    embedding = EmbeddingModel.from_pretrained("pyannote/embedding")

    config = SpeakerDiarizationConfig(
        segmentation=segmentation,
        embedding=embedding,
        #tau_active = .1, # Threshold for detecting active speakers.
        delta_new = .7, # If the distance between a local speaker and all centroids is larger than delta_new, then a new centroid is created for the current speaker.
        metric = "cosine",
        max_speakers = 20,
)

    app.pipeline = SpeakerDiarization(config)
    app.source = WebSocketAudioSource(44100, "127.0.0.1", 7007)

    inference = StreamingInference(
        app.pipeline, 
        app.source, 
        do_profile=False, 
        do_plot=False, 
        show_progress=False
    )

    inference.attach_observers(WSAggregationObserver(app.source))

    print("Waiting for signal..")
    inference()
    return {}

@app.route("/service/stop")
def stop():
    # TODO Impl.
    if app.source is not None:
        print(type(app.source))
        app.source.close()
    
    return {}

@app.route("/service/reset")
def reset():
    # FIXME Return http error code
    if app.pipeline is not None:
        print("Hello")
        app.pipeline.reset()

@app.route("/service/update-hparams")
def update_hparams(tau_active=None, rho_update=None, delta_new=None, metric=None, max_speakers=None):
    # FIXME Return http error code
    if app.pipeline is not None:
        if tau_active is not None:
            app.pipeline.clustering.tau_active = tau_active

        if rho_update is not None:
            app.pipeline.clustering.rho_update = rho_update

        if delta_new is not None:
            app.pipeline.clustering.delta_new = delta_new

        if metric is not None:
            app.pipeline.clustering.metric = metric

        if max_speakers is not None:
            app.pipeline.clustering.max_speakers = max_speakers

if __name__ == "__main__":  
   app.run()  
