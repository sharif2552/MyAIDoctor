"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

import AuthGuard from "@/components/AuthGuard";
import ChatShader from "@/components/ChatShader";
import { chatApi, SessionSummary, sessionsApi } from "@/lib/api";

type Line = { role: string; agent: string; content: string };
const ACTIVE_SESSION_KEY = "active_session_id";

function stripMdBold(s: string): string {
  return s.replace(/\*\*([^*]+)\*\*/g, "$1");
}

function FinalReportSection({ report }: { report: Record<string, unknown> }) {
  const summary =
    typeof report.summary_of_findings === "string" ? stripMdBold(report.summary_of_findings) : "";
  const dx = Array.isArray(report.differential_diagnosis) ? report.differential_diagnosis : [];
  const stepsRaw = report.recommended_next_steps;
  const steps = Array.isArray(stepsRaw)
    ? stepsRaw.filter((x): x is string => typeof x === "string")
    : [];
  const meta = report.metadata;
  const disclaimer =
    meta && typeof meta === "object" && meta !== null && "disclaimer" in meta
      ? String((meta as { disclaimer?: unknown }).disclaimer ?? "")
      : "";
  const evidence = Array.isArray(report.evidence_log) ? report.evidence_log : [];
  const treatment = Array.isArray(report.treatment_recommendations) ? report.treatment_recommendations : [];

  return (
    <section className="glass glass-card" style={{ marginTop: 16 }}>
      <h2 className="page-title" style={{ fontSize: "1.15rem", marginBottom: 8 }}>
        Medical report
      </h2>
      {summary ? (
        <div style={{ marginBottom: 14 }}>
          <strong style={{ display: "block", marginBottom: 6 }}>Summary of findings</strong>
          <p style={{ whiteSpace: "pre-wrap", margin: 0, lineHeight: 1.55 }}>{summary}</p>
        </div>
      ) : null}
      {dx.length ? (
        <div style={{ marginBottom: 14 }}>
          <strong style={{ display: "block", marginBottom: 6 }}>Differential diagnosis</strong>
          <ul style={{ margin: 0, paddingLeft: 20, lineHeight: 1.5 }}>
            {dx.map((item, i) => {
              const d = item as {
                condition?: string;
                confidence?: number;
                icd_hint?: string;
                supporting_evidence?: string[];
              };
              const ev = Array.isArray(d.supporting_evidence) ? d.supporting_evidence : [];
              return (
                <li key={i} style={{ marginBottom: 10 }}>
                  <span>
                    {d.condition ?? "—"}
                    {typeof d.confidence === "number" ? ` (${d.confidence}% confidence)` : ""}
                    {d.icd_hint ? ` · ICD hint: ${d.icd_hint}` : ""}
                  </span>
                  {ev.length ? (
                    <ul style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: "0.92em", opacity: 0.92 }}>
                      {ev.slice(0, 6).map((e, j) => (
                        <li key={j}>{e}</li>
                      ))}
                    </ul>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
      {treatment.length ? (
        <div style={{ marginBottom: 14 }}>
          <strong style={{ display: "block", marginBottom: 6 }}>Treatment options (from guidelines / sources)</strong>
          <ul style={{ margin: 0, paddingLeft: 20, lineHeight: 1.5 }}>
            {treatment.map((item, i) => {
              const t = item as {
                drug_or_class?: string;
                role?: string;
                dosing_note?: string;
                key_cautions?: string[];
              };
              const cautions = Array.isArray(t.key_cautions) ? t.key_cautions : [];
              return (
                <li key={i} style={{ marginBottom: 10 }}>
                  <strong>{t.drug_or_class ?? "—"}</strong>
                  {t.role ? ` — ${t.role}` : null}
                  {t.dosing_note ? (
                    <div style={{ marginTop: 4, fontSize: "0.95em" }}>{t.dosing_note}</div>
                  ) : null}
                  {cautions.length ? (
                    <ul style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: "0.9em", opacity: 0.9 }}>
                      {cautions.map((c, j) => (
                        <li key={j}>{c}</li>
                      ))}
                    </ul>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
      {steps.length ? (
        <div style={{ marginBottom: 14 }}>
          <strong style={{ display: "block", marginBottom: 6 }}>Recommended next steps</strong>
          <ol style={{ margin: 0, paddingLeft: 22, lineHeight: 1.55 }}>
            {steps.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ol>
        </div>
      ) : null}
      {evidence.length ? (
        <div style={{ marginBottom: 14 }}>
          <strong style={{ display: "block", marginBottom: 6 }}>Evidence reviewed</strong>
          <ul style={{ margin: 0, paddingLeft: 20, lineHeight: 1.45, fontSize: "0.92em" }}>
            {evidence.slice(0, 8).map((e, i) => {
              const row = e as { title?: string; url?: string; snippet?: string };
              return (
                <li key={i} style={{ marginBottom: 8 }}>
                  {row.title ?? "Source"}
                  {row.snippet ? ` — ${row.snippet.slice(0, 200)}${row.snippet.length > 200 ? "…" : ""}` : ""}
                  {row.url ? (
                    <>
                      {" "}
                      <a href={row.url} target="_blank" rel="noreferrer">
                        Link
                      </a>
                    </>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
      {disclaimer ? (
        <p className="muted" style={{ margin: 0, fontSize: "0.88rem", lineHeight: 1.45 }}>
          {disclaimer}
        </p>
      ) : null}
    </section>
  );
}

export default function ChatPage() {
  const [sessionId, setSessionId] = useState("");
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [input, setInput] = useState("");
  const [hitlAnswer, setHitlAnswer] = useState("");
  const [hitlQuestion, setHitlQuestion] = useState("");
  const [messages, setMessages] = useState<Line[]>([]);
  const [error, setError] = useState("");
  const [booting, setBooting] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [finalReport, setFinalReport] = useState<Record<string, unknown> | null>(null);
  const [reportOpen, setReportOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const timelineRef = useRef<HTMLElement>(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);

  useEffect(() => {
    const boot = async () => {
      setError("");
      const token = localStorage.getItem("token");
      if (!token) return;
      try {
        const existing = await sessionsApi.list(token);
        let selected = existing[0];
        const storedId = localStorage.getItem(ACTIVE_SESSION_KEY);
        if (storedId) {
          const found = existing.find((s) => s.id === storedId);
          if (found) selected = found;
        }
        if (!selected) {
          selected = await sessionsApi.create(token);
          setSessions([selected]);
        } else {
          setSessions(existing);
        }
        setSessionId(selected.id);
        setHitlQuestion(selected.waiting_for_hitl ? selected.hitl_question || "" : "");
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load sessions");
      } finally {
        setBooting(false);
      }
    };
    void boot();
  }, []);

  useEffect(() => {
    const loadMessages = async () => {
      const token = localStorage.getItem("token");
      if (!token || !sessionId) return;
      setLoadingMessages(true);
      setError("");
      try {
        localStorage.setItem(ACTIVE_SESSION_KEY, sessionId);
        const data = await sessionsApi.messages(token, sessionId);
        setMessages(data.messages || []);
      } catch (e) {
        setMessages([]);
        setError(e instanceof Error ? e.message : "Failed to load conversation");
      } finally {
        setLoadingMessages(false);
      }
    };
    void loadMessages();
  }, [sessionId]);

  useEffect(() => {
    const loadReport = async () => {
      const token = localStorage.getItem("token");
      if (!token || !sessionId) return;
      try {
        const { final_report } = await chatApi.report(token, sessionId);
        setFinalReport(final_report ?? null);
      } catch {
        setFinalReport(null);
      }
    };
    void loadReport();
  }, [sessionId]);

  const handleNewConversation = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    setError("");
    setSidebarOpen(false);
    try {
      const created = await sessionsApi.create(token);
      setSessions((prev) => [created, ...prev]);
      setFinalReport(null);
      setSessionId(created.id);
      setMessages([]);
      setHitlQuestion("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create conversation");
    }
  };

  const switchSession = (nextSession: SessionSummary) => {
    setFinalReport(null);
    setReportOpen(false);
    setSessionId(nextSession.id);
    setHitlQuestion(nextSession.waiting_for_hitl ? nextSession.hitl_question || "" : "");
    setSidebarOpen(false);
  };

  const updateSessionHitlState = (waiting: boolean, question: string) => {
    setSessions((prev) =>
      prev.map((item) =>
        item.id === sessionId ? { ...item, waiting_for_hitl: waiting, hitl_question: question } : item
      )
    );
  };

  const refreshSessionList = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const list = await sessionsApi.list(token);
      setSessions(list);
    } catch {
      // ignore list refresh failures
    }
  };

  const send = async (overrideText?: string) => {
    setError("");
    const token = localStorage.getItem("token");
    const userText = overrideText ?? input;
    if (!token || !sessionId || !userText.trim()) return;
    setMessages((prev) => [...prev, { role: "user", agent: "user", content: userText }]);
    setInput("");
    try {
      const res = await chatApi.send(token, sessionId, userText);
      setMessages((prev) => [...prev, ...res.messages]);
      const question = res.waiting_for_hitl ? res.hitl_question : "";
      setHitlQuestion(question);
      updateSessionHitlState(res.waiting_for_hitl, question);
      if (res.final_report) { setFinalReport(res.final_report); setReportOpen(true); }
      else if (res.session_done) {
        try {
          const r = await chatApi.report(token, sessionId);
          if (r.final_report) { setFinalReport(r.final_report); setReportOpen(true); }
        } catch {
          /* keep prior report if any */
        }
      }
      void refreshSessionList();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Message failed");
    }
  };

  const submitHitl = async (overrideText?: string) => {
    const token = localStorage.getItem("token");
    const answerText = overrideText ?? hitlAnswer;
    if (!token || !sessionId || !answerText.trim()) return;
    try {
      const res = await chatApi.hitl(token, sessionId, answerText);
      setMessages((prev) => [...prev, { role: "user", agent: "user", content: answerText }, ...res.messages]);
      const question = res.waiting_for_hitl ? res.hitl_question : "";
      setHitlQuestion(question);
      updateSessionHitlState(res.waiting_for_hitl, question);
      if (res.final_report) { setFinalReport(res.final_report); setReportOpen(true); }
      else if (res.session_done) {
        try {
          const r = await chatApi.report(token, sessionId);
          if (r.final_report) { setFinalReport(r.final_report); setReportOpen(true); }
        } catch {
          /* keep prior report if any */
        }
      }
      setHitlAnswer("");
      void refreshSessionList();
    } catch (e) {
      setError(e instanceof Error ? e.message : "HITL failed");
    }
  };

  // Show scroll-to-bottom button when not near the bottom
  useEffect(() => {
    const el = timelineRef.current;
    if (!el) return;
    const onScroll = () => {
      setShowScrollBtn(el.scrollHeight - el.scrollTop - el.clientHeight > 80);
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, []);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    const el = timelineRef.current;
    if (!el) return;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 120;
    if (isNearBottom) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const scrollToBottom = () => {
    const el = timelineRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  };

  return (
    <AuthGuard>
      <div className="chat-shader-wrap">
        {/* 3-D WebGL shader — rendered behind the glass card */}
        <div className="chat-shader-canvas-box">
          <ChatShader />
        </div>

        <section className="glass-shell glass-shell-above animated-border chat-layout">

          {/* ── Sidebar backdrop (closes drawer on click) ───────── */}
          {sidebarOpen && (
            <div
              className="sidebar-backdrop"
              onClick={() => setSidebarOpen(false)}
              aria-hidden="true"
            />
          )}

          {/* ── Sidebar drawer ───────────────────────────────────── */}
          <aside className={`chat-sidebar${sidebarOpen ? " sidebar-open" : ""}`}>
            <button
              className="btn-sidebar-close"
              onClick={() => setSidebarOpen(false)}
              aria-label="Close conversations"
            >
              ✕
            </button>
            <div className="conv-panel-header">
              <span className="conv-panel-label">Conversations</span>
            </div>
            <button className="btn-new-conv" onClick={handleNewConversation}>+ New chat</button>
            <ul className="conv-list">
              {sessions.map((s, idx) => {
                const active = s.id === sessionId;
                return (
                  <li key={s.id}>
                    <button
                      onClick={() => switchSession(s)}
                      className={`conv-item${active ? " conv-item--active" : ""}`}
                    >
                      <span className="conv-item-dot" />
                      <span className="conv-item-title">
                        {s.title || `Conversation ${sessions.length - idx}`}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </aside>

          {/* ── Main chat area ───────────────────────────────────── */}
          <div className="chat-main">
            <header className="top-nav">
              <div className="top-nav-brand">
                <button
                  className="btn-hamburger"
                  onClick={() => setSidebarOpen(true)}
                  aria-label="Open conversations"
                >
                  ☰
                </button>
                <h1 className="page-title">MyAIDoctor</h1>
              </div>

              <div className="top-nav-actions">
                {sessionId ? (
                  <Link href={`/sessions/${sessionId}`} className="nav-pill">Session</Link>
                ) : null}
                {sessionId ? (
                  <Link href={`/reports/${sessionId}`} className="nav-pill">Report</Link>
                ) : null}
                <button
                  className="btn-logout"
                  onClick={() => {
                    localStorage.removeItem("token");
                    window.location.href = "/login";
                  }}
                >
                  Logout
                </button>
              </div>
            </header>

            <div className="chat-timeline-wrap">
            <section ref={timelineRef} className="glass glass-strong chat-timeline">
              {booting || loadingMessages ? (
                <article className="message-row">
                  <div className="message-bubble">
                    <div className="message-meta">System</div>
                    Loading conversation...
                  </div>
                </article>
              ) : !messages.length ? (
                <article className="message-row">
                  <div className="message-bubble">
                    <div className="message-meta">System</div>
                    Share what you are feeling and when it started. You can also ask:{" "}
                    <em>do tavily search ...</em> for live web research.
                  </div>
                </article>
              ) : null}
              {messages.filter((m) => m.agent !== "actor" && m.agent !== "skeptic").map((m, i) => (
                <article key={`${i}-${m.agent}`} className={`message-row ${m.role === "user" ? "user" : ""}`}>
                  <div className={`message-bubble ${m.role === "user" ? "user" : m.agent}`}>
                    <div className="message-meta">{m.role === "user" ? "You" : m.agent}</div>
                    <p style={{ whiteSpace: "pre-wrap", margin: 0 }}>{m.content}</p>
                  </div>
                </article>
              ))}
            </section>
            {showScrollBtn && (
              <button className="btn-scroll-bottom" onClick={scrollToBottom} aria-label="Scroll to bottom">
                ↓
              </button>
            )}
            </div>

            {finalReport ? (
              <>
                <button
                  className="btn-report-toggle"
                  onClick={() => setReportOpen((o) => !o)}
                >
                  {reportOpen ? "Hide report" : "View medical report"}
                </button>
                {reportOpen ? (
                  <div className="report-drawer glass glass-card">
                    <button
                      className="btn-report-close"
                      onClick={() => setReportOpen(false)}
                      aria-label="Close report"
                    >
                      ✕
                    </button>
                    <FinalReportSection report={finalReport} />
                  </div>
                ) : null}
              </>
            ) : null}

            <section className={`glass composer${hitlQuestion ? " animated-border" : ""}`}>
              <div className="composer-row">
                <textarea
                  rows={3}
                  value={hitlQuestion ? hitlAnswer : input}
                  onChange={(e) =>
                    hitlQuestion ? setHitlAnswer(e.target.value) : setInput(e.target.value)
                  }
                  placeholder={
                    hitlQuestion ? "Type your answer…" : "Describe symptoms or ask for research…"
                  }
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      const val = (e.target as HTMLTextAreaElement).value;
                      hitlQuestion ? submitHitl(val) : send(val);
                    }
                  }}
                />
                <button onClick={() => hitlQuestion ? submitHitl() : send()}>
                  {hitlQuestion ? "Answer" : "Send"}
                </button>
              </div>
            </section>

            {error ? <p className="error-text">{error}</p> : null}
          </div>

        </section>
      </div>
    </AuthGuard>
  );
}
