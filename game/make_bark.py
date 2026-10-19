"""Generate an original rough, double-woof sound; no external samples required."""
import math
from pathlib import Path
import random
import struct
import wave


def build(path):
    rate = 24000
    rng = random.Random(317)
    phase,low,band = 0.,0.,0.
    samples = []
    for i in range(int(rate*.75)):
        t = i/rate
        value = 0.
        for start in (.06,.30):
            u = (t-start)/.18
            if 0<u<1:
                envelope = min(1,u*18)*math.exp(-u*4)*(1-u)**.25
                frequency = 190-85*u+9*math.sin(t*125)
                phase += math.tau*frequency/rate
                rough = rng.uniform(-1,1)
                low += .22*(rough-low)
                band += .055*(low-band)
                voice = sum(math.sin(phase*h)/h**.8 for h in range(1,13))
                value += envelope*(.48*voice+.9*(low-band)+.14*rough)
        samples.append(math.tanh(value*1.8))
    peak = max(abs(v) for v in samples)
    path = Path(path)
    with wave.open(str(path),'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b''.join(struct.pack('<h',int(v/peak*27000)) for v in samples))


if __name__ == '__main__':
    build(Path(__file__).parent/'assets/dog-bark.wav')
