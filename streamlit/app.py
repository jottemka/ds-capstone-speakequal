from diart.sources import MicrophoneAudioSource
from diart.inference import StreamingInference
from diart.models import SegmentationModel, EmbeddingModel
from diart.sinks import Observer, RTTMWriter, _extract_prediction
from diart import SpeakerDiarization, SpeakerDiarizationConfig

from huggingface_hub import login
your_huggingface_token = ""

import streamlit as st
import plotly.graph_objects as go

import threading

PIE_COLORS = [
    '#FDD5B1',  # Light Peachy Orange
    '#A6CEE3',  # Pastel Blue
    '#FDD9A2',  # Pastel Orange
    '#C9EBF6',  # Light Cyan
    '#F9E79F',  # Pastel Yellow
    '#B3E2E5',  # Light Sky Blue
    '#DDA0DD',  # Pastel Purple
    '#F7B6A2',  # Soft Peach
    '#B2D8D8',  # Light Teal
    '#FCF4A3',  # Soft Yellow
    '#CAB2D6',  # Soft Lilac
    '#FFCCCB',  # Light Red (use sparingly)
    '#E6CFE2',  # Light Pink
    '#F6BDC0',  # Pale Pink
    '#D7E9D7',  # Pastel Green
    '#CCE5FF',  # Light Pastel Blue
    '#BDE4B7',  # Soft Green
    '#FFF5BA',  # Soft Mustard Yellow
    '#F3C1D9',  # Soft Pinkish Violet
    '#FDEBD0',  # Light Peach
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

st.sidebar.title("Settings")

tau_active_description = "Detection-threshold for active speakers."
rho_update_description = "Cluster-update threshold."
delta_new_description = "New-speaker threshold."
max_speakers_description = "Maximum number of speakers."

tau_active = st.sidebar.slider(tau_active_description, min_value=0.0, max_value=1.0, step=0.05, value=0.6)
rho_update = st.sidebar.slider(rho_update_description, min_value=0.0, max_value=1.0, step=0.05, value=0.3)
delta_new = st.sidebar.slider(delta_new_description, min_value=0.0, max_value=2.0, step=0.05, value=0.8)
max_speakers = st.sidebar.slider(max_speakers_description, min_value=1, max_value=20, step=1, value=20)

st.sidebar.button("Start streaming", disabled=st.session_state.stream, on_click=toggle_streaming)
st.sidebar.button("Stop streaming", disabled=not st.session_state.stream, on_click=toggle_streaming)

col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
col2.image("assets/img/logo.png")
col2.image("assets/img/conversation.jpg", width = 300)

plot_placeholder = col2.empty()

@st.fragment(run_every=3.0)
def update_chart(data):
    fig = go.Figure(data=[go.Pie(values=list(data.values()), labels=list(data.keys()), hole=.3 )])
    fig.update_traces(texttemplate='%{value:.0f}s', hoverinfo='label+percent', textinfo='value', textfont_size=20, marker=dict(colors=PIE_COLORS, line=dict(color='#F5F5F5', width=2)))
    fig.update_layout(transition=dict(duration=500, easing='cubic-in-out'))
    plot_placeholder.plotly_chart(fig)
    

if st.session_state.stream is True:
    #login(your_huggingface_token)
    segmentation = SegmentationModel.from_pretrained("pyannote/segmentation-3.0")
    embedding = EmbeddingModel.from_pretrained("pyannote/embedding")

    start_streaming(
        segmentation=segmentation,
        embedding=embedding,
        tau_active=tau_active,
        rho_update=rho_update,
        delta_new=delta_new,
        max_speakers=max_speakers,
        latency = 3
    )
else:
    stop_streaming()

update_chart(st.session_state.data)