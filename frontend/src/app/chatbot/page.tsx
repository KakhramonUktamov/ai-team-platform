"use client";
import { useState, useRef, useEffect } from "react";
import { Send, Upload, Trash2, FileText, Bot, User, AlertTriangle } from "lucide-react";
import { apiPost, apiGet, apiDelete, streamChat } from "@/lib/api";
import ReactMarkdown from "react-markdown";

type Message = { role: "user" | "assistant"; content: string; confidence?: number; sources?: any[]; escalation?: any };

export default function ChatbotPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [docs, setDocs] = useState<any[]>([]);
  const [workspace, setWorkspace] = useState("default");
  const [showKB, setShowKB] = useState(true);
  const messagesEnd = useRef<HTMLDivElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => { loadDocs(); }, [workspace]);
  useEffect(() => { messagesEnd.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const loadDocs = async () => {
    try { const r = await apiGet(`/api/chat/documents?workspace_id=${workspace}`); setDocs(r.documents || []); } catch {}
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    try {
      const r = await fetch(`/api/chat/ingest/file?workspace_id=${workspace}`, { method: "POST", body: form });
      if (r.ok) { await loadDocs(); }
    } catch {}
    e.target.value = "";
  };

  const handleDelete = async (docId: string) => {
    try { await apiDelete(`/api/chat/documents/${docId}?workspace_id=${workspace}`); await loadDocs(); } catch {}
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const r = await apiPost("/api/chat/message", {
        question,
        workspace_id: workspace,
        conversation_history: messages.slice(-10),
      });
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: r.answer,
        confidence: r.confidence,
        sources: r.sources,
        escalation: r.escalation,
      }]);
    } catch (e: any) {
      setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${e.message}` }]);
    }
    setLoading(false);
  };

  return (
    <div className="flex h-full">
      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        <div className="px-8 py-5 border-b border-surface-200">
          <h1 className="text-2xl font-bold text-zinc-900">Support chatbot</h1>
          <p className="text-sm text-zinc-500 mt-1">Ask questions — answers are grounded in your knowledge base</p>
        </div>

        <div className="flex-1 overflow-y-auto px-8 py-6 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-zinc-300">
              <Bot className="w-12 h-12 mb-3" />
              <p className="text-sm">Upload documents, then start asking questions</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
              {m.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-4 h-4 text-brand-600" />
                </div>
              )}
              <div className={`max-w-[70%] ${m.role === "user" ? "bg-brand-600 text-white rounded-2xl rounded-br-md px-4 py-2.5" : "bg-white border border-surface-200 rounded-2xl rounded-bl-md px-4 py-3"}`}>
                {m.role === "user" ? (
                  <p className="text-sm">{m.content}</p>
                ) : (
                  <>
                    <div className="prose text-sm max-w-none"><ReactMarkdown>{m.content}</ReactMarkdown></div>
                    {(m.confidence !== undefined || m.sources) && (
                      <div className="mt-2 pt-2 border-t border-surface-100 flex flex-wrap gap-3 text-[11px]">
                        {m.confidence !== undefined && (
                          <span className={`font-medium ${m.confidence > 0.7 ? "text-emerald-600" : m.confidence > 0.4 ? "text-amber-600" : "text-red-500"}`}>
                            Confidence: {Math.round(m.confidence * 100)}%
                          </span>
                        )}
                        {m.sources?.map((s: any, j: number) => (
                          <span key={j} className="text-zinc-400">{s.source}</span>
                        ))}
                      </div>
                    )}
                    {m.escalation?.should_escalate && (
                      <div className="mt-2 flex items-center gap-2 text-amber-600 text-xs bg-amber-50 px-3 py-1.5 rounded-lg">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Escalation: {m.escalation.reason}
                      </div>
                    )}
                  </>
                )}
              </div>
              {m.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-4 h-4 text-white" />
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-brand-600" />
              </div>
              <div className="bg-white border border-surface-200 rounded-2xl rounded-bl-md px-4 py-3">
                <div className="flex gap-1"><div className="w-2 h-2 bg-zinc-300 rounded-full animate-bounce" /><div className="w-2 h-2 bg-zinc-300 rounded-full animate-bounce [animation-delay:0.15s]" /><div className="w-2 h-2 bg-zinc-300 rounded-full animate-bounce [animation-delay:0.3s]" /></div>
              </div>
            </div>
          )}
          <div ref={messagesEnd} />
        </div>

        <div className="px-8 py-4 border-t border-surface-200">
          <div className="flex gap-3">
            <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()} placeholder="Ask a question..." className="flex-1 rounded-xl border border-surface-200 px-4 py-3 text-sm focus:ring-2 focus:ring-brand-400 outline-none" />
            <button onClick={handleSend} disabled={loading || !input.trim()} className="px-4 py-3 bg-brand-600 text-white rounded-xl hover:bg-brand-700 disabled:opacity-50 transition-colors">
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Knowledge base sidebar */}
      <div className="w-72 border-l border-surface-200 bg-white flex flex-col shrink-0">
        <div className="px-4 py-4 border-b border-surface-100">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-zinc-700">Knowledge base</h3>
            <button onClick={() => fileInput.current?.click()} className="p-1.5 rounded-md hover:bg-surface-100 text-zinc-400 hover:text-zinc-600">
              <Upload className="w-4 h-4" />
            </button>
            <input ref={fileInput} type="file" accept=".pdf,.docx,.txt,.md,.html" className="hidden" onChange={handleUpload} />
          </div>
          <p className="text-xs text-zinc-400 mt-1">{docs.length} document{docs.length !== 1 ? "s" : ""} indexed</p>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {docs.length === 0 && (
            <div className="text-center text-zinc-300 text-xs py-8">
              <FileText className="w-8 h-8 mx-auto mb-2" />
              Upload PDFs, DOCX, or TXT files
            </div>
          )}
          {docs.map((d) => (
            <div key={d.doc_id} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-50 group">
              <FileText className="w-4 h-4 text-zinc-400 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-xs font-medium text-zinc-700 truncate">{d.source}</div>
                <div className="text-[11px] text-zinc-400">{d.total_chunks} chunks</div>
              </div>
              <button onClick={() => handleDelete(d.doc_id)} className="p-1 rounded hover:bg-red-50 text-zinc-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all">
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
