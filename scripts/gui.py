import torch
import torchaudio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from speechbrain.inference import SpeakerRecognition
from sklearn.cluster import AgglomerativeClustering, KMeans, MiniBatchKMeans, Birch, DBSCAN, SpectralCoclustering
from pyannote.core import Segment, Annotation, notebook
from pyannote.metrics.diarization import DiarizationErrorRate
import sys
import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
from scipy.io.wavfile import write
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt5.QtCore import pyqtSlot, QTimer
import warnings

warnings.filterwarnings("ignore")


# Load pre-trained x-vector model
xvector_model = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-xvect-voxceleb",
    savedir="pretrained_models/spkrec-xvect-voxceleb"
)

class AudioRecorderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.fs = 16000  # Sample rate, must be 16k
        self.recording_data = []  # To store the recording data in chunks
        self.is_recording = False  # To track if recording is ongoing
        self.stream = None  # Stream for real-time recording

    def initUI(self):
        layout = QVBoxLayout()

        # Record/Stop button
        self.record_button = QPushButton('Record', self)
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)

        # Plot waveform button
        self.plot_button = QPushButton('Analyze', self)
        self.plot_button.clicked.connect(self.plot_waveform)
        layout.addWidget(self.plot_button)
        self.plot_button.setEnabled(False)  # Disabled until a recording is made

        # Status label
        self.status_label = QLabel('Press "Record" to start recording', self)
        layout.addWidget(self.status_label)

        # Set layout and window settings
        self.setLayout(layout)
        self.setWindowTitle('SpeakEqual')
        self.setGeometry(300, 300, 300, 200)
        self.show()

    @pyqtSlot()
    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.status_label.setText('Recording...')
        self.record_button.setText('Stop')
        self.is_recording = True

        # Start streaming and recording
        self.stream = sd.InputStream(samplerate=self.fs, channels=1, callback=self.audio_callback)
        self.stream.start()

    def stop_recording(self):
        self.status_label.setText('Recording stopped. Press "Analyze" to view it.')
        self.record_button.setText('Record')
        self.is_recording = False

        # Stop streaming
        self.stream.stop()
        self.stream.close()

        # Convert recorded chunks to a numpy array
        self.recording_data = np.concatenate(self.recording_data, axis=0)
        write('data/derived/output.wav', self.fs, self.recording_data)  # Save the recording to a WAV file
        self.plot_button.setEnabled(True)  # Enable plotting button after recording

    def audio_callback(self, indata, frames, time, status):
        """Callback function to receive audio chunks during recording."""
        if status:
            print(status)
        self.recording_data.append(indata.copy())

    @pyqtSlot()
    def plot_waveform(self):
        if self.recording_data.any():

            # Load audio file (fs is sampling rate)
            signal, fs = torchaudio.load("data/derived/output.wav")

            # Ensure the audio is mono and 16kHz
            if signal.shape[0] > 1:
                signal = torch.mean(signal, dim=0, keepdim=True)

            #if fs != 16000:
            #    signal = torchaudio.transforms.Resample(fs, 16000)(signal)

            # Define segment length and step
            segment_length = .5  # adjust to preference
            step = .5  # adjust to preference
            segment_length_samples = int(segment_length * 16000)
            step_samples = int(step * 16000)

            # Extract x-vectors for each segment
            xvectors = []
            segments = []
            for start in range(0, signal.shape[1] - segment_length_samples, step_samples):
                segment = signal[:, start:start + segment_length_samples]
                xvector = xvector_model.encode_batch(segment)
                xvectors.append(xvector.squeeze().detach().numpy())
                segments.append(Segment(start / 16000, (start + segment_length_samples) / 16000))

            xvectors = np.array(xvectors)

            # Perform agglomerative clustering
            num_speakers = 2  # Change this number based on expected number of speakers
            labels = DBSCAN(eps=.186, min_samples=8, metric="cosine", n_jobs=-1).fit_predict(xvectors)

            # Create a pyannote annotation for visualization and output
            annotation = Annotation()
            for i, label in enumerate(labels):
                annotation[segments[i]] = f"Speaker {label + 1}"

            # Display the diarization result
            notebook.plot_annotation(annotation, time=True, legend=True)
            plt.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AudioRecorderApp()
    sys.exit(app.exec_())