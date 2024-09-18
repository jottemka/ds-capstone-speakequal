from diart import SpeakerDiarization, SpeakerDiarizationConfig
from diart.sources import MicrophoneAudioSource
from diart.inference import StreamingInference
from diart.models import SegmentationModel, EmbeddingModel
from diart.sinks import RTTMWriter

from huggingface_hub import login

import datetime


#login("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")

config = SpeakerDiarizationConfig(
    segmentation=SegmentationModel.from_pretrained("pyannote/segmentation-3.0"),
    embedding=EmbeddingModel.from_pretrained("pyannote/embedding")
)

pipeline = SpeakerDiarization(config)
source = MicrophoneAudioSource()
inference = StreamingInference(
    pipeline=pipeline,
    source=source, 
    do_profile=False, 
    do_plot=True, 
    show_progress=False
)

time_index = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
inference.attach_observers(RTTMWriter("mic://localhost", f"data/derived/tester/{time_index}.rttm"))

print("Waiting for signal..")
prediction = inference()
