from diart import SpeakerDiarization, SpeakerDiarizationConfig
from diart.sources import MicrophoneAudioSource
from diart.inference import StreamingInference
from diart.sinks import RTTMWriter
from diart.models import SegmentationModel, EmbeddingModel

from huggingface_hub import login

HUGGING_FACE_TOKEN = "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"
#login(HUGGING_FACE_TOKEN)

segmentation = SegmentationModel.from_pretrained("pyannote/segmentation")
embedding = EmbeddingModel.from_pretrained("pyannote/embedding")

config = SpeakerDiarizationConfig(
    segmentation=segmentation,
    embedding=embedding,
    delta_new=0.7
)
pipeline = SpeakerDiarization(config)
mic = MicrophoneAudioSource()

inference = StreamingInference(pipeline, mic, do_plot=True)

prediction = inference()