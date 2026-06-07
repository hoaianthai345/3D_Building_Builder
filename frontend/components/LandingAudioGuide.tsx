"use client";

import { useEffect, useRef, useState } from "react";
import { SpeakerHighIcon } from "@phosphor-icons/react";

export function LandingAudioGuide({ src }: { src: string }) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [blocked, setBlocked] = useState(false);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.volume = 0.86;
    const play = async () => {
      try {
        await audio.play();
        setPlaying(true);
        setBlocked(false);
      } catch {
        setBlocked(true);
      }
    };
    void play();
  }, []);

  async function playNow() {
    const audio = audioRef.current;
    if (!audio) return;
    try {
      await audio.play();
      setPlaying(true);
      setBlocked(false);
    } catch {
      setBlocked(true);
    }
  }

  return (
    <div className="mt-6">
      <audio
        ref={audioRef}
        controls
        preload="metadata"
        src={src}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        className="w-full"
      />
      {blocked && (
        <button
          type="button"
          onClick={playNow}
          className="mt-3 inline-flex h-10 items-center gap-2 rounded-[10px] bg-[var(--accent-strong)] px-4 text-sm font-medium text-white hover:bg-[var(--accent-hover)]"
        >
          <SpeakerHighIcon size={18} /> Nghe hướng dẫn
        </button>
      )}
      {!blocked && playing && (
        <p className="mt-2 text-xs text-[var(--text-faint)]">Đang phát giọng đọc giới thiệu website.</p>
      )}
    </div>
  );
}
