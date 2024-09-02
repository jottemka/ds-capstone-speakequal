HUGGING_FACE_TOKEN = "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"

from diart import SpeakerDiarization
from diart.sources import MicrophoneAudioSource
from diart.inference import StreamingInference
from diart.sinks import RTTMWriter
from huggingface_hub import login
import diart.models as m
from diart import SpeakerDiarization, SpeakerDiarizationConfig
from diart.models import EmbeddingModel, SegmentationModel
import warnings

warnings.simplefilter(action='ignore')

segmentation = m.SegmentationModel.from_pretrained("pyannote/segmentation")
embedding = m.EmbeddingModel.from_pretrained("speechbrain/spkrec-xvect-voxceleb")

config = SpeakerDiarizationConfig(
    segmentation=segmentation,
    embedding=embedding,
)

#login(HUGGING_FACE_TOKEN)
pipeline = SpeakerDiarization(config)
mic = MicrophoneAudioSource()
inference = StreamingInference(pipeline, mic, do_plot=True)
inference.attach_observers(RTTMWriter(mic.uri, "data/out.rttm"))
prediction = inference()

SpeakerDiarization(  )
