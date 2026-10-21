// Narration. Prefers the local natural voice (Kokoro via /api/tts); falls
// back to the browser Web Speech voice when the server engine isn't available.
// Both drive a per-sentence callback so the lesson text highlights as it reads.
import { api } from "./api";

export function splitSentences(text: string): string[] {
  return (text.match(/[^.!?]+[.!?]+|\S[^.!?]*$/g) || [text]).map((s) => s.trim()).filter(Boolean);
}

export interface NarrationHandle { stop: () => void; }
export type OnSentence = (index: number) => void;

let _localAvailable: boolean | null = null;
export async function localVoiceAvailable(): Promise<boolean> {
  if (_localAvailable !== null) return _localAvailable;
  try {
    const r = await fetch("/api/tts/status");
    const d = await r.json();
    _localAvailable = !!d.available;
  } catch { _localAvailable = false; }
  return _localAvailable;
}

// Local natural voice. Prefetches the NEXT sentence's audio while the current
// one plays, so there's no synth/network gap between sentences — smooth, like
// a real conversation. Still fires onSentence for highlight sync.
function speakLocal(sentences: string[], onSentence: OnSentence, onEnd: () => void, rate: number): NarrationHandle {
  let cancelled = false;
  let audio: HTMLAudioElement | null = null;

  const fetchUrl = async (i: number): Promise<string | null> => {
    try {
      const res = await api.tts(sentences[i]);
      if (!res.ok) return null;
      return URL.createObjectURL(await res.blob());
    } catch { return null; }
  };

  // Buffer for the upcoming sentence (starts immediately).
  let pending: Promise<string | null> | null = sentences.length ? fetchUrl(0) : null;

  const play = async (i: number) => {
    if (cancelled || i >= sentences.length) { if (!cancelled) onEnd(); return; }
    const url = await (pending ?? fetchUrl(i));
    // Kick off the next sentence's synth NOW, while this one plays.
    pending = i + 1 < sentences.length ? fetchUrl(i + 1) : null;
    if (cancelled) { if (url) URL.revokeObjectURL(url); return; }
    onSentence(i);
    if (!url) { play(i + 1); return; }
    audio = new Audio(url);
    audio.playbackRate = rate;
    const adv = () => { URL.revokeObjectURL(url); play(i + 1); };
    audio.onended = adv;
    audio.onerror = adv;
    audio.play().catch(adv);
  };

  play(0);
  return { stop: () => { cancelled = true; audio?.pause(); } };
}

// Browser Web Speech fallback.
function speakBrowserVoice(sentences: string[], onSentence: OnSentence, onEnd: () => void, rate: number): NarrationHandle {
  const synth = window.speechSynthesis;
  synth.cancel();
  let cancelled = false, i = 0;
  const voices = synth.getVoices();
  // Prefer a natural-sounding MALE English voice the OS offers.
  const male = /david|daniel|alex|fred|rishi|george|james|mark|guy|tom|oliver|male/i;
  const pref = voices.find((v) => /en/i.test(v.lang) && male.test(v.name) && /natural|neural|premium|enhanced|google/i.test(v.name))
    || voices.find((v) => /en/i.test(v.lang) && male.test(v.name))
    || voices.find((v) => /en-US|en-GB/i.test(v.lang));
  const next = () => {
    if (cancelled || i >= sentences.length) { if (!cancelled) onEnd(); return; }
    const u = new SpeechSynthesisUtterance(sentences[i]);
    u.rate = rate; u.pitch = 1.02;
    if (pref) u.voice = pref;
    onSentence(i);
    u.onend = () => { i += 1; next(); };
    u.onerror = () => { i += 1; next(); };
    synth.speak(u);
  };
  next();
  return { stop: () => { cancelled = true; synth.cancel(); } };
}

// Unified entry: local natural voice if available, else browser.
export async function narrate(
  sentences: string[], onSentence: OnSentence, onEnd: () => void, rate = 1,
): Promise<NarrationHandle> {
  if (await localVoiceAvailable()) return speakLocal(sentences, onSentence, onEnd, rate);
  return speakBrowserVoice(sentences, onSentence, onEnd, rate);
}

export function ttsSupported(): boolean {
  return typeof window !== "undefined" && ("speechSynthesis" in window);
}
