## Project Roadmap

### Week 1
- Preparing workspace
- Get in touch with the challenge
- Find infos and papers on speaker diarization
- Apply some rapid prototyping to find the pros/cons of the models

#### Achievements:

- Successful workspace set-up (git, virtual environment, etc.)
- Rapid prototype based on x-vectors (speechbrain) and clustering, only post-hoc application
- Clustering methods tested:
    - Kmeans (not promising because indeterministic)
    - Agglomerative (okay performance)
    - Birch (fast and good performance)
    - DBSCAN (intense hyperparameter-tuning needed)

- Finding Diart framework as the most promising framework for real-time speaker diarization

### Week 2
- Find out which approach is applicable and put more effort into it
- DIART seems promising, but is it really applicable? Getting more into detail on DIART configuration. E.g. VAD, Thresholds to reduce confusion
- Getting more into detail on i- and x-vectors
- We need more labeled audio data. Where to get it? Can we provide audio data as a simulated live stream?
- Create mid-term presentation
- Think about adding a Max-speakers setting in the app
- Think about a voice-heterogenity setting in the app

#### Achievements:
- Sleek HTML/Chart.js frontend prototype (todo: check JSON pipeline for delays)
- Routing Zoom/Youtube audio into the application via pavucontrol for real-time clustering (todo: get microphone working parallel)
- Finalizing midterm presentation (todo: who does which part?)
- Diart hyperparameter experiments for better model performance: 
    - tau_active 0.6 (speaker activation threshold)
    - rho_update = 0.3 (The centroid a speaker is mapped to is only updated if the ratio of speech/chunk duration of a given local speaker is greater than this threshold.)
    - delta_new = 1 (threshold for adding new speaker, depends on embedding; .5 for pyannote/embedding, .05 for xvect-voxceleb)
- Understanding neural network structure for speaker embedding
- Explore clustering options in Diart

### Week 3
- Train the underlying embedding model ourselves
- Instead of "speaker0" show the real name => Speaker detection with prior training
- Perform live-tests in real world environment. E.g. Webcalls, Room microphone, Phone Microphone
- Finalize the User Interface

### Week 4
- Prepare the final presentation
- Clean up the repo
- Create documentation

