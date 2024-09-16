from diart import SpeakerDiarization, SpeakerDiarizationConfig
from diart.sources import MicrophoneAudioSource
from diart.inference import StreamingInference
from diart.models import SegmentationModel, EmbeddingModel
from diart.sinks import RTTMWriter

from huggingface_hub import login


#login("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")

config = SpeakerDiarizationConfig(
    segmentation=SegmentationModel.from_pretrained("pyannote/segmentation"),
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

inference.attach_observers(RTTMWriter("mic://localhost", "data/derived/eval-tester.rttm"))

print("Waiting for signal..")
prediction = inference()
