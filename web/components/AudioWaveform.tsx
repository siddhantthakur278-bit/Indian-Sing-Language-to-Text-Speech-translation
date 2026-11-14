"use client";

import React, { useEffect, useRef } from "react";

interface AudioWaveformProps {
  isActive: boolean;
  barCount?: number;
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({ isActive, barCount = 14 }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let phase = 0;

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      const barWidth = Math.floor(width / barCount) - 2;
      phase += 0.15;

      for (let i = 0; i < barCount; i++) {
        let barHeight = 3;
        if (isActive) {
          // Sine modulation with randomized variation for lively sound waves
          const wave = Math.sin(phase + i * 0.45) * 0.5 + 0.5;
          barHeight = Math.max(4, Math.floor(wave * (height - 4)));
        }

        const x = i * (barWidth + 2);
        const y = (height - barHeight) / 2;

        // Gradient from Gold to Ruby
        const grad = ctx.createLinearGradient(0, y, 0, y + barHeight);
        grad.addColorStop(0, "#FFDF00"); // bright gold
        grad.addColorStop(0.6, "#D4AF37"); // metallic gold
        grad.addColorStop(1, "#E63946"); // ruby red

        ctx.fillStyle = isActive ? grad : "#2A3447";
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, 2);
        ctx.fill();
      }

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [isActive, barCount]);

  return (
    <canvas
      ref={canvasRef}
      width={120}
      height={28}
      className="rounded-lg bg-space-950/80 border border-gold-500/20 px-1 py-0.5"
      title={isActive ? "Audio synthesis playing..." : "Audio idle"}
    />
  );
};
