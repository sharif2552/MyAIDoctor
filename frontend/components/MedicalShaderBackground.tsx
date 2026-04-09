"use client";

import { useEffect, useRef } from "react";

/* Pre-computed particle colors — no per-frame string building */
const P_COLORS = [
  "rgba(100, 210, 255, 0.28)",
  "rgba(45,  212, 191, 0.28)",
  "rgba(140, 180, 255, 0.26)",
  "rgba(167, 139, 250, 0.22)",
];

const PARTICLE_COUNT = 28;   /* was 85  */
const FPS_INTERVAL   = 1000 / 24; /* 24 fps  */

export default function MedicalShaderBackground() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    /* particles with pre-assigned color index */
    const particles = Array.from({ length: PARTICLE_COUNT }, (_, i) => ({
      phase:  (Math.PI * 2 * i) / PARTICLE_COUNT,
      radius: 1.5 + Math.random() * 2.5,
      speed:  0.4 + Math.random() * 0.8,
      drift:  0.4 + Math.random() * 1.2,
      lane:   Math.random(),
      color:  P_COLORS[i % P_COLORS.length],
    }));

    let raf   = 0;
    let lastTs = 0;
    let width  = 0;
    let height = 0;
    /* Gradient objects — rebuilt only on resize, not every frame */
    let g1: CanvasGradient | null = null;
    let g2: CanvasGradient | null = null;

    const resize = () => {
      /* Cap DPR at 1 — background is decorative, crisp pixels not needed */
      const dpr = 1;
      width  = window.innerWidth;
      height = window.innerHeight;
      canvas.width  = Math.floor(width  * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width  = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      /* Pre-build gradients after every resize */
      g1 = ctx.createRadialGradient(width * 0.18, height * 0.08, 0, width * 0.18, height * 0.08, width * 0.72);
      g1.addColorStop(0, "rgba(38, 111, 201, 0.28)");
      g1.addColorStop(1, "rgba(4, 11, 23, 0)");

      g2 = ctx.createRadialGradient(width * 0.85, height * 0.88, 0, width * 0.85, height * 0.88, width * 0.60);
      g2.addColorStop(0, "rgba(20, 140, 130, 0.20)");
      g2.addColorStop(1, "rgba(4, 11, 23, 0)");
    };

    /* Coarser step (16px) — was 8px, half as many path points */
    const drawWave = (t: number, yOffset: number, color: string, amp = 34, freq = 0.012) => {
      ctx.beginPath();
      for (let x = -20; x <= width + 20; x += 16) {
        const y = yOffset
          + Math.sin(x * freq + t * 0.0018) * amp
          + Math.sin(x * freq * 0.55 - t * 0.0012) * (amp * 0.38);
        x === -20 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.strokeStyle = color;
      ctx.lineWidth   = 1.5;
      ctx.stroke();
    };

    /* Coarser step (14px) — was 6px */
    const drawHeartbeat = (t: number) => {
      const baseline = height * 0.34;
      const speed    = t * 0.0022;
      ctx.beginPath();
      for (let x = 0; x <= width; x += 14) {
        const p     = (x / width) * 8 + speed;
        const pulse = Math.exp(-Math.pow((p % 1) - 0.52, 2) * 120);
        const y     = baseline + Math.sin(p * 7) * 4 - pulse * 34;
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.strokeStyle = "rgba(111, 238, 222, 0.32)";
      ctx.lineWidth   = 1.5;
      ctx.stroke();
    };

    const render = (ts: number) => {
      raf = requestAnimationFrame(render);
      if (ts - lastTs < FPS_INTERVAL) return;
      lastTs = ts;

      ctx.clearRect(0, 0, width, height);

      /* Reuse pre-built gradients */
      if (g1) { ctx.fillStyle = g1; ctx.fillRect(0, 0, width, height); }
      if (g2) { ctx.fillStyle = g2; ctx.fillRect(0, 0, width, height); }

      /* Two waves (was three) */
      drawWave(ts, height * 0.62, "rgba(96, 165, 250, 0.22)", 44, 0.010);
      drawWave(ts + 700, height * 0.55, "rgba(45, 212, 191, 0.20)", 34, 0.014);
      drawHeartbeat(ts);

      /* Particles — pre-computed colors, batched per color to reduce state changes */
      for (let ci = 0; ci < P_COLORS.length; ci++) {
        ctx.fillStyle = P_COLORS[ci];
        ctx.beginPath();
        particles.forEach((p) => {
          if (p.color !== P_COLORS[ci]) return;
          const x     = ((Math.sin(ts * 0.0005 * p.speed + p.phase) + 1) / 2) * width;
          const yBase = height * (0.22 + p.lane * 0.62);
          const y     = yBase + Math.sin(ts * 0.0013 * p.drift + p.phase) * 26;
          ctx.moveTo(x + p.radius, y);
          ctx.arc(x, y, p.radius, 0, Math.PI * 2);
        });
        ctx.fill();
      }
    };

    resize();
    raf = requestAnimationFrame(render);

    window.addEventListener("resize", resize, { passive: true });
    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div
      aria-hidden="true"
      style={{ position: "fixed", inset: 0, zIndex: 0, pointerEvents: "none", overflow: "hidden" }}
    >
      <canvas ref={canvasRef} />
    </div>
  );
}
