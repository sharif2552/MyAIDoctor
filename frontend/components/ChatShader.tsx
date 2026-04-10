"use client";

import { useEffect, useRef } from "react";

const VERT = `
attribute vec2 a_pos;
void main() { gl_Position = vec4(a_pos, 0.0, 1.0); }
`;

/*
 * Optimised fragment shader
 * - mediump precision (faster on mobile GPUs)
 * - 3 octave FBM (was 5)
 * - single warp layer q→f (was double q→r→f)
 * - 2 orbs (was 3), no scanline pass
 * Total noise evals per pixel: 9 (was 25)
 */
const FRAG = `
precision mediump float;
uniform float u_time;
uniform vec2  u_res;

float hash(float n) { return fract(sin(n) * 43758.5453); }

float noise(vec2 x) {
  vec2 i = floor(x);
  vec2 f = fract(x);
  f = f * f * (3.0 - 2.0 * f);
  float n = i.x + i.y * 57.0;
  return mix(
    mix(hash(n),        hash(n +  1.0), f.x),
    mix(hash(n + 57.0), hash(n + 58.0), f.x),
    f.y
  );
}

float fbm(vec2 p) {
  float v = 0.0, a = 0.5;
  for (int i = 0; i < 3; i++) {
    v += a * noise(p);
    p  = p * 2.02 + vec2(1.7, 9.2);
    a *= 0.5;
  }
  return v;
}

void main() {
  vec2 uv    = gl_FragCoord.xy / u_res;
  float ratio = u_res.x / u_res.y;
  float t    = u_time * 0.00022;

  vec2 p = uv;
  p.x   *= ratio;

  /* single domain-warp layer */
  vec2 q = vec2(
    fbm(p               + t * 0.60),
    fbm(p + vec2(5.2, 1.3) + t * 0.45)
  );
  float f = fbm(p + 2.0 * q + t * 0.18);

  /* palette */
  vec3 col = mix(vec3(0.01, 0.02, 0.10), vec3(0.02, 0.16, 0.28), clamp(f * 2.6,           0.0, 1.0));
  col      = mix(col, vec3(0.04, 0.58, 0.52),                     clamp((f - 0.28) * 3.2,  0.0, 1.0));
  col      = mix(col, vec3(0.46, 0.20, 0.82),                     clamp((f - 0.62) * 4.5,  0.0, 1.0));

  /* two animated orbs */
  float d0 = length(p - vec2(ratio * 0.28 + 0.08 * sin(t * 1.10), 0.60 + 0.09 * cos(t * 0.90)));
  float d1 = length(p - vec2(ratio * 0.72 + 0.11 * cos(t * 0.75), 0.36 + 0.11 * sin(t * 1.30)));
  col += 0.20 * vec3(0.10, 0.70, 0.80) * exp(-d0 * 3.2);
  col += 0.16 * vec3(0.30, 0.42, 0.92) * exp(-d1 * 2.8);

  /* vignette */
  vec2 vig = uv - 0.5;
  col *= 1.0 - smoothstep(0.25, 0.85, dot(vig, vig) * 2.8);

  col = pow(max(col, 0.0), vec3(0.88));
  col = clamp(col * 1.55, 0.0, 1.0);

  gl_FragColor = vec4(col, 1.0);
}
`;

/* Render at half resolution — CSS upscales it, blur is fine for a bg glow */
const RENDER_SCALE = 0.5;
/* Cap at 30 fps — fluid motion, far lower GPU pressure than 60 fps */
const FPS_INTERVAL = 1000 / 30;

export default function ChatShader() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    // Skip WebGL on mobile — CSS hides the wrapper, but also avoid creating the context
    if (window.matchMedia("(max-width: 768px)").matches) return;

    const gl = canvas.getContext("webgl", { antialias: false, alpha: false, powerPreference: "low-power" });
    if (!gl) return;

    const compile = (src: string, type: number) => {
      const s = gl.createShader(type)!;
      gl.shaderSource(s, src);
      gl.compileShader(s);
      return s;
    };

    const prog = gl.createProgram()!;
    gl.attachShader(prog, compile(VERT, gl.VERTEX_SHADER));
    gl.attachShader(prog, compile(FRAG, gl.FRAGMENT_SHADER));
    gl.linkProgram(prog);
    gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
    const posLoc = gl.getAttribLocation(prog, "a_pos");
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

    const uTime = gl.getUniformLocation(prog, "u_time");
    const uRes  = gl.getUniformLocation(prog, "u_res");

    let raf = 0;
    let lastTs = 0;

    const resize = () => {
      const w = Math.floor(canvas.offsetWidth  * RENDER_SCALE);
      const h = Math.floor(canvas.offsetHeight * RENDER_SCALE);
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width  = w;
        canvas.height = h;
        gl.viewport(0, 0, w, h);
      }
    };

    const render = (ts: number) => {
      raf = requestAnimationFrame(render);
      if (ts - lastTs < FPS_INTERVAL) return;
      lastTs = ts;
      gl.uniform1f(uTime, ts);
      gl.uniform2f(uRes, canvas.width, canvas.height);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    };

    resize();
    raf = requestAnimationFrame(render);

    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      gl.deleteProgram(prog);
      gl.deleteBuffer(buf);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{ display: "block", width: "100%", height: "100%" }}
    />
  );
}
