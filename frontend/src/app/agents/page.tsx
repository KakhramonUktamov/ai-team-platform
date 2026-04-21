"use client";
import { useState, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Loader2, Download, RotateCcw, Copy, Check } from "lucide-react";
import { streamAgent, apiPost } from "@/lib/api";
import ReactMarkdown from "react-markdown";

function AgentWorkspace() {
  const params = useSearchParams();
  const agentType = params.get("type") || "content-writer";

  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [meta, setMeta] = useState<any>(null);
  const outputRef = useRef<HTMLDivElement>(null);

  // Content writer fields
  const [topic, setTopic] = useState("");
  const [format, setFormat] = useState("blog_post");
  const [tone, setTone] = useState("professional");
  const [audience, setAudience] = useState("general audience");
  const [wordCount, setWordCount] = useState(800);

  // Email marketer fields
  const [product, setProduct] = useState("");
  const [goal, setGoal] = useState("nurture_leads");
  const [segment, setSegment] = useState("all subscribers");
  const [emailCount, setEmailCount] = useState(5);
  const [brandVoice, setBrandVoice] = useState("professional, friendly");

  // SEO fields
  const [keywords, setKeywords] = useState("");
  const [seoContent, setSeoContent] = useState("");
  const [seoMode, setSeoMode] = useState("content_audit");

  const buildPayload = () => {
    if (agentType === "content-writer") return { topic, format, tone, audience, word_count: wordCount };
    if (agentType === "email-marketer") return { product, goal, segment, email_count: emailCount, brand_voice: brandVoice };
    if (agentType === "seo-optimizer") return { keywords, content: seoContent, mode: seoMode, topic, audience };
    return {};
  };

  const isReady = () => {
    if (agentType === "content-writer") return !!topic;
    if (agentType === "email-marketer") return !!product;
    if (agentType === "seo-optimizer") return !!(keywords || topic);
    return false;
  };

  const handleRun = async () => {
    if (!isReady()) return;
    setLoading(true);
    setOutput("");
    setMeta(null);
    try {
      let text = "";
      for await (const chunk of streamAgent(agentType, buildPayload())) {
        text += chunk;
        setOutput(text);
      }
    } catch (e: any) {
      setOutput(`Error: ${e.message}`);
    }
    setLoading(false);
  };

  const handleCopy = () => { navigator.clipboard.writeText(output); setCopied(true); setTimeout(() => setCopied(false), 2000); };

  const title = agentType.replace("-", " ").replace(/\b\w/g, (c) => c.toUpperCase());
  const descriptions: Record<string,string> = {
    "content-writer": "Generate blog posts, social media content, newsletters, and product descriptions.",
    "email-marketer": "Create email drip sequences with subject lines, A/B variants, and CTAs.",
    "seo-optimizer": "Analyze keywords, audit content, generate meta tags, and optimize for search.",
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-zinc-900">{title}</h1>
        <p className="text-sm text-zinc-500 mt-1">{descriptions[agentType] || ""}</p>
      </div>

      <div className="grid grid-cols-5 gap-6">
        {/* Input panel */}
        <div className="col-span-2 space-y-4">
          <div className="bg-white rounded-xl border border-surface-200 p-5 space-y-4">
            {agentType === "content-writer" && (<>
              <div>
                <label className="block text-xs font-medium text-zinc-500 mb-1.5">Topic</label>
                <textarea value={topic} onChange={(e) => setTopic(e.target.value)} rows={3} placeholder="e.g., 10 Python tips every dev should know" className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-400 focus:border-transparent outline-none resize-none" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-zinc-500 mb-1.5">Format</label>
                  <select value={format} onChange={(e) => setFormat(e.target.value)} className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm">
                    <option value="blog_post">Blog post</option>
                    <option value="social_media">Social media</option>
                    <option value="email_newsletter">Newsletter</option>
                    <option value="product_description">Product description</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-500 mb-1.5">Tone</label>
                  <select value={tone} onChange={(e) => setTone(e.target.value)} className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm">
                    {["professional","casual","friendly","authoritative","witty","empathetic"].map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-500 mb-1.5">Audience</label>
                <input value={audience} onChange={(e) => setAudience(e.target.value)} className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-500 mb-1.5">Word count: {wordCount}</label>
                <input type="range" min={200} max={2000} step={100} value={wordCount} onChange={(e) => setWordCount(Number(e.target.value))} className="w-full" />
              </div>
            </>)}

            {agentType === "email-marketer" && (<>
              <div>
                <label className="block text-xs font-medium text-zinc-500 mb-1.5">Product / Service</label>
                <textarea value={product} onChange={(e) => setProduct(e.target.value)} rows={3} placeholder="e.g., SaaS project management tool, $29/month" className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm outline-none resize-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-500 mb-1.5">Campaign goal</label>
                <select value={goal} onChange={(e) => setGoal(e.target.value)} className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm">
                  {["welcome_series","trial_to_paid_conversion","product_launch","re_engagement","nurture_leads","onboarding","abandoned_cart"].map(g => <option key={g} value={g}>{g.replace(/_/g, " ")}</option>)}
                </select>
              </div>
              <div><label className="block text-xs font-medium text-zinc-500 mb-1.5">Segment</label><input value={segment} onChange={(e) => setSegment(e.target.value)} className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm" /></div>
              <div><label className="block text-xs font-medium text-zinc-500 mb-1.5">Emails: {emailCount}</label><input type="range" min={2} max={10} value={emailCount} onChange={(e) => setEmailCount(Number(e.target.value))} className="w-full" /></div>
              <div><label className="block text-xs font-medium text-zinc-500 mb-1.5">Brand voice</label><input value={brandVoice} onChange={(e) => setBrandVoice(e.target.value)} className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm" /></div>
            </>)}

            {agentType === "seo-optimizer" && (<>
              <div>
                <label className="block text-xs font-medium text-zinc-500 mb-1.5">Mode</label>
                <select value={seoMode} onChange={(e) => setSeoMode(e.target.value)} className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm">
                  {["keyword_analysis","content_audit","meta_generator","optimize_content","full_audit"].map(m => <option key={m} value={m}>{m.replace(/_/g, " ")}</option>)}
                </select>
              </div>
              <div><label className="block text-xs font-medium text-zinc-500 mb-1.5">Keywords</label><input value={keywords} onChange={(e) => setKeywords(e.target.value)} placeholder="python performance, optimize python" className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm" /></div>
              {seoMode !== "keyword_analysis" && (
                <div><label className="block text-xs font-medium text-zinc-500 mb-1.5">Content to analyze</label><textarea value={seoContent} onChange={(e) => setSeoContent(e.target.value)} rows={6} className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm outline-none resize-none" /></div>
              )}
              {seoMode === "keyword_analysis" && (
                <div><label className="block text-xs font-medium text-zinc-500 mb-1.5">Topic</label><input value={topic} onChange={(e) => setTopic(e.target.value)} className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm" /></div>
              )}
            </>)}

            <button onClick={handleRun} disabled={loading || !isReady()} className="w-full py-2.5 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2">
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</> : "Generate"}
            </button>
          </div>
        </div>

        {/* Output panel */}
        <div className="col-span-3">
          <div className="bg-white rounded-xl border border-surface-200 min-h-[500px] flex flex-col">
            <div className="flex items-center justify-between px-5 py-3 border-b border-surface-100">
              <span className="text-xs font-medium text-zinc-400 uppercase tracking-wide">Output</span>
              {output && (
                <div className="flex gap-1.5">
                  <button onClick={handleCopy} className="p-1.5 rounded-md hover:bg-surface-100 text-zinc-400 hover:text-zinc-600 transition-colors">
                    {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
                  </button>
                  <a href={`data:text/plain,${encodeURIComponent(output)}`} download={`${agentType}-output.txt`} className="p-1.5 rounded-md hover:bg-surface-100 text-zinc-400 hover:text-zinc-600 transition-colors">
                    <Download className="w-4 h-4" />
                  </a>
                  <button onClick={() => { setOutput(""); setMeta(null); }} className="p-1.5 rounded-md hover:bg-surface-100 text-zinc-400 hover:text-zinc-600 transition-colors">
                    <RotateCcw className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
            <div ref={outputRef} className="flex-1 p-5 overflow-y-auto">
              {output ? (
                <div className="prose max-w-none text-sm"><ReactMarkdown>{output}</ReactMarkdown></div>
              ) : (
                <div className="flex items-center justify-center h-full text-zinc-300 text-sm">
                  Output will appear here...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AgentsPage() {
  return <Suspense fallback={<div className="p-8">Loading...</div>}><AgentWorkspace /></Suspense>;
}
