"use client";

import { useEffect, useRef } from "react";

export default function MedicalShaderBackground() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const reducedMotion = media.matches;
    const particleCount = reducedMotion ? 30 : 85;
    const particles = Array.from({ length: particleCount }, (_, i) => ({
      phase: (Math.PI * 2 * i) / particleCount,
      radius: 1.6 + Math.random() * 2.8,
      speed: 0.4 + Math.random() * 0.9,
      drift: 0.4 + Math.random() * 1.4,
      lane: Math.random(),
    }));

    let raf = 0;
    let width = 0;
    let height = 0;
    let dpr = 1;

    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const drawWave = (t: number, yOffset: number, color: string, amp = 34, freq = 0.012) => {
      ctx.beginPath();
      for (let x = -20; x <= width + 20; x += 8) {
        const y =
          yOffset +
          Math.sin(x * freq + t * 0.0018) * amp +
          Math.sin(x * (freq * 0.55) - t * 0.0012) * (amp * 0.38);
        if (x === -20) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();
    };

    const drawHeartbeat = (t: number) => {
      const baseline = height * 0.34;
      const speed = t * 0.0022;
      ctx.beginPath();
      for (let x = 0; x <= width; x += 6) {
        const p = (x / width) * 8 + speed;
        const pulse = Math.exp(-Math.pow((p % 1) - 0.52, 2) * 120);
        const y = baseline + Math.sin(p * 7) * 4 - pulse * 34;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = "rgba(111, 238, 222, 0.36)";
      ctx.lineWidth = 1.5;
      ctx.stroke();
    };

    const render = (time: number) => {
      ctx.clearRect(0, 0, width, height);

      const g = ctx.createRadialGradient(width * 0.18, height * 0.08, 0, width * 0.18, height * 0.08, width * 0.8);
      g.addColorStop(0, "rgba(38, 111, 201, 0.25)");
      g.addColorStop(1, "rgba(4, 11, 23, 0)");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, width, height);

      drawWave(time, height * 0.62, "rgba(96, 165, 250, 0.22)", 42, 0.01);
      drawWave(time + 700, height * 0.55, "rgba(45, 212, 191, 0.2)", 34, 0.014);
      drawHeartbeat(time);

      particles.forEach((p) => {
        const x = ((Math.sin(time * 0.0005 * p.speed + p.phase) + 1) / 2) * width;
        const yBase = height * (0.22 + p.lane * 0.62);
        const y = yBase + Math.sin(time * 0.0013 * p.drift + p.phase) * 24;
        ctx.beginPath();
        ctx.arc(x, y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(122, 217, 255, 0.34)";
        ctx.fill();
      });

      if (!reducedMotion) {
        raf = window.requestAnimationFrame(render);
      }
    };

    resize();
    render(0);
    if (!reducedMotion) raf = window.requestAnimationFrame(render);

    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      window.cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div
      aria-hidden="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 0,
        pointerEvents: "none",
        overflow: "hidden",
      }}
    >
      <canvas ref={canvasRef} />
    </div>
  );
}
