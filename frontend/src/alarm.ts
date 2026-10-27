let ctx: AudioContext | null = null;

/** Short two-tone alarm. Browsers only allow audio after the user has interacted with the page. */
export function playAlarm(urgent: boolean) {
  try {
    ctx ??= new AudioContext();
    const tones = urgent ? [880, 660, 880, 660] : [880];
    tones.forEach((freq, i) => {
      const osc = ctx!.createOscillator();
      const gain = ctx!.createGain();
      const start = ctx!.currentTime + i * 0.22;
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.15, start);
      gain.gain.exponentialRampToValueAtTime(0.001, start + 0.2);
      osc.connect(gain).connect(ctx!.destination);
      osc.start(start);
      osc.stop(start + 0.2);
    });
  } catch {
    // audio unavailable: the visual toast still shows
  }
}
