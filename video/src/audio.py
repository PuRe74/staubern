"""Soundtrack für das Staubern-2026-Video: 30 s, 120 BPM, a-Moll, synchron zu scene.html.

Ablauf: 0–4 s ruhiges Intro (Frümsen), ab 4 s Beat, 16–17 s Break mit Wirbel und Riser,
17 s Drop (Bestzeit), 25–30 s ruhiger Abspann mit Schlussakkord.
Nur numpy. Aufruf: python3 audio.py out.wav"""
import sys, wave
import numpy as np

SR = 44100
DUR = 30.0
BEAT = 0.5           # 120 BPM
OFF = 4.0            # Szenen 1–5 beginnen 4 s nach Videostart
N = int(SR * DUR)
rng = np.random.default_rng(7)
L = np.zeros(N); R = np.zeros(N)

def midi(n): return 440.0 * 2 ** ((n - 69) / 12)
def env_adsr(n, a, d, s, r, sus_len):
    a, d, r = int(a*SR), int(d*SR), int(r*SR)
    sl = max(0, int(sus_len*SR) - a - d)
    e = np.concatenate([np.linspace(0, 1, max(a,1)), np.linspace(1, s, max(d,1)), np.full(sl, s), np.linspace(s, 0, max(r,1))])
    return e[:n] if len(e) >= n else np.pad(e, (0, n-len(e)))
def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1/SR); g = np.ones_like(f)
    if lo: g *= 1/np.sqrt(1+(lo/np.maximum(f,1e-3))**4)
    if hi: g *= 1/np.sqrt(1+(f/hi)**4)
    return np.fft.irfft(X*g, len(x))
def saw(freq, n, detune=0.0):
    t = np.arange(n)/SR; out = np.zeros(n)
    for d in (-detune, 0, detune):
        ph = (t*freq*(1+d)) % 1.0; out += 2*ph-1
    return out/3
def add(sig, t0, gl=1.0, gr=None):
    gr = gl if gr is None else gr
    i = int(t0*SR); j = min(N, i+len(sig))
    if i >= N or j <= i: return
    L[i:j] += sig[:j-i]*gl; R[i:j] += sig[:j-i]*gr

# Akkorde je Takt (2 s)
CH = {"Am":[57,60,64], "F":[53,57,60], "C":[48,55,60,64], "G":[55,59,62], "Em":[52,55,59], "Dm":[50,53,57]}
ROOT = {"Am":45,"F":41,"C":48,"G":43,"Em":40,"Dm":38}
PROG = ["Am","F",                                         # Intro
        "Am","F","C","G","Am","F","Dm","Em","Am","F",     # Hauptteil (4–24 s)
        "C","G","Am"]                                     # Abspann
BREAK = (16.0, 17.0)                                      # vor dem Drop
in_break = lambda t: BREAK[0] <= t < BREAK[1]
beats = [b*BEAT for b in range(int(DUR/BEAT))]

# Kick: ab 5 s bis 28 s, im Abspann leiser
kicks = [(t, 1.0 if t < 25 else 0.55) for t in beats if 5.0 <= t < 28.0 and not in_break(t)]
duck = np.ones(N)
for k, v in kicks:
    i = int(k*SR); n = int(0.28*SR); j = min(N, i+n)
    duck[i:j] = np.minimum(duck[i:j], 1 - v*0.65*(1 - np.linspace(0,1,j-i)**0.7))

# Pad
pad = np.zeros(N)
for bar, ch in enumerate(PROG):
    n = int((3.2 if bar == len(PROG)-1 else 2.3)*SR); t0 = bar*2.0
    s = sum(saw(midi(m), n, 0.004) for m in CH[ch]) * env_adsr(n, .25, .4, .8, .9 if bar == len(PROG)-1 else .5, n/SR-.5)
    s = fft_filter(s, hi=1100 if bar < 2 else 1400 if bar != 8 else 2200)
    i = int(t0*SR); j = min(N, i+n); pad[i:j] += s[:j-i]
pad[:int(4.0*SR)] *= 1.7                                  # Intro etwas präsenter
L += pad*0.10*duck; R += np.roll(pad, 400)*0.10*duck

# Bass (Achtel) 5–28 s
for t0b in beats:
    if not (5.0 <= t0b < 28.0) or in_break(t0b): continue
    ch = PROG[int(t0b//2)]
    for half in (0, 1):
        t0 = t0b + half*BEAT/2; n = int(0.22*SR); f = midi(ROOT[ch]); tt = np.arange(n)/SR
        s = (np.sin(2*np.pi*f*tt) + 0.2*np.sign(np.sin(2*np.pi*f*tt))) * np.exp(-tt*9)
        add(fft_filter(s, hi=500)*(0.22 if t0b < 25 else 0.14), t0)

# Arpeggio (Sechzehntel, Pluck)
pattern = [0,1,2,1,0,2,1,2]
for st in range(int(DUR/(BEAT/4))):
    t0 = st*BEAT/4
    if t0 < 0.5 or t0 >= 28.0 or in_break(t0): continue
    ch = CH[PROG[int(t0//2)]]
    note = ch[pattern[st % 8] % len(ch)] + 12 + (12 if (st//8) % 4 == 3 else 0)
    n = int(0.18*SR); tt = np.arange(n)/SR; f = midi(note)
    s = (np.sign(np.sin(2*np.pi*f*tt))*0.5 + np.sin(2*np.pi*2*f*tt)*0.3) * np.exp(-tt*22)
    pan = 0.5 + 0.35*np.sin(st*0.7)
    vol = 0.03 + 0.015*(t0/4) if t0 < 4 else 0.06 if t0 < 25 else 0.045
    add(s*vol, t0, (1-pan)*1.4, pan*1.4)

# Drums
def kick():
    n = int(0.35*SR); tt = np.arange(n)/SR
    f = 45 + 110*np.exp(-tt*30); ph = 2*np.pi*np.cumsum(f)/SR
    return np.sin(ph)*np.exp(-tt*9)
def clap(len_s=0.2):
    n = int(len_s*SR); tt = np.arange(n)/SR
    nz = fft_filter(rng.standard_normal(n), lo=900, hi=6000)
    e = np.exp(-tt*22) * (1 + 0.6*(np.sin(2*np.pi*90*tt) > 0.6))
    return nz*e*0.6/np.max(np.abs(nz))
def hat(open_=False):
    n = int((0.12 if open_ else 0.04)*SR); tt = np.arange(n)/SR
    nz = fft_filter(rng.standard_normal(n), lo=7000)
    return nz/np.max(np.abs(nz))*np.exp(-tt*(25 if open_ else 90))
K = kick()
for k, v in kicks: add(K*0.55*v, k)
for b, t0 in enumerate(beats):
    if in_break(t0): continue
    if 5.0 <= t0 < 25.0 and b % 2 == 1: add(clap()*0.32, t0, 0.9, 1.0)
    if 2.0 <= t0 < 28.0: add(hat()*(0.05 if t0 < 4 else 0.10), t0+BEAT/2, 0.7, 1.0)
    if 17.0 <= t0 < 25.0: add(hat()*0.06, t0+BEAT/4, 1.0, 0.7); add(hat()*0.06, t0+3*BEAT/4, 1.0, 0.7)
# Wirbel vor dem Drop und kleiner Aufbau vor dem Titel
for i in range(16): add(clap(0.08)*(0.08+0.22*i/15), BREAK[0] + i/16)
for i in range(8):  add(clap(0.06)*(0.04+0.10*i/7), 3.5 + i/16)

# --- Effekte ---
def whoosh(t0, length=0.6, vol=0.25):
    n = int(length*SR); tt = np.linspace(0,1,n)
    nz = rng.standard_normal(n); out = np.zeros(n); seg = 2048
    for s0 in range(0, n, seg):
        x = tt[s0]; out[s0:s0+seg] = fft_filter(nz[s0:s0+seg], lo=300+3500*x, hi=1200+7000*x)
    add(out*np.sin(np.pi*tt)**2*vol, t0, 0.8, 1.0)
whoosh(0.3, 0.9, 0.10)
for ts in (3.75, 7.35, 11.75, 20.75, 24.75): whoosh(ts, 0.5, 0.18)

def tick(t0, f=2400, vol=0.05):
    n = int(0.03*SR); tt = np.arange(n)/SR
    add(np.sin(2*np.pi*f*tt)*np.exp(-tt*180)*vol, t0)
def inv_eout(v): return 1 - (1 - v) ** (1/3)
for k in range(1, 24): tick(OFF + 3.8 + 1.2*inv_eout(k/23), 1800 + k*40, 0.06)       # Aufstiege
for k in range(1, 29): tick(OFF + 5.0 + 1.3*inv_eout(k/28), 2600, 0.035)             # Höhenmeter
for i in range(4):                                                                    # Everest
    n = int(0.15*SR); tt = np.arange(n)/SR
    add(np.sin(2*np.pi*midi(69+[0,3,7,12][i])*tt)*np.exp(-tt*25)*0.08, OFF + 6.4 + i*0.12)

def inv_eio(v):
    lo, hi = 0.0, 1.0
    for _ in range(40):
        m = (lo+hi)/2; y = 4*m**3 if m < .5 else 1-(-2*m+2)**3/2
        lo, hi = (m, hi) if y < v else (lo, m)
    return lo
SCALE = [69,72,74,76,79,81,84,86,88]
for i in range(23):                                                                   # Chart-Punkte
    n = int(0.25*SR); tt = np.arange(n)/SR; f = midi(SCALE[min(len(SCALE)-1, i*len(SCALE)//23)])
    s = (np.sin(2*np.pi*f*tt) + 0.3*np.sin(2*np.pi*3*f*tt)) * np.exp(-tt*14)
    add(s*0.05, OFF + 8.4 + 3.2*inv_eio((i+0.0001)/23), 1.0 - i/30, 0.4 + i/30)

# Riser und Impact (Bestzeit bei 17 s)
n = int(1.3*SR); tt = np.arange(n)/SR
ph = 2*np.pi*np.cumsum(200*2**(tt/1.3*3))/SR
add((np.sin(ph)*0.5 + fft_filter(rng.standard_normal(n), lo=2000)*0.25) * (tt/1.3)**2 * 0.18, BREAK[1]-1.3)
n = int(1.6*SR); tt = np.arange(n)/SR
boom = np.sin(2*np.pi*np.cumsum(30+60*np.exp(-tt*8))/SR)*np.exp(-tt*2.5)
crash = fft_filter(rng.standard_normal(n), lo=3000)*np.exp(-tt*2.2)*0.25
add((boom*0.7 + crash)*0.55, BREAK[1], 1.0, 0.95)
for i in range(4):                                                                    # Kacheln
    n = int(0.5*SR); tt = np.arange(n)/SR; f = midi(76 + [0, 3, 7, 12][i])
    add((np.sin(2*np.pi*f*tt) + 0.4*np.sin(2*np.pi*2.01*f*tt))*np.exp(-tt*7)*0.05, OFF + 14.0 + i*0.5)
# Gipfelflagge
n = int(1.2*SR); tt = np.arange(n)/SR
add(sum(np.sin(2*np.pi*midi(m)*tt) for m in (69, 72, 76))*np.exp(-tt*3)*0.04, OFF + 18.4, 0.95, 1.0)
# Schlussakkord
n = int(2.2*SR); tt = np.arange(n)/SR
fin = sum(np.sin(2*np.pi*midi(m)*tt) for m in (45, 57, 64, 69, 72, 76)) * np.exp(-tt*1.3)
add(fin*0.06, 28.0, 0.95, 1.0); add(K*0.45, 28.0)

# Master
mix = np.stack([L, R], 1)
mix[:int(0.05*SR)] *= np.linspace(0, 1, int(0.05*SR))[:, None]
fade = int(0.9*SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]**1.5
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
mix *= 0.89 / np.max(np.abs(mix))
pcm = (mix * 32767).astype("<i2")
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok", sys.argv[1])
