from diart import SpeakerDiarization, SpeakerDiarizationConfig
from diart.sources import WebSocketAudioSource
from diart.inference import StreamingInference
from diart.models import SegmentationModel, EmbeddingModel
from diart.sinks import Observer
import webbrowser

from huggingface_hub import login

import json

SAMPLE_RATE = 16000
#HUGGING_FACE_TOKEN = "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"

class DummyObserver(Observer):

    def __init__(self) -> None:
        super().__init__()

    def on_next(self, value) -> None:
        if len(value[0]) > 0:
            print(value[0])

def client_response(annotation):
    chart = annotation[0].chart()
    if len(chart) > 0:
        source.send(json.dumps(chart))

#login(HUGGING_FACE_TOKEN)

segmentation = SegmentationModel.from_pretrained("pyannote/segmentation-3.0")
embedding = EmbeddingModel.from_pretrained("pyannote/embedding")

config = SpeakerDiarizationConfig(
    segmentation=segmentation,
    embedding=embedding,
    sample_rate=SAMPLE_RATE,
    #duration=5,
    #step=0.5,
    #latency=0.5,
    #tau_active = .576, # Threshold for detecting active speakers.
    delta_new = 1, # If the distance between a local speaker and all centroids is larger than delta_new, then a new centroid is created for the current speaker.
    metric = "cosine",
    max_speakers = 20,
)

pipeline = SpeakerDiarization(config)
source = WebSocketAudioSource(SAMPLE_RATE, "127.0.0.1", 7007)

inference = StreamingInference(
    pipeline, 
    source, 
    do_profile=False, 
    do_plot=False, 
    show_progress=False
)

inference.attach_hooks(client_response)
inference.attach_observers(DummyObserver())

webbrowser.open('../webapp/streaming.html')

print("Waiting for signal..")
prediction = inference()


