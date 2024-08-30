from diart import SpeakerDiarization, SpeakerDiarizationConfig
from diart.sources import MicrophoneAudioSource
from diart.inference import StreamingInference
from diart.sinks import RTTMWriter
import diart

from huggingface_hub import login

HUGGING_FACE_TOKEN = "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"
login(HUGGING_FACE_TOKEN)

segmentation = diart.models.SegmentationModel.from_pretrained("pyannote/segmentation")
embedding = diart.models.EmbeddingModel.from_pretrained("pyannote/embedding")

config = SpeakerDiarizationConfig(
    segmentation=segmentation,
    embedding=embedding,
    step=0.5,
    latency=0.5,
    tau_active=0.555,
    rho_update=0.422,
    delta_new=1.517
)
pipeline = SpeakerDiarization(config)
mic = MicrophoneAudioSource()

inference = StreamingInference(pipeline, mic, do_plot=True)
inference.attach_observers(RTTMWriter(mic.uri, "data/derived/stream.rttm"))

prediction = inference()