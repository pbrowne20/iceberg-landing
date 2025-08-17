"use client";
import { useState } from "react";

type NLQResponse = {
  answer?: string;
  code?: string;
  result?: any;
  error?: string;
  available_intents?: string[];
  plan?: any;
};

export default function NLQ() {
  const [q, setQ] = useState("");
  const [resp, setResp] = useState<NLQResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function ask() {
    setLoading(true);
    const r = await fetch("/api/nlq", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ q })
    });
    const data = await r.json();
    setResp(data);
    setLoading(false);
  }

  return (
    <main className="mx-auto max-w-2xl p-6 space-y-4">
      <h1 className="text-2xl font-semibold">ICEBERG: Natural Language</h1>
      <div className="flex gap-2">
        <input className="flex-1 border rounded px-3 py-2" placeholder="Ask: what's our current NOI per kSF?"
               value={q} onChange={e=>setQ(e.target.value)} />
        <button className="rounded px-4 py-2 border" onClick={ask} disabled={loading}>
          {loading ? "Thinking..." : "Ask"}
        </button>
      </div>
      {resp && (
        <section className="rounded-2xl shadow p-4 space-y-2">
          {resp.error ? (
            <>
              <div className="text-red-600">Error: {resp.error}</div>
              {resp.available_intents && (
                <div className="text-sm opacity-80">Try one: {resp.available_intents.join(", ")}</div>
              )}
            </>
          ) : (
            <>
              <div>{resp.answer}</div>
              <details className="cursor-pointer">
                <summary className="font-medium">Show code</summary>
                <pre className="text-xs overflow-auto mt-2">{resp.code}</pre>
              </details>
              <details className="cursor-pointer">
                <summary className="font-medium">Show raw result</summary>
                <pre className="text-xs overflow-auto mt-2">{JSON.stringify(resp.result, null, 2)}</pre>
              </details>
            </>
          )}
        </section>
      )}
    </main>
  );
}
