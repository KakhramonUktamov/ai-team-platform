"use client";
import { useState, useEffect } from "react";
import { Settings as SettingsIcon, Key, Users, CreditCard, Plug } from "lucide-react";

const tabs = [
  { id: "general", label: "General", icon: SettingsIcon },
  { id: "api", label: "API keys", icon: Key },
  { id: "team", label: "Team", icon: Users },
  { id: "billing", label: "Billing", icon: CreditCard },
  { id: "integrations", label: "Integrations", icon: Plug },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("general");
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    fetch("/").then(r => r.json()).then(setStatus).catch(() => {});
  }, []);

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-zinc-900">Settings</h1>
        <p className="text-sm text-zinc-500 mt-1">Configure your platform</p>
      </div>

      <div className="flex gap-6">
        <div className="w-48 space-y-1 shrink-0">
          {tabs.map((t) => (
            <button key={t.id} onClick={() => setActiveTab(t.id)} className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${activeTab === t.id ? "bg-brand-50 text-brand-700 font-medium" : "text-zinc-500 hover:bg-surface-100"}`}>
              <t.icon className="w-4 h-4" /> {t.label}
            </button>
          ))}
        </div>

        <div className="flex-1 bg-white rounded-xl border border-surface-200 p-6">
          {activeTab === "general" && (
            <div className="space-y-4">
              <h2 className="font-semibold text-zinc-800">Platform status</h2>
              {status ? (
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between py-2 border-b border-surface-100"><span className="text-zinc-500">Status</span><span className="text-emerald-600 font-medium">{status.status}</span></div>
                  <div className="flex justify-between py-2 border-b border-surface-100"><span className="text-zinc-500">LLM provider</span><span className="font-medium">{status.provider}</span></div>
                  <div className="flex justify-between py-2 border-b border-surface-100"><span className="text-zinc-500">Model</span><span className="font-mono text-xs">{status.model}</span></div>
                  <div className="flex justify-between py-2"><span className="text-zinc-500">Version</span><span>{status.version}</span></div>
                </div>
              ) : <p className="text-sm text-zinc-400">Connecting to API...</p>}
            </div>
          )}
          {activeTab === "api" && (
            <div className="space-y-4">
              <h2 className="font-semibold text-zinc-800">API configuration</h2>
              <p className="text-sm text-zinc-500">API keys are managed in your <code className="bg-surface-100 px-1.5 py-0.5 rounded text-xs">.env</code> file on the server. The frontend does not handle keys directly for security.</p>
              <div className="bg-surface-50 rounded-lg p-4 font-mono text-xs space-y-1 text-zinc-600">
                <div>LLM_PROVIDER=openai</div>
                <div>OPENAI_API_KEY=sk-***</div>
                <div>ANTHROPIC_API_KEY=sk-ant-***</div>
              </div>
            </div>
          )}
          {activeTab === "team" && (
            <div className="space-y-4">
              <h2 className="font-semibold text-zinc-800">Team members</h2>
              <p className="text-sm text-zinc-500">Team management with Clerk authentication will be available in Phase 3. For now, the platform runs in single-user mode.</p>
            </div>
          )}
          {activeTab === "billing" && (
            <div className="space-y-4">
              <h2 className="font-semibold text-zinc-800">Billing</h2>
              <p className="text-sm text-zinc-500">Stripe billing integration will be available in Phase 3.</p>
            </div>
          )}
          {activeTab === "integrations" && (
            <div className="space-y-4">
              <h2 className="font-semibold text-zinc-800">Integrations</h2>
              <p className="text-sm text-zinc-500">Mailchimp, SendGrid, Slack, and Zapier connectors will be available in Phase 3.</p>
              <div className="grid grid-cols-2 gap-3">
                {["Mailchimp", "SendGrid", "Slack", "Zapier"].map((name) => (
                  <div key={name} className="border border-surface-200 rounded-lg p-4 flex items-center justify-between">
                    <span className="text-sm font-medium text-zinc-700">{name}</span>
                    <span className="text-xs text-zinc-400 bg-surface-100 px-2 py-0.5 rounded">Coming soon</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
