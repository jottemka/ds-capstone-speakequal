from diart import SpeakerDiarization, SpeakerDiarizationConfig
from diart.sources import WebSocketAudioSource
from diart.inference import StreamingInference
from diart.models import SegmentationModel, EmbeddingModel
from diart.sinks import Observer
import webbrowser

from huggingface_hub import login

import json

HUGGING_FACE_TOKEN = "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"
#login(HUGGING_FACE_TOKEN)

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


segmentation = SegmentationModel.from_pretrained("pyannote/segmentation")
embedding = EmbeddingModel.from_pretrained("pyannote/embedding")

config = SpeakerDiarizationConfig(
    segmentation=segmentation,
<<<<<<< HEAD
    embedding=embedding,
    #delta_new=0.7,
    max_speakers=3
=======
    embedding=embedding
>>>>>>> main
)

pipeline = SpeakerDiarization(config)
source = WebSocketAudioSource(44100, "127.0.0.1", 7007)

inference = StreamingInference(
    pipeline, 
    source, 
    do_profile=False, 
    do_plot=False, 
    show_progress=False
)

inference.attach_hooks(client_response)
inference.attach_observers(DummyObserver())

#webbrowser.open('../webapp/streaming.html')

print("Waiting for signal..")

prediction = inference()
