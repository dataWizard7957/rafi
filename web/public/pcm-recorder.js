// AudioWorklet: downsample mic audio to 16 kHz 16-bit mono PCM, post ~100 ms chunks.
class PcmRecorder extends AudioWorkletProcessor {
  constructor() {
    super();
    this.ratio = sampleRate / 16000;
    this.buf = [];
    this.acc = 0;
    this.pos = 0;
  }
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (!ch) return true;
    for (let i = 0; i < ch.length; i++) {
      this.acc += ch[i];
      this.pos++;
      if (this.pos >= this.ratio) {
        const v = Math.max(-1, Math.min(1, this.acc / this.pos));
        this.buf.push(v < 0 ? v * 0x8000 : v * 0x7fff);
        this.acc = 0;
        this.pos -= this.ratio;
        if (this.pos < 0) this.pos = 0;
      }
    }
    if (this.buf.length >= 1600) {
      const out = new Int16Array(this.buf);
      this.port.postMessage(out.buffer, [out.buffer]);
      this.buf = [];
    }
    return true;
  }
}
registerProcessor("pcm-recorder", PcmRecorder);
