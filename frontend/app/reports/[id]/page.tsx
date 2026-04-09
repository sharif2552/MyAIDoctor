"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

import AuthGuard from "@/components/AuthGuard";
import { chatApi } from "@/lib/api";

export default function ReportPage() {
  const params = useParams<{ id: string }>();
  const [report, setReport] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    const load = async () => {
      const token = localStorage.getItem("token");
      if (!token || !params.id) return;
      const data = await chatApi.report(token, params.id);
      setReport(data.final_report);
    };
    void load();
  }, [params.id]);

  return (
    <AuthGuard>
      <section className="glass-shell animated-border glass-card">
        <h1 className="page-title">Final Report</h1>
        <p>
          <Link href="/chat">Back to chat</Link>
        </p>
        <pre className="glass glass-card report-code">
          {JSON.stringify(report, null, 2)}
        </pre>
      </section>
    </AuthGuard>
  );
}
