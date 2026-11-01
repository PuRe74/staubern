"""Soundtrack für das Staubern-2026-Video: 20 s, 120 BPM, a-Moll, synchron zu scene.html.
Nur numpy. Aufruf: python3 audio.py out.wav"""
import sys, wave
import numpy as np

SR = 44100
DUR = 20.0
BEAT = 0.5           # 120 BPM
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

# Akkorde je Takt (2 s): Am F C G | Am F C G | Am(F) ... Schlussakkord
CH = {"Am":[57,60,64], "F":[53,57,60], "C":[48,55,60,64], "G":[55,59,62], "Em":[52,55,59], "Dm":[50,53,57]}
PROG = ["Am","F","C","G","Am","F","Dm","Em","Am","F"]
ROOT = {"Am":45,"F":41,"C":48,"G":43,"Em":40,"Dm":38}

# Ducking-Kurve (Sidechain) aus den Kick-Zeitpunkten
kicks = [b*BEAT for b in range(40) if (b >= 2 and not (24 <= b < 26) and b < 38) ]
duck = np.ones(N)
for k in kicks:
    i = int(k*SR); n = int(0.28*SR); j = min(N, i+n)
    duck[i:j] = np.minimum(duck[i:j], 0.35 + 0.65*np.linspace(0,1,j-i)**0.7)

# Pad
pad = np.zeros(N)
for bar, ch in enumerate(PROG):
    n = int(2.3*SR); t0 = bar*2.0
    if t0 >= DUR: break
    s = sum(saw(midi(m), n, 0.004) for m in CH[ch]) * env_adsr(n, .25, .4, .8, .5, 2.0)
    s = fft_filter(s, hi=1400 if bar not in (6,) else 2200)
    i = int(t0*SR); j = min(N, i+n); pad[i:j] += s[:j-i]
pad[int(18.0*SR):] *= np.linspace(1, 0.0, N-int(18.0*SR))**1.2
L += pad*0.10*duck; R += np.roll(pad, 400)*0.10*duck

# Bass (Achtel, ab Takt 1)
for b in range(4, 38):
    if 24 <= b < 26: continue
    ch = PROG[b//4]
    for half in (0, 1):
        t0 = b*BEAT + half*BEAT/2; n = int(0.22*SR)
        f = midi(ROOT[ch] + (12 if half else 0)*0)
        tt = np.arange(n)/SR
        s = (np.sin(2*np.pi*f*tt) + 0.5*np.sign(np.sin(2*np.pi*f*tt))*0.4) * np.exp(-tt*9)
        add(fft_filter(s, hi=500)*0.22, t0)

# Arpeggio (Sechzehntel, Pluck)
pattern = [0,1,2,1,0,2,1,2]
for st in range(int(DUR/(BEAT/4))):
    t0 = st*BEAT/4
    if t0 < 0.5 or t0 >= 18.0 or 12.0 <= t0 < 13.0: continue
    ch = CH[PROG[int(t0//2)]]
    note = ch[pattern[st % 8] % len(ch)] + 12 + (12 if (st//8) % 4 == 3 else 0)
    n = int(0.18*SR); tt = np.arange(n)/SR; f = midi(note)
    s = (np.sign(np.sin(2*np.pi*f*tt))*0.5 + np.sin(2*np.pi*2*f*tt)*0.3) * np.exp(-tt*22)
    pan = 0.5 + 0.35*np.sin(st*0.7)
    vol = 0.045 if t0 < 3.6 else 0.06
    add(s*vol, t0, (1-pan)*1.4, pan*1.4)

# Drums
def kick():
    n = int(0.35*SR); tt = np.arange(n)/SR
    f = 45 + 110*np.exp(-tt*30); ph = 2*np.pi*np.cumsum(f)/SR
    return np.sin(ph)*np.exp(-tt*9)*1.0
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
for k in kicks: add(K*0.55, k)
for b in range(4, 38):
    if 24 <= b < 26: continue
    if b % 2 == 1: add(clap()*0.32, b*BEAT, 0.9, 1.0)
    add(hat()*0.10, b*BEAT+BEAT/2, 0.7, 1.0)
    if b >= 26: add(hat()*0.06, b*BEAT+BEAT/4, 1.0, 0.7); add(hat()*0.06, b*BEAT+3*BEAT/4, 1.0, 0.7)
# Snare-Wirbel vor dem Drop (12.0–13.0)
for i in range(16):
    t0 = 12.0 + i*(1.0/16)
    add(clap(0.08)*(0.08+0.22*i/15), t0)

# --- Effekte ---
def whoosh(t0, length=0.6, up=True, vol=0.25):
    n = int(length*SR); tt = np.linspace(0,1,n)
    nz = rng.standard_normal(n); out = np.zeros(n); seg = 2048
    for s0 in range(0, n, seg):
        x = tt[s0] if up else 1-tt[s0]
        out[s0:s0+seg] = fft_filter(nz[s0:s0+seg], lo=300+3500*x, hi=1200+7000*x)
    e = np.sin(np.pi*tt)**2
    add(out*e*vol, t0, 0.8, 1.0)
for ts in (3.35, 7.75, 16.75):
    whoosh(ts, 0.5, vol=0.18)
whoosh(0.25, 0.8, vol=0.14)

def tick(t0, f=2400, vol=0.05):
    n = int(0.03*SR); tt = np.arange(n)/SR
    add(np.sin(2*np.pi*f*tt)*np.exp(-tt*180)*vol, t0)
# Zähler Aufstiege: 0→23 (3.8–5.0, easeOutCubic), Höhenmeter (5.0–6.3)
def inv_eout(v): return 1 - (1 - v) ** (1/3)
for k in range(1, 24):
    tick(3.8 + 1.2*inv_eout(k/23), 1800 + k*40, 0.06)
for k in range(1, 29):
    tick(5.0 + 1.3*inv_eout(k/28), 2600, 0.035)
# Everest-Berge ploppen
for i in range(4):
    t0 = 6.4 + i*0.12; n = int(0.15*SR); tt = np.arange(n)/SR
    add(np.sin(2*np.pi*(midi(69+[0,3,7,12][i]))*tt)*np.exp(-tt*25)*0.08, t0)

# Chart-Punkte: Zupfer mit steigender Tonhöhe (8.4–11.6, easeInOut)
def inv_eio(v):
    lo, hi = 0.0, 1.0
    for _ in range(40):
        m = (lo+hi)/2; y = 4*m**3 if m < .5 else 1-(-2*m+2)**3/2
        lo, hi = (m, hi) if y < v else (lo, m)
    return lo
SCALE = [69,72,74,76,79,81,84,86,88]
for i in range(23):
    t0 = 8.4 + 3.2*inv_eio((i+0.0001)/23)
    n = int(0.25*SR); tt = np.arange(n)/SR; f = midi(SCALE[min(len(SCALE)-1, i*len(SCALE)//23)])
    s = (np.sin(2*np.pi*f*tt) + 0.3*np.sin(2*np.pi*3*f*tt)) * np.exp(-tt*14)
    add(s*0.05, t0, 1.0 - i/30, 0.4 + i/30)

# Riser 11.7–13.0
n = int(1.3*SR); tt = np.arange(n)/SR
f = 200*2**(tt/1.3*3); ph = 2*np.pi*np.cumsum(f)/SR
rs = (np.sin(ph) * 0.5 + fft_filter(rng.standard_normal(n), lo=2000)*0.25) * (tt/1.3)**2
add(rs*0.18, 11.7)
# Impact beim Drop 13.0
n = int(1.6*SR); tt = np.arange(n)/SR
boom = np.sin(2*np.pi*np.cumsum(30+60*np.exp(-tt*8))/SR)*np.exp(-tt*2.5)
crash = fft_filter(rng.standard_normal(n), lo=3000)*np.exp(-tt*2.2)*0.25
add((boom*0.7 + crash)*0.55, 13.0, 1.0, 0.95)
# Kacheln 14.0, 14.5, 15.0, 15.5: kurze Glocken
for i, t0 in enumerate((14.0, 14.5, 15.0, 15.5)):
    n = int(0.5*SR); tt = np.arange(n)/SR; f = midi(76 + [0, 3, 7, 12][i])
    add((np.sin(2*np.pi*f*tt) + 0.4*np.sin(2*np.pi*2.01*f*tt))*np.exp(-tt*7)*0.05, t0)
# Schluss: Gipfelflagge 18.4 und Schlussakkord
n = int(1.6*SR); tt = np.arange(n)/SR
fin = sum(np.sin(2*np.pi*midi(m)*tt) for m in (57, 64, 69, 72, 76)) * np.exp(-tt*1.6)
add(fin*0.06, 18.4, 0.95, 1.0)
add(K*0.5, 18.4)

# Master
mix = np.stack([L, R], 1)
mix[:int(0.05*SR)] *= np.linspace(0, 1, int(0.05*SR))[:, None]
fade = int(0.6*SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]**1.5
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
mix *= 0.89 / np.max(np.abs(mix))
pcm = (mix * 32767).astype("<i2")
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok", sys.argv[1])
