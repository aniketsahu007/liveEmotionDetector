/* ═══════════════════════════════════════════════════════════════════════════
   EmotionLens — Client-side Script
   Polls /emotion_data, updates UI, manages particles & history
   ═══════════════════════════════════════════════════════════════════════════ */

const EMOJI_MAP = {
    angry:    '😠',
    disgust:  '🤢',
    fear:     '😨',
    happy:    '😄',
    neutral:  '😐',
    sad:      '😢',
    surprise: '😲'
};

const EMOTION_COLORS = {
    angry:    '#ef4444',
    disgust:  '#84cc16',
    fear:     '#a855f7',
    happy:    '#facc15',
    neutral:  '#94a3b8',
    sad:      '#3b82f6',
    surprise: '#f97316'
};

const ORDERED_EMOTIONS = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise'];

// ── DOM refs ────────────────────────────────────────────────────────────────
const emotionEmoji     = document.getElementById('emotion-emoji');
const emotionLabel     = document.getElementById('emotion-label');
const emotionBadge     = document.getElementById('emotion-badge');
const overlayEmotion   = document.getElementById('overlay-emotion');
const confidenceBars   = document.getElementById('confidence-bars');
const historyList      = document.getElementById('history-list');
const faceStatus       = document.getElementById('face-status');
const faceStatusText   = document.getElementById('face-status-text');
const timestampEl      = document.getElementById('timestamp');
const clearHistoryBtn  = document.getElementById('clear-history');
const particlesEl      = document.getElementById('particles');
const emotionCard      = document.getElementById('emotion-card');

let lastEmotion = null;
let localHistory = [];

// ── Initialise confidence bars ──────────────────────────────────────────────
function initConfidenceBars() {
    confidenceBars.innerHTML = '';
    ORDERED_EMOTIONS.forEach(em => {
        const row = document.createElement('div');
        row.className = 'conf-row';
        row.innerHTML = `
            <span class="conf-label">${em}</span>
            <div class="conf-bar-track">
                <div class="conf-bar-fill ${em}" id="bar-${em}" style="width: 0%"></div>
            </div>
            <span class="conf-value" id="val-${em}">0%</span>
        `;
        confidenceBars.appendChild(row);
    });
}

// ── Spawn background particles ──────────────────────────────────────────────
function spawnParticles(count = 25) {
    for (let i = 0; i < count; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        const size = Math.random() * 4 + 2;
        const left = Math.random() * 100;
        const duration = Math.random() * 15 + 10;
        const delay = Math.random() * 15;
        const colors = ['#8b5cf6', '#ec4899', '#06b6d4', '#facc15', '#22c55e'];
        const color = colors[Math.floor(Math.random() * colors.length)];

        p.style.cssText = `
            width: ${size}px;
            height: ${size}px;
            left: ${left}%;
            background: ${color};
            animation-duration: ${duration}s;
            animation-delay: ${delay}s;
        `;
        particlesEl.appendChild(p);
    }
}

// ── Timestamp updater ───────────────────────────────────────────────────────
function updateTimestamp() {
    const now = new Date();
    timestampEl.textContent = now.toLocaleTimeString('en-GB', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// ── Update UI from emotion data ─────────────────────────────────────────────
function updateUI(data) {
    const { emotion, confidences, history, face_detected } = data;

    // — Face status
    if (face_detected) {
        faceStatus.classList.add('detected');
        faceStatusText.textContent = 'Face detected';
    } else {
        faceStatus.classList.remove('detected');
        faceStatusText.textContent = 'Searching…';
    }

    if (!face_detected) return;

    // — Emotion display
    if (emotion !== lastEmotion) {
        emotionEmoji.textContent = EMOJI_MAP[emotion] || '😐';
        emotionEmoji.style.animation = 'none';
        // trigger reflow
        void emotionEmoji.offsetWidth;
        emotionEmoji.style.animation = 'emoji-entrance 0.5s cubic-bezier(0.34,1.56,0.64,1)';

        emotionLabel.textContent = emotion;
        emotionBadge.textContent = emotion.toUpperCase();
        overlayEmotion.textContent = `${EMOJI_MAP[emotion]}  ${emotion.toUpperCase()}`;

        // Update card border glow
        const glowColor = EMOTION_COLORS[emotion] || '#8b5cf6';
        emotionCard.style.borderColor = glowColor + '40';
        emotionCard.style.boxShadow = `0 8px 32px rgba(0,0,0,0.4), 0 0 20px ${glowColor}25`;

        lastEmotion = emotion;
    }

    // — Confidence bars
    let maxVal = 0;
    let maxEm = '';
    ORDERED_EMOTIONS.forEach(em => {
        const val = confidences[em] || 0;
        if (val > maxVal) { maxVal = val; maxEm = em; }
    });

    ORDERED_EMOTIONS.forEach(em => {
        const val = confidences[em] || 0;
        const bar = document.getElementById(`bar-${em}`);
        const valEl = document.getElementById(`val-${em}`);
        if (bar) bar.style.width = val + '%';
        if (valEl) {
            valEl.textContent = val.toFixed(1) + '%';
            valEl.classList.toggle('highlight', em === maxEm);
        }
    });

    // — History
    if (history && history.length > 0) {
        // Only add new items
        const newItems = history.slice(localHistory.length);
        if (newItems.length > 0 || history.length < localHistory.length) {
            localHistory = history;
            renderHistory();
        }
    }
}

function renderHistory() {
    if (localHistory.length === 0) {
        historyList.innerHTML = '<li class="history-empty">Waiting for detections…</li>';
        return;
    }

    historyList.innerHTML = '';
    // show newest first
    const reversed = [...localHistory].reverse();
    reversed.forEach(entry => {
        const li = document.createElement('li');
        li.className = 'history-item';
        li.innerHTML = `
            <span class="history-emoji">${EMOJI_MAP[entry.emotion] || '😐'}</span>
            <span class="history-label">${entry.emotion}</span>
            <span class="history-time">${entry.time}</span>
        `;
        historyList.appendChild(li);
    });
}

// ── Polling ─────────────────────────────────────────────────────────────────
async function pollEmotionData() {
    try {
        const res = await fetch('/emotion_data');
        if (res.ok) {
            const data = await res.json();
            updateUI(data);
        }
    } catch (err) {
        // silently retry
    }
}

// ── Clear history ───────────────────────────────────────────────────────────
clearHistoryBtn.addEventListener('click', () => {
    localHistory = [];
    renderHistory();
});

// ── Boot ────────────────────────────────────────────────────────────────────
initConfidenceBars();
spawnParticles(25);
updateTimestamp();
setInterval(updateTimestamp, 1000);
setInterval(pollEmotionData, 500);
