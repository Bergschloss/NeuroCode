# Neurocode Studio

<p align="center">
  <img src="static/logo.png" width="160" height="160" alt="Neurocode Studio Logo"/>
</p>

**Neurocode Studio** is a high-fidelity psychoacoustic audio processing engine and desktop suite designed for synthesizing subliminal audio tracks. It encodes verbal affirmation texts directly into high-frequency stereo carriers using multi-layer Amplitude Modulation (AM), optional brainwave entrainment (Binaural Beats), and background music beds with surgical DSP filtering.

The entire application runs as a standalone desktop suite (using `pywebview` and `FastAPI`) or as a web service.

---

## Key Features

- **Neural TTS Engine**: Multi-language Text-to-Speech synthesis (English, Ukrainian, Russian) with automatic per-sentence language detection.
- **Band-Limited AM Stereo Carriers**: Speech is low-pass filtered before modulation and placed on carriers from **3000 Hz** to **17500 Hz**, keeping AM sidebands below the 44.1 kHz Nyquist limit.
- **Massive Multi-Layering**: Supports dense psychoacoustic stacking of up to 24 parallel voice layers (default 12) with randomized speed ($\pm 0.05\text{x}$) and frequency jitters ($\pm 150\text{ Hz}$) to eliminate phantom mono images and create a wide, diffuse subliminal field.
- **Configurable Speed Range**: Asynchronous layer speech stretching can be randomized across a user-selected range.
- **Zero-offset First Layer**: The first left-channel carrier starts at a $0\text{-second}$ offset, while other layers use offsets to reduce cross-channel correlation.
- **Brainwave Entrainment (Binaural Beats)**: Generates precise binaural frequencies to stimulate targeted mental states:
  - **Delta (2 Hz)**: Deep sleep, physical repair, and restoration.
  - **Theta (4 Hz)**: Deep meditation, visualization, and subconscious openness.
  - **Alpha (10 Hz)**: Flow state, active learning, and relaxed focus.
  - **Beta (15 Hz)**: Cognitive activity, alert processing, and problem-solving.
- **Surgical Notch EQ**: A high-selectivity notch filter ($Q = 30$) carved exactly at the binaural carrier frequencies (e.g., $136.1\text{ Hz}$ and $140.1\text{ Hz}$) inside the background music, preventing the music from acoustically masking the therapeutic beat.
- **Automated Audio Engineering**: Real-time automatic RMS volume normalization of background music tracks, smooth fade-in/fade-out transitions, and peak-limiting to prevent digital clipping.
- **WAV Output**: Direct export to uncompressed **44.1 kHz / 16-bit / Stereo WAV** files.
- **Controlled Processing Queue**: One DSP-heavy generation runs at a time; later jobs wait safely and can be cancelled.

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
The encoder low-pass filters speech to 3.5 kHz and modulates it onto sine carriers ranging from 3 kHz to 17.5 kHz. The band limit prevents upper AM sidebands from folding across the 22.05 kHz Nyquist boundary. This is an experimental signal-processing technique; the application does not claim that the resulting content bypasses conscious hearing or produces a specific neurological response.

### 2. Symmetrical Stereo Grid
Both left and right channels contain carrier grids from 3000 Hz to 17500 Hz. This produces a balanced stereo signal without making claims about hemispheric integration.

### 3. Golden Speed Stretches
Layers can be accelerated at different rates to create a dense asynchronous texture. Faster speech is not guaranteed to remain intelligible or to affect subconscious processing.

### 4. Surgical Notch Filtering
When enabled, the background music receives a narrow notch cut at the selected binaural carrier frequencies. This reduces competing energy at those frequencies but does not establish a therapeutic effect.

---

## Patent Foundations

The DSP pipeline is inspired by techniques described in the following historical patents. A patent describes an invention; it is not evidence of clinical efficacy:

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
├── job_state.py               # Bounded job registry, cancellation and TTS LRU cache
├── telegram_client.py         # Telegram config and HTTP adapter
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
