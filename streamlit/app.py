from diart.sources import MicrophoneAudioSource
from diart.inference import StreamingInference
from diart.models import SegmentationModel, EmbeddingModel
from diart.sinks import Observer, RTTMWriter, _extract_prediction
from diart import SpeakerDiarization, SpeakerDiarizationConfig

from huggingface_hub import login

import streamlit as st
import plotly.graph_objects as go

import threading

PIE_COLORS = [
    '#FFB3BA',
    '#BAFFC9',
    '#FFFFBA',
    '#BAE1FF',
    '#CBAACB',
    '#FFDAC1',
    '#B5EAD7',
    '#E2F0CB',
    '#FF9AA2',
    '#FDFD96',
    '#A1CAF1',
    '#FFCBF2',
    '#E0BBE4',
    '#D4A5A5',
    '#FDE2E4',
    '#C1E1C1',
    '#C4DEF6',
    '#FAD2E1',
    '#F5E1DA',
    '#FFDFBA',
]


if "stream" not in st.session_state:
    st.session_state.stream = False

if "source" not in st.session_state:
    st.session_state.source = None

if "data" not in st.session_state:
    st.session_state.data = {}

class PieChartObserver(Observer):

    def __init__(self) -> None:
        super().__init__()

    def on_next(self, value) -> None:
        prediction = _extract_prediction(value)
        if prediction:
            print(prediction)
            for label, sec_spoken in prediction.chart():
                if label in st.session_state.data:
                    st.session_state.data[label] += sec_spoken
                else:
                    st.session_state.data[label] = sec_spoken


def toggle_streaming():
    st.session_state.stream = not st.session_state.stream

def stop_streaming():
    print("Stop streaming..")
    try:
        if st.session_state.source is not None:
            st.session_state.source.close()
    finally:
        st.session_state.stream = False
        st.session_state.source = None
        st.session_state.data = {}

def start_streaming(**kwargs):
    print("Start streaming..")

    config = SpeakerDiarizationConfig(**kwargs)
    pipeline = SpeakerDiarization(config)
    st.session_state.source = MicrophoneAudioSource()

    inference = StreamingInference(
        pipeline, 
        st.session_state.source, 
        do_profile=False, 
        do_plot=False, 
        show_progress=False
    )

    inference.attach_observers(PieChartObserver())
    inference.attach_observers(RTTMWriter("mic://localhost", "../data/derived/eval-streamlit.rttm"))

    def inference_runner():
        print("Waiting for signal..")
        inference()

    thread = threading.Thread(target=inference_runner)
    st.runtime.scriptrunner.add_script_run_ctx(thread)
    thread.start()


tau_active = st.sidebar.slider("tau_active", min_value=0.0, max_value=1.0, step=0.05, value=0.6)
rho_update = st.sidebar.slider("rho_update", min_value=0.0, max_value=1.0, step=0.05, value=0.3)
delta_new = st.sidebar.slider("delta_new", min_value=0.0, max_value=2.0, step=0.05, value=1.0)
max_speakers = st.sidebar.slider("max_speakers", min_value=1, max_value=20, step=1, value=20)

st.sidebar.button("Start streaming", disabled=st.session_state.stream, on_click=toggle_streaming)
st.sidebar.button("Stop streaming", disabled=not st.session_state.stream, on_click=toggle_streaming)

col1, col2, col3 = st.columns([0.25, 0.5, 0.25])
col2.image("assets/img/logo.png")
col2.image("assets/img/conversation.jpg")

plot_placeholder = col2.empty()

@st.fragment(run_every=3.0)
def update_chart(data):
    fig = go.Figure(data=[go.Pie(values=list(data.values()), labels=list(data.keys()))])
    fig.update_traces(hoverinfo='label+percent', textinfo='value', textfont_size=20, marker=dict(colors=PIE_COLORS, line=dict(color='#000000', width=2)))
    fig.update_layout(transition=dict(duration=500, easing='cubic-in-out'))
    plot_placeholder.plotly_chart(fig)

if st.session_state.stream is True:
    #login("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")
    segmentation = SegmentationModel.from_pretrained("pyannote/segmentation-3.0")
    embedding = EmbeddingModel.from_pretrained("pyannote/embedding")

    start_streaming(
        segmentation=segmentation,
        embedding=embedding,
        tau_active=tau_active,
        rho_update=rho_update,
        delta_new=delta_new,
        max_speakers=max_speakers
    )
else:
    stop_streaming()

update_chart(st.session_state.data)