# Neurocode Studio

<p align="center">
  <img src="static/logo.png" width="160" height="160" alt="Neurocode Studio Logo"/>
</p>

**Neurocode Studio** is a high-fidelity psychoacoustic audio processing engine and desktop suite designed for synthesizing subliminal audio tracks. It encodes verbal affirmation texts directly into high-frequency stereo carriers using multi-layer Amplitude Modulation (AM), optional brainwave entrainment (Binaural Beats), and background music beds with surgical DSP filtering.

The entire application runs as a standalone desktop suite (using `pywebview` and `FastAPI`) or as a web service.

---

## Key Features

- **Neural TTS Engine**: Multi-language Text-to-Speech synthesis (English, Ukrainian, Russian) with automatic per-sentence language detection.
- **Symmetrical AM Stereo Carriers**: Speech signals are modulated onto symmetrical high-frequency carriers starting at **3000 Hz** up to **18000 Hz** across both left and right channels to enforce bilateral brain hemisphere stimulation.
- **Ultra-HD Mode**: A premium, high-density 4-layer configuration (2 layers panned Left, 2 layers panned Right) featuring randomized carrier offsets ($\pm 300\text{ Hz}$) and independent speed-up factors.
- **Golden Speed Range**: Asynchronous layer speech stretching randomized between **2.0x** and **4.0x** — the optimal speed for subconscious processing and auditory comprehension.
- **Instant Entry Technology**: Base carrier layers start with a $0\text{-second}$ offset, ensuring that affirmation signals enter the listener's subconscious immediately without initial silent gaps.
- **Brainwave Entrainment (Binaural Beats)**: Generates precise binaural frequencies to stimulate targeted mental states:
  - **Delta (2 Hz)**: Deep sleep, physical repair, and restoration.
  - **Theta (4 Hz)**: Deep meditation, visualization, and subconscious openness.
  - **Alpha (10 Hz)**: Flow state, active learning, and relaxed focus.
  - **Beta (15 Hz)**: Cognitive activity, alert processing, and problem-solving.
- **Surgical Notch EQ**: A high-selectivity notch filter ($Q = 30$) carved exactly at the binaural carrier frequencies (e.g., $136.1\text{ Hz}$ and $140.1\text{ Hz}$) inside the background music, preventing the music from acoustically masking the therapeutic beat.
- **Automated Audio Engineering**: Real-time automatic RMS volume normalization of background music tracks, smooth fade-in/fade-out transitions, and peak-limiting to prevent digital clipping.
- **Composer-Grade Output**: Direct export to uncompressed **48 kHz / 16-bit / Stereo WAV** files.

---

## Technical Mechanics & Psychoacoustics

```
                       ┌─────────────────────────┐
                       │   Affirmation Text      │
                       └────────────┬────────────┘
                                    ▼
                       ┌─────────────────────────┐
                       │  Multi-Language TTS    │
                       └────────────┬────────────┘
                                    ▼
                       ┌─────────────────────────┐
                       │ Asynchronous Stretching │ (2.0x - 4.0x speed)
                       └────────────┬────────────┘
                                    ▼
                       ┌─────────────────────────┐
                       │   Carrier Modulation    │ (AM Modulation: 3kHz - 18kHz)
                       └──────┬───────────┬──────┘
                              │           │
                     (Left Ch)│           │(Right Ch)
                              ▼           ▼
                      ┌───────────┐   ┌───────────┐
                      │ Left AM   │   │ Right AM  │
                      │ Carriers  │   │ Carriers  │
                      └──────┬────┘   └────┬──────┘
                             │             │
                             └──────┬──────┘
                                    ▼
                       ┌─────────────────────────┐
                       │  Binaural Beat Sync     │ (θ, α, δ, β waves)
                       └────────────┬────────────┘
                                    ▼
                       ┌─────────────────────────┐
                       │    Surgical Notch EQ    │ (Q=30 on background track)
                       └────────────┬────────────┘
                                    ▼
                       ┌─────────────────────────┐
                       │   Stereo Mix & Export   │ (48kHz WAV)
                       └─────────────────────────┘
```

### 1. Amplitude Modulation (AM) Subliminal Encoding
Standard audio signals are easily captured by the conscious mind. By modulating the amplitude of high-frequency sine carriers (ranging from 3 kHz up to 18 kHz) with the speech signal, the verbal content is shifted into a frequency spectrum where it bypasses the conscious threshold of the human ear, yet remains fully decodable by the auditory cortex and the subconscious mind.

### 2. Symmetrical Stereo Grid
Instead of panning layers in an offset comb grid, both Left and Right channels contain matching carrier frequencies starting from 3000 Hz. This symmetry creates a cohesive, balanced soundstage, reinforcing bilateral integration in the brain hemispheres.

### 3. Golden Speed Stretches
To increase the cognitive throughput to the subconscious, layers are accelerated between 2.0x and 4.0x. This range is high enough to compress information and bypass verbal resistance, while remaining fully intelligible to the subconscious processing centers of the brain.

### 4. Surgical Notch Filtering
To combine subliminal voice carriers with background music without losing the binaural entrainment effect, the background music undergoes a sharp parametric notch cut at the exact carrier frequencies of the binaural wave (usually around $136.1\text{ Hz}$). This prevents acoustic masking and maintains the therapeutic beat's effectiveness.

---

## Patent Foundations

The DSP pipelines implemented in Neurocode Studio build upon established psychoacoustic and neuro-electrical stimulation methodologies. Key patent foundations referenced by this system include:

- **Amplitude Modulation (AM) Subliminal Encoding**:
  - **U.S. Patent No. 5,159,703** (*"Silent Subliminal Presentation System"*, Oliver M. Lowery, 1992 - Expired): Describes the conversion of standard audio to silent subliminal frequencies via high-frequency carrier wave modulation.
- **Binaural Beats & Hemispheric Synchronization**:
  - **U.S. Patent No. 3,884,218** (Robert A. Monroe, 1975 - Expired): Pioneer patent on hemispheric synchronization (Hemi-Sync) using binaural beat patterns.
  - **U.S. Patent No. 5,213,562** (Robert A. Monroe, 1993 - Expired): Describes methods of inducing specific mental states by superimposing binaural frequency signals.
  - **U.S. Patent No. 5,356,368** (Robert A. Monroe, 1994 - Expired): Methods and apparatus for inducing sleep and targeted states of consciousness.
- **Surgical Notch EQ**:
  - Tailors frequency-notched music similar to auditory training schemes used to manage critical-band audio. Commercial hearing-aid implementations are licensed under patents such as **U.S. Patent No. 9,549,269 B2** (Sivantos / Signia Notch Therapy).

---

## Project Structure

```
SubliminalGenerator/
├── app.py                     # FastAPI backend & webview window initializer
├── requirements.txt           # Python package dependencies
├── test_api_short.py          # Short API endpoint smoke tests
├── engine/
│   ├── encoder.py             # Audio DSP: AM grid, Binaural, Notch filter, Mixdown
│   ├── tts.py                 # TTS synthesis wrapper (edge-tts)
│   └── music/                 # Directory containing background music files (.mp3/.wav)
└── static/
    ├── index.html             # UI structure (English)
    ├── app.js                 # UI logic, state management, and status polling
    └── style.css              # Custom styling (editorial dark theme, Liquid Flow loader)
```

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher.
- **FFmpeg**: Must be installed on your system and added to your system `PATH` (required by `librosa` and `soundfile` for decoding/encoding audio).

### Step 1: Clone the Repository
```bash
git clone https://github.com/Bergschloss/NeuroCode.git
cd NeuroCode/SubliminalGenerator
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

*Note: Major dependencies include: `fastapi`, `uvicorn`, `edge-tts`, `soundfile`, `librosa`, `scipy`, `numpy`, `miniaudio`, and `pywebview`.*

---

## Running the Application

### Option A: Standalone GUI Mode (Desktop App)
To launch the application as a standalone desktop interface:
```bash
python app.py
```
This starts a lightweight window hosting the frontend with native file dialog integrations.

### Option B: Web Browser Mode
To run the backend as a local web server and access the UI from any browser:
```bash
python app.py --browser
```
Then, open your browser and navigate to:
```
http://127.0.0.1:7860
```

---

## License

This project is created for private research and development in the field of audio-psychoacoustics and subconscious stimulation.
