"use client";

import { useEffect, useRef, useState } from "react";
import { MusicNotesIcon, SpeakerSlashIcon } from "@phosphor-icons/react";

const MUSIC_SRC = "/audio/tour-ambient-loop.mp3";
const BASE_VOLUME = 0.14;
const DUCKED_VOLUME = 0.045;

export function BackgroundMusic() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [enabled, setEnabled] = useState(false);
  const [blocked, setBlocked] = useState(false);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.volume = BASE_VOLUME;
    const tryPlay = async () => {
      try {
        await audio.play();
        setEnabled(true);
        setBlocked(false);
      } catch {
        setBlocked(true);
      }
    };
    void tryPlay();
  }, []);

  useEffect(() => {
    const onPlay = (event: Event) => {
      const target = event.target;
      const audio = audioRef.current;
      if (!audio || target === audio || !(target instanceof HTMLAudioElement)) return;
      audio.volume = DUCKED_VOLUME;
    };
    const onPause = () => {
      const audio = audioRef.current;
      if (audio) audio.volume = BASE_VOLUME;
    };
    document.addEventListener("play", onPlay, true);
    document.addEventListener("pause", onPause, true);
    document.addEventListener("ended", onPause, true);
    return () => {
      document.removeEventListener("play", onPlay, true);
      document.removeEventListener("pause", onPause, true);
      document.removeEventListener("ended", onPause, true);
    };
  }, []);

  async function toggleMusic() {
    const audio = audioRef.current;
    if (!audio) return;
    if (enabled && !audio.paused) {
      audio.pause();
      setEnabled(false);
      return;
    }
    try {
      await audio.play();
      setEnabled(true);
      setBlocked(false);
    } catch {
      setBlocked(true);
    }
  }

  return (
    <>
      <audio ref={audioRef} src={MUSIC_SRC} loop preload="auto" aria-hidden="true" />
      <button
        type="button"
        onClick={toggleMusic}
        className="fixed bottom-4 right-4 z-[80] inline-flex h-11 items-center gap-2 rounded-full border border-white/30 bg-[rgba(31,30,28,0.76)] px-4 text-xs font-medium text-white shadow-[var(--shadow-md)] backdrop-blur hover:bg-[rgba(31,30,28,0.9)]"
        aria-label={enabled ? "Tắt nhạc nền" : "Bật nhạc nền"}
        title={enabled ? "Tắt nhạc nền" : "Bật nhạc nền"}
      >
        {enabled ? <MusicNotesIcon size={18} /> : <SpeakerSlashIcon size={18} />}
        <span>{enabled ? "Nhạc nền" : blocked ? "Bật nhạc" : "Nhạc nền"}</span>
      </button>
    </>
  );
}
