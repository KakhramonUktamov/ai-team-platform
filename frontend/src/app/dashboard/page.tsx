"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { PenTool, Mail, MessageCircle, Search, ArrowRight, Zap, Clock, CheckCircle2 } from "lucide-react";
import { apiGet } from "@/lib/api";

const agents = [
  { id: "content-writer", name: "Content writer", desc: "Blog posts, social media, newsletters, product copy", icon: PenTool, color: "bg-violet-500", lightBg: "bg-violet-50", textColor: "text-violet-700" },
  { id: "email-marketer", name: "Email marketer", desc: "Drip sequences, subject lines, A/B variants, CTAs", icon: Mail, color: "bg-sky-500", lightBg: "bg-sky-50", textColor: "text-sky-700" },
  { id: "support-chatbot", name: "Support chatbot", desc: "RAG-powered Q&A with escalation detection", icon: MessageCircle, color: "bg-emerald-500", lightBg: "bg-emerald-50", textColor: "text-emerald-700", href: "/chatbot" },
  { id: "seo-optimizer", name: "SEO optimizer", desc: "Keywords, audits, meta tags, content optimization", icon: Search, color: "bg-amber-500", lightBg: "bg-amber-50", textColor: "text-amber-700" },
];

const stats = [
  { label: "Agents active", value: "4", icon: Zap, color: "text-brand-500" },
  { label: "Tasks today", value: "—", icon: CheckCircle2, color: "text-emerald-500" },
  { label: "Avg quality", value: "—", icon: CheckCircle2, color: "text-violet-500" },
  { label: "Uptime", value: "—", icon: Clock, color: "text-sky-500" },
];

export default function Dashboard() {
  const [status, setStatus] = useState<string>("checking...");

  useEffect(() => {
    fetch("/api/agents/types")
      .then((r) => r.json())
      .then((d) => setStatus(`${d.count} agents online`))
      .catch(() => setStatus("API offline — start the backend"));
  }, []);

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-zinc-900">Dashboard</h1>
        <p className="text-zinc-500 text-sm mt-1">Status: {status}</p>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-8">
        {stats.map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-surface-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-zinc-400 uppercase tracking-wide font-medium">{s.label}</span>
              <s.icon className={`w-4 h-4 ${s.color}`} />
            </div>
            <div className="text-2xl font-semibold text-zinc-900">{s.value}</div>
          </div>
        ))}
      </div>

      <h2 className="text-sm font-medium text-zinc-400 uppercase tracking-wide mb-4">Your agents</h2>
      <div className="grid grid-cols-2 gap-4">
        {agents.map((a) => (
          <Link
            key={a.id}
            href={a.href || `/agents?type=${a.id}`}
            className="group bg-white rounded-xl border border-surface-200 p-5 hover:border-brand-300 hover:shadow-md transition-all duration-200"
          >
            <div className="flex items-start justify-between mb-3">
              <div className={`w-10 h-10 ${a.lightBg} rounded-lg flex items-center justify-center`}>
                <a.icon className={`w-5 h-5 ${a.textColor}`} />
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                <span className="text-xs text-zinc-400">Active</span>
              </div>
            </div>
            <h3 className="font-semibold text-zinc-900 mb-1">{a.name}</h3>
            <p className="text-sm text-zinc-500 mb-4">{a.desc}</p>
            <div className="flex items-center text-sm text-brand-500 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
              Open agent <ArrowRight className="w-4 h-4 ml-1" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
