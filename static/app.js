/* Brand mark: 5×5 grid pulse */
(function(){
  const SVG = 'http://www.w3.org/2000/svg';
  function makeGrid(g) {
    if (!g) return;
    g.innerHTML = '';
    for (let r = 0; r < 5; r++) {
      for (let c = 0; c < 5; c++) {
        const x = 18 + c * 33.5;
        const y = 18 + r * 33.5;
        const delay = ((r + c) * 0.15).toFixed(2) + 's';
        const dot = document.createElementNS(SVG, 'circle');
        dot.setAttribute('cx', x);
        dot.setAttribute('cy', y);
        dot.setAttribute('r', '2');
        dot.setAttribute('fill', '#fff');
        const aR = document.createElementNS(SVG, 'animate');
        aR.setAttribute('attributeName', 'r');
        aR.setAttribute('values', '1.2;5;1.2');
        aR.setAttribute('dur', '2.5s');
        aR.setAttribute('begin', delay);
        aR.setAttribute('repeatCount', 'indefinite');
        const aO = document.createElementNS(SVG, 'animate');
        aO.setAttribute('attributeName', 'opacity');
        aO.setAttribute('values', '.3;1;.3');
        aO.setAttribute('dur', '2.5s');
        aO.setAttribute('begin', delay);
        aO.setAttribute('repeatCount', 'indefinite');
        dot.appendChild(aR);
        dot.appendChild(aO);
        g.appendChild(dot);
      }
    }
  }
  makeGrid(document.getElementById('grid-pulse-small'));
})();

let pollTimer = null;
let currentJobId = null;
const CPS = 14;
const clientSessionId = Math.random().toString(36).substring(2, 15);

function toggleHelpMode() {
  document.body.classList.toggle('help-active');
  const btn = document.getElementById('help-toggle-btn');
  if (btn) {
    const active = document.body.classList.contains('help-active');
    btn.textContent = active ? 'Help Active' : 'Help';
    btn.classList.toggle('active', active);
  }
}

function detectLang(t) {
  const lo = t.toLowerCase();
  const lat = (lo.match(/[a-z]/g)||[]).length;
  const cyr = (lo.match(/[\u0400-\u04FF]/g)||[]).length;
  if (lat > cyr && lat > 0) return 'en';
  
  const uk_m = (lo.match(/[їієґ]/g)||[]).length;
  const ru_m = (lo.match(/[ыъэё]/g)||[]).length;
  
  if (uk_m > ru_m) return 'uk';
  if (ru_m > uk_m) return 'ru';
  
  // Ambiguous
  if (lo.includes('и') && !lo.includes('і')) return 'ru';
  if (lo.includes('і') && !lo.includes('и')) return 'uk';
  
  return 'ru';
}

function getSegments(text, forcedLang) {
  const parts = text.trim().split(/(?<=[.!?\n])\s+|\n+/).filter(s=>s.trim());
  const segs = [];
  parts.forEach(s => {
    const lang = (forcedLang && forcedLang !== 'auto') ? forcedLang : detectLang(s);
    if (segs.length && segs[segs.length-1].lang === lang) segs[segs.length-1].t += ' '+s;
    else segs.push({lang, t:s});
  });
  return segs;
}

const LL = {uk:'UK · UKR', ru:'RU · RUS', en:'EN · ENG'};
const CC = {uk:'chip-uk', ru:'chip-ru', en:'chip-en'};

function onInput(id) {
  const text = document.getElementById('text-'+id).value;
  const forced = document.getElementById('lang-'+id).value;
  
  const words = text.trim() ? text.trim().split(/\s+/).filter(w => w.length > 0).length : 0;
  const chars = text.length;
  document.getElementById('count-'+id).textContent = `${chars} characters · ${words} words`;

  const speedMinEl = document.getElementById('speed-min');
  const speedMin = speedMinEl ? parseFloat(speedMinEl.value) : 3.0;
  const silStartEl = document.getElementById('sil-start');
  const silEndEl = document.getElementById('sil-end');
  const fades = (silStartEl ? parseFloat(silStartEl.value) : 1.5) + (silEndEl ? parseFloat(silEndEl.value) : 1.5);

  let estDurSec = 0;
  let estMp3Mb = "0.0";
  let estWavMb = "0.0";
  let formattedTime = "0s";

  if (chars > 0) {
    const segs = text.trim() ? getSegments(text, forced) : [];
    let baseSpeechSec = 0;
    if (segs.length > 0) {
      segs.forEach(s => {
        const cps = s.lang === 'en' ? 14.5 : 10.2;
        baseSpeechSec += s.t.length / cps;
      });
    } else {
      baseSpeechSec = chars / 10.5;
    }
    
    estDurSec = Math.max(2, Math.round((baseSpeechSec / speedMin) + fades));
    
    const mins = Math.floor(estDurSec / 60);
    const secs = estDurSec % 60;
    formattedTime = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;

    // MP3 320 kbps: 40 KB/s
    estMp3Mb = (estDurSec * 40 / 1024).toFixed(1);
    // WAV 44.1kHz 16-bit Stereo: 172.266 KB/s
    estWavMb = (estDurSec * 172.266 / 1024).toFixed(1);
  }

  const durEl = document.getElementById('dur-'+id);
  if (durEl) {
    durEl.textContent = estDurSec > 0 
      ? `Est. Duration: ~${formattedTime} (${estDurSec}s) · MP3: ~${estMp3Mb} MB · WAV: ~${estWavMb} MB` 
      : '—';
  }
  
  const preview = document.getElementById('preview-'+id);
  if (!preview) return;
  const segs = text.trim() ? getSegments(text, forced) : [];
  preview.innerHTML = segs.map(s => `<span class="chip ${CC[s.lang]}">${LL[s.lang]}</span>`).join('');
}

function sync(el, lbl, sfx='') {
  document.getElementById(lbl).textContent = el.value + sfx;
  const pct = (el.value - el.min) / (el.max - el.min) * 100;
  el.style.setProperty('--pct', pct + '%');
}

async function loadMusicTracks() {
  const sel = document.getElementById('music-type');
  try {
    const tracks = await fetch('/music_tracks').then(r => r.json());
    sel.innerHTML = '<option value="none">— Disabled</option>';
    if (tracks.length === 0) {
      const opt = document.createElement('option');
      opt.disabled = true;
      opt.textContent = '— No audio files in engine/music/';
      sel.appendChild(opt);
    } else {
      tracks.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = t.label;
        sel.appendChild(opt);
      });
    }
  } catch(e) {
    console.warn('Could not load music tracks:', e);
  }
}
loadMusicTracks();

/* ==========================================
   TOP LOADER VISUALIZER LOGIC (LIQUID FLOW)
   ========================================== */

// Set controls on load
document.addEventListener('DOMContentLoaded', () => {
  // Initialize path geometry for the Liquid Flow loader
  const SVG = 'http://www.w3.org/2000/svg';
  const base = document.getElementById('lfBase');
  const fill = document.getElementById('lfFillG');
  if (base && fill) {
    base.innerHTML = '';
    fill.innerHTML = '';
    const N = 18;
    for (let i = 0; i < N; i++) {
      const y = 6 + i * (76 / (N - 1));
      const d = `M-40 ${y} L 1040 ${y}`;
      const p1 = document.createElementNS(SVG, 'path');
      p1.setAttribute('d', d);
      base.appendChild(p1);
      
      const p2 = document.createElementNS(SVG, 'path');
      p2.setAttribute('d', d);
      fill.appendChild(p2);
    }
  }
  // Load saved path and filename from localStorage
  const savedDir = localStorage.getItem('ncs_export_dir');
  if (savedDir) {
    const dirInput = document.getElementById('export-dir');
    if (dirInput) dirInput.value = savedDir;
  }
  const savedName = localStorage.getItem('ncs_export_filename');
  if (savedName) {
    const nameInput = document.getElementById('export-filename');
    if (nameInput) nameInput.value = savedName;
  }
  const savedAutosaveEnc = localStorage.getItem('ncs_export_autosave_encoded');
  if (savedAutosaveEnc !== null) {
    const autosaveEncInput = document.getElementById('export-autosave-encoded');
    if (autosaveEncInput) autosaveEncInput.checked = (savedAutosaveEnc === 'true');
  }
  const savedAutosaveRaw = localStorage.getItem('ncs_export_autosave_raw');
  if (savedAutosaveRaw !== null) {
    const autosaveRawInput = document.getElementById('export-autosave-raw');
    if (autosaveRawInput) autosaveRawInput.checked = (savedAutosaveRaw === 'true');
  }
  const savedSound = localStorage.getItem('ncs_export_sound');
  if (savedSound !== null) {
    const soundInput = document.getElementById('export-sound');
    if (soundInput) soundInput.checked = (savedSound === 'true');
  }
  const savedVoiceVol = localStorage.getItem('ncs_voice_volume');
  if (savedVoiceVol !== null) {
    const voiceVolInput = document.getElementById('voice-volume');
    if (voiceVolInput) voiceVolInput.value = savedVoiceVol;
  }

  // Save to localStorage on input modification
  const dirInputEl = document.getElementById('export-dir');
  if (dirInputEl) {
    dirInputEl.addEventListener('input', (e) => {
      localStorage.setItem('ncs_export_dir', e.target.value);
    });
  }
  const nameInputEl = document.getElementById('export-filename');
  if (nameInputEl) {
    nameInputEl.addEventListener('input', (e) => {
      localStorage.setItem('ncs_export_filename', e.target.value);
    });
  }
  const autosaveEncEl = document.getElementById('export-autosave-encoded');
  if (autosaveEncEl) {
    autosaveEncEl.addEventListener('change', (e) => {
      localStorage.setItem('ncs_export_autosave_encoded', e.target.checked);
    });
  }
  const autosaveRawEl = document.getElementById('export-autosave-raw');
  if (autosaveRawEl) {
    autosaveRawEl.addEventListener('change', (e) => {
      localStorage.setItem('ncs_export_autosave_raw', e.target.checked);
    });
  }
  const soundEl = document.getElementById('export-sound');
  if (soundEl) {
    soundEl.addEventListener('change', (e) => {
      localStorage.setItem('ncs_export_sound', e.target.checked);
    });
  }
  const voiceVolEl = document.getElementById('voice-volume');
  if (voiceVolEl) {
    voiceVolEl.addEventListener('input', (e) => {
      localStorage.setItem('ncs_voice_volume', e.target.value);
    });
  }

  const tgEnabled = document.getElementById('tg-enabled');
  if (tgEnabled) {
    tgEnabled.addEventListener('change', () => {
      toggleTgFields();
      saveTelegramConfig();
    });
  }
  const tgToken = document.getElementById('tg-token');
  if (tgToken) {
    tgToken.addEventListener('input', saveTelegramConfig);
  }
  const tgChatId = document.getElementById('tg-chat-id');
  if (tgChatId) {
    tgChatId.addEventListener('input', saveTelegramConfig);
  }

  loadTelegramConfig();
  updateLoaderVisibility();
  renderActiveLoader(0, 'STANDBY');

  setTimeout(() => {
    if (window.pywebview) {
      const browseBtn = document.getElementById('btn-browse-folder');
      if (browseBtn) {
        browseBtn.style.display = 'inline-block';
      }
    }
  }, 300);
});

async function browseFolder() {
  if (window.pywebview && window.pywebview.api) {
    try {
      const folder = await window.pywebview.api.choose_folder();
      if (folder) {
        document.getElementById('export-dir').value = folder;
        localStorage.setItem('ncs_export_dir', folder);
      }
    } catch (e) {
      console.error("Error browsing folder:", e);
    }
  }
}

function updateLoaderVisibility() {
  const container = document.getElementById('top-loader-container');
  if (container) {
    container.style.setProperty('display', 'block', 'important');
  }
}

function renderActiveLoader(pct, stage) {
  const fillEl = document.getElementById('lfFill');
  if (fillEl) {
    fillEl.style.width = pct + '%';
  }
  
  const shell = document.getElementById('top-loader');
  if (shell) {
    shell.style.setProperty('--lf-pct', pct + '%');
  }

  const pctLabel = document.getElementById('loader-pct-label');
  if (pctLabel) {
    pctLabel.textContent = `${Math.round(pct)}/100`;
  }
  
  const stageLabel = document.getElementById('loader-stage-label');
  if (stageLabel) {
    stageLabel.textContent = `${stage.toUpperCase()} · 44.1 kHz / 16-bit / Stereo`;
  }
}

/* Sync properties */
['layers','speed-min','speed-max','sil-start','sil-end','binaural-volume','music-volume','voice-volume'].forEach(id => {
  const el = document.getElementById(id);
  if(el) el.style.setProperty('--pct', ((el.value-el.min)/(el.max-el.min)*100)+'%');
});

const BINAURAL_FREQS = {
  turbo_manipura: { l: '126/330/528', r: '129/336/538', label: 'Turbo-Manipura (3/6/10 Hz)' },
  delta: { l: 136.1, r: 138.1, label: 'Delta (2 Hz)' },
  theta: { l: 136.1, r: 140.1, label: 'Theta (4 Hz)' },
  alpha: { l: 136.1, r: 146.1, label: 'Alpha (10 Hz)' },
  beta:  { l: 136.1, r: 151.1, label: 'Beta (15 Hz)' },
};

function updateNotchDesc() {
  const type = document.getElementById('binaural-type').value;
  const desc = document.getElementById('notch-desc');
  const toggle = document.getElementById('notch-toggle');
  if (toggle) {
    toggle.checked = (type !== 'none');
  }
  if (!desc) return;
  if (type === 'none' || !BINAURAL_FREQS[type]) {
    desc.innerHTML = 'Carves out active binaural carrier frequencies from the background track to prevent acoustic masking. <em>Select a binaural beat to see target frequencies.</em>';
  } else {
    const f = BINAURAL_FREQS[type];
    desc.innerHTML = `Notch EQ for <strong>${f.label}</strong>: notches out <strong>${f.l} Hz</strong> (L) and <strong>${f.r} Hz</strong> (R) from the background music. Q=30 (~4–5 Hz notch width). Active only when binaural + music.`;
  }
}

updateNotchDesc();
document.getElementById('binaural-type').addEventListener('change', updateNotchDesc);

async function generate() {
  const main = document.getElementById('text-main').value.trim();
  if (!main) { alert('Affirmation text is required'); return; }

  const exportDirInput = document.getElementById('export-dir');
  const exportDir = exportDirInput ? exportDirInput.value.trim() : '';
  if (!exportDir) {
    alert('Please specify the Output (Export Directory) folder.');
    if (exportDirInput) exportDirInput.focus();
    return;
  }

  const autosaveEncoded = document.getElementById('export-autosave-encoded').checked;
  const autosaveRaw = document.getElementById('export-autosave-raw').checked;

  if (!autosaveEncoded && !autosaveRaw) {
    alert('Please check at least one save option (Auto-save encoded WAV or Auto-save raw voice).');
    return;
  }

  const btn = document.getElementById('btn-gen');
  btn.disabled = true; btn.innerHTML = '<span>Processing...</span>';
  document.getElementById('prog-wrap').style.display = 'block';
  const successWrap = document.getElementById('success-wrap');
  if (successWrap) successWrap.style.display = 'none';
  const tgWrap = document.getElementById('tg-upload-wrap');
  if (tgWrap) tgWrap.style.display = 'none';
  document.getElementById('err-txt').style.display = 'none';
  setProgress(5, 'Sending request...');

  const fd = new FormData();
  fd.append('client_session_id', clientSessionId);
  fd.append('text_main',   main);
  fd.append('voice_uk',    document.getElementById('voice-uk').value);
  fd.append('voice_ru',    document.getElementById('voice-ru').value);
  fd.append('voice_en',    document.getElementById('voice-en').value);
  fd.append('lang_main',     document.getElementById('lang-main').value);
  fd.append('layers',        document.getElementById('layers').value);
  fd.append('speed_min',     document.getElementById('speed-min').value);
  fd.append('speed_max',     document.getElementById('speed-max').value);
  fd.append('silence_start', document.getElementById('sil-start').value);
  fd.append('silence_end',   document.getElementById('sil-end').value);
  fd.append('binaural_type',    document.getElementById('binaural-type').value);
  fd.append('binaural_volume',  document.getElementById('binaural-volume').value);
  fd.append('music_type',       document.getElementById('music-type').value);
  fd.append('music_volume',     document.getElementById('music-volume').value);
  fd.append('music_notch_enabled', document.getElementById('notch-toggle').checked ? 'true' : 'false');
  const autosaveFlac = document.getElementById('export-autosave-flac') ? document.getElementById('export-autosave-flac').checked : false;
  fd.append('export_filename', document.getElementById('export-filename').value.trim());
  fd.append('export_dir',      exportDir);
  fd.append('save_encoded',    autosaveEncoded ? 'true' : 'false');
  fd.append('save_flac',       autosaveFlac ? 'true' : 'false');
  fd.append('save_raw',        autosaveRaw ? 'true' : 'false');
  fd.append('tg_enabled',      document.getElementById('tg-enabled').checked ? 'true' : 'false');
  fd.append('tg_token',        document.getElementById('tg-token').value.trim());
  fd.append('tg_chat_id',      document.getElementById('tg-chat-id').value.trim());

  try {
    const response = await fetch('/generate', {method:'POST', body:fd});
    const payload = await response.json();
    if (!response.ok) {
      const detail = Array.isArray(payload.detail)
        ? payload.detail.join('\n')
        : (payload.detail || `Request failed (${response.status})`);
      throw new Error(detail);
    }
    const {job_id} = payload;
    currentJobId = job_id;
    const cancelBtn = document.getElementById('btn-cancel');
    if (cancelBtn) {
      cancelBtn.disabled = false;
      cancelBtn.textContent = 'Cancel';
      cancelBtn.style.display = 'inline-block';
    }
    pollStatus(job_id);
  } catch(e) { showError('Error: '+e.message); resetBtn(); }
}

function playBellSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const now = ctx.currentTime;
    
    // Tone 1 (High bell sound)
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(880, now); // A5
    osc1.frequency.exponentialRampToValueAtTime(1760, now + 0.08); // Quick slide up
    gain1.gain.setValueAtTime(0.25, now);
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 1.2);
    
    osc1.connect(gain1);
    gain1.connect(ctx.destination);
    
    // Tone 2 (Perfect harmony - E6)
    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.type = 'sine';
    osc2.frequency.setValueAtTime(1318.51, now); 
    gain2.gain.setValueAtTime(0.12, now);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 1.6);
    
    osc2.connect(gain2);
    gain2.connect(ctx.destination);
    
    osc1.start(now);
    osc2.start(now);
    
    osc1.stop(now + 1.8);
    osc2.stop(now + 1.8);
  } catch (e) {
    console.error("Audio playback error:", e);
  }
}

let cancellingPollCount = 0;
function pollStatus(job_id) {
  clearInterval(pollTimer);
  cancellingPollCount = 0;
  pollTimer = setInterval(async () => {
    try {
      const d = await fetch('/status/'+job_id).then(r=>r.json());
      
      // Update real-time log ticker
      if (d.logs && d.logs.length > 0) {
        const latestLog = d.logs[d.logs.length - 1];
        const ticker = document.getElementById('loader-ticker-label');
        if (ticker) {
          ticker.textContent = latestLog;
        }
        updateTelegramUploadProgress(d.logs);
      }
      
      if (d.status === 'queued') {
        setProgress(0, 'Queued — waiting for the active generation...');
      } else if (d.status === 'cancelling') {
        cancellingPollCount++;
        if (cancellingPollCount >= 3) {
          clearInterval(pollTimer);
          showError('Generation cancelled.');
          resetBtn();
        } else {
          setProgress(d.progress || 0, 'Cancelling safely...');
        }
      } else if (d.status === 'processing') {
        const p = d.progress || 5;
        const msg = p < 25 ? 'Generating TTS...'
          : p < 90 ? `AM encoding layers... ${p}%`
          : 'Normalizing and writing audio...';
        setProgress(p, msg);
      } else if (d.status === 'done') {
        clearInterval(pollTimer);
        setProgress(100, 'Done.');
        const ticker = document.getElementById('loader-ticker-label');
        if (ticker) ticker.textContent = 'Generation finished successfully.';
        
        // Play notification chime if enabled
        const soundEnabled = document.getElementById('export-sound') ? document.getElementById('export-sound').checked : true;
        if (soundEnabled) {
          playBellSound();
        }
        
        setTimeout(() => showDownload(job_id), 400);
        resetBtn();
      } else if (d.status === 'error') {
        clearInterval(pollTimer);
        showError('Error: ' + (d.error||'unknown'));
        resetBtn();
      } else if (d.status === 'cancelled') {
        clearInterval(pollTimer);
        showError('Generation cancelled.');
        resetBtn();
      }
    } catch {}
  }, 800);
}

function setProgress(pct, msg) {
  const fill = document.getElementById('prog-fill');
  if (fill) fill.style.width = pct+'%';
  const pctText = document.getElementById('prog-pct');
  if (pctText) pctText.textContent = pct+'%';
  const txt = document.getElementById('status-txt');
  if (txt) txt.textContent = msg;
  
  // Render visualizer
  renderActiveLoader(pct, msg);
}
async function showDownload(job_id) {
  try {
    const d = await fetch('/status/'+job_id).then(r=>r.json());
    const encodedPath = d.output_path || '-';
    const rawPath = d.output_raw_path || '-';
    const autosaveEncoded = document.getElementById('export-autosave-encoded').checked;
    const autosaveRaw = document.getElementById('export-autosave-raw').checked;
    
    const flacPath = d.output_flac_path || '-';
    const autosaveFlac = document.getElementById('export-autosave-flac') ? document.getElementById('export-autosave-flac').checked : false;

    const encodedEl = document.getElementById('success-path-encoded');
    if (encodedEl) {
      if (autosaveEncoded) {
        encodedEl.style.display = 'block';
        encodedEl.textContent = `Encoded MP3: ${encodedPath}`;
      } else {
        encodedEl.style.display = 'none';
      }
    }

    const flacEl = document.getElementById('success-path-flac');
    if (flacEl) {
      if (autosaveFlac && flacPath !== '-') {
        flacEl.style.display = 'block';
        flacEl.textContent = `Lossless FLAC: ${flacPath}`;
      } else {
        flacEl.style.display = 'none';
      }
    }

    const rawEl = document.getElementById('success-path-raw');
    if (rawEl) {
      if (autosaveRaw) {
        rawEl.style.display = 'block';
        rawEl.textContent = `Raw: ${rawPath}`;
      } else {
        rawEl.style.display = 'none';
      }
    }

    
    const w = document.getElementById('success-wrap');
    if (w) {
      w.style.display = 'block';
      w.scrollIntoView({behavior:'smooth'});
    }

    const tgEnabled = document.getElementById('tg-enabled') ? document.getElementById('tg-enabled').checked : true;
    if (tgEnabled && encodedPath && encodedPath !== '-') {
      const fd = new FormData();
      fd.append('file_path', encodedPath);
      fd.append('username', 'ricardo_la_retardo');
      fetch('/open_in_telegram', { method: 'POST', body: fd })
        .then(r => r.json())
        .then(res => {
          const tgWrap = document.getElementById('tg-upload-wrap');
          const tgStatusText = document.getElementById('tg-upload-status-text');
          const tgBadge = document.getElementById('tg-upload-badge');
          const tgFill = document.getElementById('tg-upload-fill');
          if (tgWrap && tgStatusText && tgBadge && tgFill) {
            tgWrap.style.display = 'block';
            tgStatusText.textContent = '⚡️ Auto-sending file to Telegram Desktop chat @ricardo_la_retardo...';
            tgBadge.textContent = 'AUTO-SENDING';
            tgBadge.style.background = 'rgba(0, 204, 136, 0.15)';
            tgBadge.style.color = '#00cc88';
            tgWrap.style.borderColor = 'rgba(0, 204, 136, 0.25)';
            tgWrap.style.background = 'rgba(0, 204, 136, 0.04)';
            tgFill.classList.remove('tg-upload-animated-bar');
            tgFill.style.width = '100%';
            tgFill.style.background = '#00cc88';
          }
        })
        .catch(err => console.warn('Failed to open in Telegram Desktop:', err));
    }
  } catch (e) {
    console.error("Error displaying success paths:", e);
  }
}
function showError(msg) {
  const el = document.getElementById('err-txt');
  if (el) { el.textContent = msg; el.style.display = 'block'; }
  const wrap = document.getElementById('prog-wrap');
  if (wrap) wrap.style.display = 'none';
  
  renderActiveLoader(0, 'ERROR: ' + msg);
}
function resetBtn() {
  const btn = document.getElementById('btn-gen');
  if (btn) {
    btn.disabled = false;
    btn.innerHTML = '<span>Generate Audio</span>';
  }
  const cancelBtn = document.getElementById('btn-cancel');
  if (cancelBtn) {
    cancelBtn.style.display = 'none';
    cancelBtn.disabled = false;
    cancelBtn.textContent = 'Cancel';
  }
  currentJobId = null;
}

async function cancelGeneration() {
  if (!currentJobId) return;
  const btn = document.getElementById('btn-cancel');
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Cancelling...';
  }
  try {
    const response = await fetch(`/jobs/${currentJobId}/cancel`, {method: 'POST'});
    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.detail || 'Cancellation failed');
    }
  } catch (error) {
    showError('Cancellation error: ' + error.message);
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Cancel';
    }
  }
}

/* ===== Telegram Bot Configuration and Testing ===== */
async function loadTelegramConfig() {
  try {
    const res = await fetch('/telegram_config').then(r => r.json());
    if (res) {
      const enabledEl = document.getElementById('tg-enabled');
      const tokenEl = document.getElementById('tg-token');
      const chatIdEl = document.getElementById('tg-chat-id');
      
      if (enabledEl) enabledEl.checked = res.enabled || false;
      if (tokenEl) {
        tokenEl.value = res.token || '';
        tokenEl.placeholder = 'Enter Telegram Bot Token';
      }
      if (chatIdEl) chatIdEl.value = res.chat_id || '';
      
      toggleTgFields();
    }
  } catch (e) {
    console.warn('Could not load Telegram config from server:', e);
    const savedEnabled = localStorage.getItem('ncs_tg_enabled');
    const savedChatId = localStorage.getItem('ncs_tg_chat_id');
    if (savedEnabled !== null) document.getElementById('tg-enabled').checked = (savedEnabled === 'true');
    if (savedChatId !== null) document.getElementById('tg-chat-id').value = savedChatId;
    toggleTgFields();
  }
}

function saveTelegramConfig() {
  const enabled = document.getElementById('tg-enabled').checked;
  const token = document.getElementById('tg-token').value.trim();
  const chat_id = document.getElementById('tg-chat-id').value.trim();
  
  localStorage.setItem('ncs_tg_enabled', enabled);
  localStorage.setItem('ncs_tg_chat_id', chat_id);
  
  const fd = new FormData();
  fd.append('enabled', enabled ? 'true' : 'false');
  fd.append('token', token);
  fd.append('chat_id', chat_id);
  
  fetch('/telegram_config', { method: 'POST', body: fd }).catch(err => console.warn("Failed to persist TG config:", err));
}

function toggleTgFields() {
  const enabled = document.getElementById('tg-enabled').checked;
  const block = document.getElementById('tg-fields-block');
  if (block) {
    block.style.display = enabled ? 'block' : 'none';
  }
}

async function openTelegramHelper(handle) {
  const allowed = new Set(['BotFather', 'userinfobot']);
  if (!allowed.has(handle)) return;
  const url = `https://t.me/${handle}`;
  if (window.pywebview && window.pywebview.api && window.pywebview.api.open_external) {
    await window.pywebview.api.open_external(url);
  } else {
    window.open(url, '_blank', 'noopener,noreferrer');
  }
}

async function testTelegramConnection() {
  const btn = document.getElementById('btn-tg-test');
  const token = document.getElementById('tg-token').value.trim();
  const chat_id = document.getElementById('tg-chat-id').value.trim();
  
  if (!token || !chat_id) {
    alert('Please enter both Bot Token and Chat ID to run a test.');
    return;
  }
  
  btn.disabled = true;
  btn.textContent = 'Testing...';
  
  const fd = new FormData();
  fd.append('token', token);
  fd.append('chat_id', chat_id);
  
  try {
    const res = await fetch('/telegram_test', { method: 'POST', body: fd }).then(r => r.json());
    if (res.status === 'success') {
      alert('Success! A test message was sent to your Telegram chat.');
      saveTelegramConfig();
    } else {
      alert('Telegram Test Failed:\n' + (res.error || 'Unknown error'));
    }
  } catch (e) {
    alert('Request failed: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Test Send';
  }
}

function updateTelegramUploadProgress(logs) {
  if (!logs || logs.length === 0) return;
  
  const tgWrap = document.getElementById('tg-upload-wrap');
  const tgStatusText = document.getElementById('tg-upload-status-text');
  const tgBadge = document.getElementById('tg-upload-badge');
  const tgFill = document.getElementById('tg-upload-fill');
  
  if (!tgWrap || !tgStatusText || !tgBadge || !tgFill) return;

  const tgLogs = logs.filter(l => l.includes('Telegram') || l.includes('Sending Encoded WAV') || l.includes('Sending Raw Voice'));
  if (tgLogs.length === 0) return;

  tgWrap.style.display = 'block';
  const latest = tgLogs[tgLogs.length - 1];

  if (latest.includes('successfully sent') || latest.includes('Sent to Telegram') || latest.includes('successfully sent to Telegram')) {
    tgStatusText.textContent = '✓ Audio delivered to Telegram Bot!';
    tgBadge.textContent = 'SENT';
    tgBadge.style.background = 'rgba(0, 204, 136, 0.15)';
    tgBadge.style.color = '#00cc88';
    tgWrap.style.borderColor = 'rgba(0, 204, 136, 0.25)';
    tgWrap.style.background = 'rgba(0, 204, 136, 0.04)';
    tgFill.classList.remove('tg-upload-animated-bar');
    tgFill.style.width = '100%';
    tgFill.style.background = '#00cc88';
  } else if (latest.includes('failed') || latest.includes('Error')) {
    tgStatusText.textContent = latest;
    tgBadge.textContent = 'ERROR';
    tgBadge.style.background = 'rgba(255, 68, 68, 0.15)';
    tgBadge.style.color = '#ff4444';
    tgWrap.style.borderColor = 'rgba(255, 68, 68, 0.25)';
    tgWrap.style.background = 'rgba(255, 68, 68, 0.04)';
    tgFill.classList.remove('tg-upload-animated-bar');
    tgFill.style.width = '100%';
    tgFill.style.background = '#ff4444';
  } else {
    tgStatusText.textContent = latest;
    tgBadge.textContent = 'UPLOADING';
    tgBadge.style.background = 'rgba(0, 136, 204, 0.15)';
    tgBadge.style.color = '#0088cc';
    tgWrap.style.borderColor = 'rgba(0, 136, 204, 0.25)';
    tgWrap.style.background = 'rgba(0, 136, 204, 0.04)';
    if (!tgFill.classList.contains('tg-upload-animated-bar')) {
      tgFill.classList.add('tg-upload-animated-bar');
    }
    tgFill.style.background = '#0088cc';
  }
}

/* ===== Top status indicator hook ===== */
(function(){
  const gs = document.getElementById('gen-status');
  const gsState = document.getElementById('gs-state');
  if (!gs || !gsState) return;
  const STATES = {
    idle:       'Ready to generate',
    processing: 'Generating',
    done:       'Ready · files available',
    error:      'Processing error',
  };
  function setState(name, extra){
    gs.dataset.state = name;
    gsState.textContent = (STATES[name] || name) + (extra ? ' · ' + extra : '');
  }
  const fill = document.getElementById('prog-fill');
  const successWrap = document.getElementById('success-wrap');
  const err = document.getElementById('err-txt');
  const btn = document.getElementById('btn-gen');
  if (fill) new MutationObserver(()=>{
    const w = parseFloat(fill.style.width) || 0;
    if (btn && btn.disabled && w < 100) setState('processing', Math.round(w) + '%');
    else if (w >= 100) setState('done');
  }).observe(fill, {attributes:true, attributeFilter:['style']});
  if (successWrap) new MutationObserver(()=>{
    if (successWrap.style.display && successWrap.style.display !== 'none') setState('done');
  }).observe(successWrap, {attributes:true, attributeFilter:['style']});
  if (err) new MutationObserver(()=>{
    if (err.style.display && err.style.display !== 'none') setState('error');
  }).observe(err, {attributes:true, attributeFilter:['style']});
  if (btn) new MutationObserver(()=>{
    if (!btn.disabled && gs.dataset.state === 'processing') setState('idle');
    updateLoaderVisibility();
  }).observe(btn, {attributes:true, attributeFilter:['disabled']});
})();
