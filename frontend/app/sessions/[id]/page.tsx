"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

import AuthGuard from "@/components/AuthGuard";
import { apiFetch } from "@/lib/api";

type Row = { role: string; agent: string; content: string };

export default function SessionPage() {
  const params = useParams<{ id: string }>();
  const [rows, setRows] = useState<Row[]>([]);

  useEffect(() => {
    const load = async () => {
      const token = localStorage.getItem("token");
      if (!token || !params.id) return;
      const data = await apiFetch<{ messages: Row[] }>(`/sessions/${params.id}/messages`, {}, token).catch(() => ({ messages: [] }));
      setRows(data.messages || []);
    };
    void load();
  }, [params.id]);

  return (
    <AuthGuard>
      <section className="glass-shell animated-border glass-card">
        <h1 className="page-title">Session History</h1>
        <p className="muted">Session: {params.id}</p>
        <p>
          <Link href="/chat">Back to chat</Link>
        </p>
        <div className="stack">
          {rows.map((m, i) => (
            <article key={i} className="glass glass-card">
              <strong>{m.role} · {m.agent}</strong>
              <p style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>{m.content}</p>
            </article>
          ))}
        </div>
      </section>
    </AuthGuard>
  );
}
