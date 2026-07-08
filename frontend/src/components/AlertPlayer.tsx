/** Alert player — fetches TTS audio and plays via <audio> element. */

import { useEffect, useRef, useState } from "react";
import { getTtsAudio } from "../api/endpoints";

interface AlertPlayerProps {
  message: string;
}

export function AlertPlayer({ message }: AlertPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    getTtsAudio(message)
      .then((url) => {
        if (cancelled) return;
        setAudioUrl(url);
        setLoading(false);
        if (url && audioRef.current) {
          audioRef.current.play().catch(() => {
            // Autoplay blocked — user needs to click play
          });
        }
      })
      .catch(() => {
        if (cancelled) return;
        setError("TTS unavailable");
        setLoading(false);
      });

    return () => {
      cancelled = true;
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [message]);

  return (
    <div className="flex items-center gap-2 border-t border-slate-200 px-4 py-2.5 dark:border-slate-700">
      <span className="text-sm">🔊</span>
      {loading && <span className="text-xs text-slate-500 dark:text-slate-400">Generating audio...</span>}
      {error && <span className="text-xs text-slate-500 dark:text-slate-400">{error}</span>}
      {audioUrl && (
        <audio ref={audioRef} src={audioUrl} controls className="h-7 w-full" />
      )}
    </div>
  );
}
