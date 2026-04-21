"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, PenTool, Mail, MessageCircle, Search, BarChart3, Settings, Zap } from "lucide-react";
import clsx from "clsx";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/agents?type=content-writer", label: "Content writer", icon: PenTool },
  { href: "/agents?type=email-marketer", label: "Email marketer", icon: Mail },
  { href: "/agents?type=seo-optimizer", label: "SEO optimizer", icon: Search },
  { href: "/chatbot", label: "Support chatbot", icon: MessageCircle },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const path = usePathname();
  return (
    <aside className="w-64 bg-brand-900 text-white flex flex-col shrink-0">
      <div className="p-5 flex items-center gap-3 border-b border-white/10">
        <div className="w-9 h-9 rounded-lg bg-brand-500 flex items-center justify-center">
          <Zap className="w-5 h-5" />
        </div>
        <div>
          <div className="font-semibold text-sm tracking-tight">AI Team</div>
          <div className="text-[11px] text-brand-200">Platform v0.1</div>
        </div>
      </div>
      <nav className="flex-1 p-3 space-y-0.5">
        {nav.map((item) => {
          const active = path === item.href || (item.href.startsWith("/agents") && path === "/agents" && item.href.includes(new URLSearchParams(typeof window !== "undefined" ? window.location.search : "").get("type") || "content-writer"));
          const isActive = path === item.href.split("?")[0] && (item.href.includes("?") ? typeof window !== "undefined" && window.location.search.includes(item.href.split("?")[1]?.split("=")[1] || "") : true);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors",
                path.startsWith(item.href.split("?")[0])
                  ? "bg-white/15 text-white font-medium"
                  : "text-brand-200 hover:bg-white/10 hover:text-white"
              )}
            >
              <item.icon className="w-[18px] h-[18px] shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-white/10">
        <div className="text-[11px] text-brand-300">4 agents active</div>
        <div className="mt-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
          <div className="h-full bg-emerald-400 rounded-full" style={{ width: "100%" }} />
        </div>
      </div>
    </aside>
  );
}
