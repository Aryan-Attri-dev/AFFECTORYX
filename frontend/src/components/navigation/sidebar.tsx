"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Boxes,
  GitFork,
  Users2,
  GitPullRequest,
  Zap,
  FileCheck2,
  ShieldCheck,
  Settings,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  phase: string;
  activeInPhase1: boolean;
}

const navItems: NavItem[] = [
  { name: "Executive Overview", href: "/", icon: LayoutDashboard, phase: "Phase 1", activeInPhase1: true },
  { name: "Projects & Services", href: "/projects", icon: Boxes, phase: "Phase 1", activeInPhase1: true },
  { name: "Dependency Graph", href: "/graph", icon: GitFork, phase: "Phase 2", activeInPhase1: true },
  { name: "Evidence Registry", href: "/evidence", icon: FileCheck2, phase: "Phase 2", activeInPhase1: true },
  { name: "Change Analyzer", href: "/analyzer", icon: GitPullRequest, phase: "Phase 3", activeInPhase1: true },
  { name: "Impact Simulator", href: "/simulator", icon: Zap, phase: "Phase 3", activeInPhase1: true },
  { name: "Customer Intelligence", href: "/customers", icon: Users2, phase: "Phase 2", activeInPhase1: true },
  { name: "Audit & Security", href: "/audit", icon: ShieldCheck, phase: "Phase 1", activeInPhase1: true },
  { name: "Organization Settings", href: "/settings", icon: Settings, phase: "Phase 1", activeInPhase1: true },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-[#1f2937] bg-[#0d131f] flex flex-col justify-between shrink-0 min-h-[calc(100vh-3.5rem)]">
      <div className="p-3 space-y-6">
        <div>
          <div className="px-3 pb-2 text-[10px] font-mono uppercase tracking-wider text-gray-500">
            Platform Modules
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              const isReady = item.activeInPhase1;

              return (
                <Link
                  key={item.name}
                  href={isReady ? item.href : "#"}
                  className={`flex items-center justify-between px-3 py-2 rounded text-xs transition-colors ${
                    isActive && isReady
                      ? "bg-[#111827] text-gray-100 font-medium border border-[#1f2937]"
                      : isReady
                      ? "text-gray-400 hover:text-gray-200 hover:bg-[#111827]/60"
                      : "text-gray-600 cursor-not-allowed hover:bg-transparent"
                  }`}
                  onClick={(e) => {
                    if (!isReady) e.preventDefault();
                  }}
                >
                  <div className="flex items-center space-x-2.5 truncate">
                    <Icon className={`w-4 h-4 ${isActive && isReady ? "text-[#10b981]" : ""}`} />
                    <span className="truncate">{item.name}</span>
                  </div>
                  <span
                    className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${
                      isReady
                        ? "bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/20"
                        : "bg-[#1f2937] text-gray-500"
                    }`}
                  >
                    {item.phase}
                  </span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      <div className="p-3 border-t border-[#1f2937] text-[11px] text-gray-500 font-mono">
        <div>ENGINE: AFFECTORYX-CORE</div>
        <div className="text-[10px] text-gray-600">TENANT ISOLATION: ACTIVE</div>
      </div>
    </aside>
  );
}
