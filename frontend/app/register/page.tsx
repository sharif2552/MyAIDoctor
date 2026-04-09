"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { authApi } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const data = await authApi.register(email, password);
      localStorage.setItem("token", data.access_token);
      router.push("/chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Register failed");
    }
  };

  return (
    <section className="glass-shell animated-border glass-card auth-shell">
      <h1 className="page-title">Create Account</h1>
      <p className="muted">Start your diagnostic workspace</p>
      <form className="stack" onSubmit={onSubmit}>
        <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button type="submit">Register</button>
      </form>
      {error ? <p className="error-text">{error}</p> : null}
      <p className="muted">
        Already registered? <Link href="/login">Login</Link>
      </p>
    </section>
  );
}
