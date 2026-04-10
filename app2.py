import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import spectrogram
from scipy.io import wavfile
import tempfile, time

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="⚡ Whistler Lab", layout="wide")

# -----------------------------
# FUTURISTIC CSS
# -----------------------------
st.markdown("""
<style>
/* Background */
html, body, [class*="css"] {
    background: radial-gradient(1200px 600px at 10% -10%, #1a1a3a 0%, #0b0b16 50%, #05050a 100%);
    color: #e8f1ff;
}

/* Neon header */
.neon-title {
    text-align:center;
    font-size: 42px;
    font-weight: 800;
    letter-spacing: 1px;
    color:#9ad1ff;
    text-shadow:
      0 0 6px rgba(58,134,255,0.7),
      0 0 16px rgba(58,134,255,0.5),
      0 0 32px rgba(58,134,255,0.35);
    margin-bottom: 10px;
}

/* Glass card */
.glass {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 18px;
    padding: 24px 26px;
    backdrop-filter: blur(14px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.55);
}

/* Accent text */
.accent {
    color:#78b7ff;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(90deg,#3a86ff,#7cc2ff);
    color: white;
    border-radius: 12px;
    padding: 10px 18px;
    border: none;
    font-weight: 700;
    box-shadow: 0 0 14px rgba(58,134,255,0.6);
}
.stButton>button:hover {
    transform: translateY(-1px);
    box-shadow: 0 0 22px rgba(58,134,255,0.9);
}

/* Sidebar tweaks */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0d1c, #070712);
}

/* Metric cards */
.metric {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 14px;
    padding: 18px;
    text-align:center;
    box-shadow: inset 0 0 18px rgba(120,183,255,0.08);
}

/* Divider */
.hr {
    height:1px; background:linear-gradient(90deg, transparent, #3a86ff, transparent);
    margin: 14px 0 18px 0;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# SESSION STATE
# -----------------------------
if "signal" not in st.session_state:
    st.session_state.signal = None
    st.session_state.fs = None

# -----------------------------
# HEADER
# -----------------------------
st.markdown('<div class="neon-title">⚡ WHISTLER SIGNAL LAB</div>', unsafe_allow_html=True)
st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3 = st.tabs(["📘 Theory", "⚙ Simulation", "📊 Results"])

# =========================================================
# THEORY
# =========================================================
with tab1:
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.markdown("### 🌌 Ionospheric Dispersion (LTI View)")
    st.write("""
    Whistler waves originate from lightning and travel along Earth's magnetic field lines.
    The ionosphere behaves like a **dispersive LTI system**, causing **frequency-dependent delay**:
    higher frequencies arrive earlier than lower ones → a descending tone in the spectrogram.
    """)
    st.markdown("**Model:**  \\( Y(f)=H(f)X(f),\\; y(t)=\\mathcal{F}^{-1}\\{Y(f)\\} \\)")
    st.info("👉 Open the **Simulation** tab to generate or import a signal.")
    st.info("Whistler signals typically occur between 300 Hz and 10 kHz.")
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# SIMULATION
# =========================================================
with tab2:

    # Sidebar controls
    st.sidebar.header("⚙ Controls")

    real_mode = st.sidebar.toggle("Realistic Mode", True)
    
    fs = st.sidebar.slider("Sampling Frequency (Hz)", 8000, 48000, 20000)

    alpha = st.sidebar.slider("Dispersion Constant (α)", 200, 1500, 500)

    duration = st.sidebar.slider("Duration (seconds)", 0.5, 5.0, 2.0)

    noise = st.sidebar.slider("Noise Level", 0.0, 0.2, 0.05)

    window = st.sidebar.slider("Spectrogram Window Size", 128, 1024, 256)

    max_freq = st.sidebar.slider("Max Frequency Display (Hz)", 1000, 10000, 5000)

    live_mode = st.sidebar.toggle("🔴 Live Mode (animate)", value=False)
    file = st.sidebar.file_uploader("📂 Upload WAV", type=["wav"])

    # -------------------------
    # SMART VALIDATION SYSTEM
    # -------------------------
    warnings = []
    errors = []
    score = 100  # quality meter (0–100)

    # Sampling frequency
    if fs < 8000:
        errors.append("Sampling frequency too low for whistler signals (≥ 8 kHz recommended)")
        score -= 30
    elif fs < 12000:
        warnings.append("Low sampling rate may distort high-frequency components")
        score -= 10

    # Dispersion constant
    if not (200 <= alpha <= 1500):
        warnings.append("Dispersion constant outside typical whistler range (200–1500)")
        score -= 10

    # Duration
    if duration < 0.5:
        warnings.append("Duration too short — whistler sweep may not be visible")
        score -= 10
    elif duration > 5:
        warnings.append("Duration long — computation heavier than needed")
        score -= 5

    # Noise
    if noise > 0.2:
        warnings.append("Noise too high — signal may be masked")
        score -= 15

    # Window size
    if window < 128:
        warnings.append("Window too small — poor frequency resolution")
        score -= 10
    elif window > 1024:
        warnings.append("Window too large — poor time resolution")
        score -= 10

    # -------------------------
    # UI FEEDBACK
    # -------------------------
    if real_mode:
        st.sidebar.success("Realistic Mode ON")
    else:
        st.sidebar.warning("Free Mode (no constraints)")

    # Errors
    for e in errors:
        st.sidebar.error(e)

    # Warnings
    for w in warnings:
        st.sidebar.warning(w)

    # Quality meter
    st.sidebar.markdown("### ⚡ Signal Quality")
    st.sidebar.progress(max(0, min(score, 100)) / 100)

    if score > 85:
        st.sidebar.success("Excellent signal configuration")
    elif score > 60:
        st.sidebar.info("Good configuration")
    else:
        st.sidebar.error("Poor configuration — adjust parameters")

    # Generate
    if st.sidebar.button("🚀 Generate"):

        # Apply automatic correction
        if real_mode:
            fs = min(max(fs, 8000), 48000)
            alpha = min(max(alpha, 200), 1500)
            duration = min(max(duration, 0.5), 5.0)
            noise = min(max(noise, 0.0), 0.2)
            window = min(max(window, 128), 1024)

            st.sidebar.info("Parameters auto-corrected for realism")

        # STOP if critical error
        if errors and real_mode:
            st.error("❌ Fix errors before generating signal")
            st.stop()

        # ---- Continue simulation ----
        N = int(fs * duration)
        t = np.linspace(0, duration, N)
        f = np.fft.fftfreq(N, 1/fs)

        H = np.exp(-1j * alpha / (np.abs(f) + 1))

        impulse = np.zeros(N)
        impulse[0] = 1

        Y = np.fft.fft(impulse) * H
        y = np.real(np.fft.ifft(Y))

        y += noise * np.random.randn(N)

        st.session_state.signal = y
        st.session_state.fs = fs

    # Upload
    if file is not None:
        fs_r, data = wavfile.read(file)
        if len(data.shape) > 1:
            data = data[:, 0]
        st.session_state.signal = data.astype(float)
        st.session_state.fs = fs_r

    # Display
    if st.session_state.signal is not None:
        y = st.session_state.signal
        fs = st.session_state.fs
        t = np.linspace(0, len(y)/fs, len(y))

        left, right = st.columns(2)

        # TIME
        with left:
            st.markdown("### 📈 Time Domain")
            fig1, ax1 = plt.subplots()
            ax1.plot(t, y, linewidth=1.2)
            ax1.set_title("Signal")
            st.pyplot(fig1)

        # SPEC
        with right:
            st.markdown("### 🎧 Spectrogram")
            f_spec, t_spec, Sxx = spectrogram(y, fs, nperseg=window)
            fig2, ax2 = plt.subplots()
            ax2.pcolormesh(t_spec, f_spec, 10*np.log10(Sxx + 1e-10), shading='gouraud')
            ax2.set_ylim(300, max_freq)
            st.pyplot(fig2)

        # AUDIO + DOWNLOAD
        y_norm = y / np.max(np.abs(y))
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        wavfile.write(tmp.name, fs, (y_norm * 32767).astype(np.int16))
        st.audio(tmp.name)
        with open(tmp.name, "rb") as f:
            st.download_button("⬇ Download WAV", f, file_name="whistler.wav")

        # 3D
        if st.button("📊 3D Spectrogram"):
            f_spec, t_spec, Sxx = spectrogram(y, fs, nperseg=window)
            Sxx_db = 10*np.log10(Sxx + 1e-10)
            T, F = np.meshgrid(t_spec, f_spec)
            fig3d = plt.figure()
            ax3d = fig3d.add_subplot(111, projection='3d')
            ax3d.plot_surface(T, F, Sxx_db, cmap='viridis')
            st.pyplot(fig3d)

        # LIVE MODE (animated redraw)
        if live_mode:
            placeholder = st.empty()
            for k in range(10):
                y_live = y + 0.02*np.random.randn(len(y))
                fig_live, ax_live = plt.subplots()
                ax_live.plot(t, y_live)
                ax_live.set_title("Live Signal")
                placeholder.pyplot(fig_live)
                time.sleep(0.2)

# =========================================================
# RESULTS
# =========================================================
with tab3:

    st.markdown("### 🧠 Signal Health")

    if score > 85:
        st.success("High-quality whistler signal")
    elif score > 60:
        st.info("Moderate quality signal")
    else:
        st.error("Low-quality signal — adjust parameters")
        
    if st.session_state.signal is not None:
        y = st.session_state.signal
        fs = st.session_state.fs
        peak = np.max(np.abs(y))
        energy = np.sum(y**2)

        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.markdown("### 📊 Signal Metrics")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="metric">Max Amplitude<br><b>{peak:.3f}</b></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric">Signal Energy<br><b>{energy:.3f}</b></div>', unsafe_allow_html=True)

        st.info("Observation: Dispersion introduces frequency-dependent delay.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Generate or upload a signal first.")
