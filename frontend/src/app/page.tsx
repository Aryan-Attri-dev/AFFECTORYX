"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Header } from "@/components/navigation/header";
import { Sidebar } from "@/components/navigation/sidebar";
import { api } from "@/lib/api";
import { Project, AuditLog } from "@/types";
import {
  Boxes,
  ShieldCheck,
  Server,
  Layers,
  ArrowUpRight,
  GitPullRequest,
  CheckCircle2,
  Clock,
  Plus,
} from "lucide-react";
import Link from "next/link";
import { CreateProjectModal } from "@/components/projects/create-project-modal";

export default function DashboardPage() {
  const router = useRouter();
  const { user, activeOrg, isLoading } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [user, isLoading, router]);

  useEffect(() => {
    if (activeOrg) {
      setDataLoading(true);
      Promise.all([
        api.listProjects().catch(() => []),
        api.getAuditLogs(activeOrg.id, 10).catch(() => []),
      ]).then(([projs, logs]) => {
        setProjects(projs);
        setAuditLogs(logs);
        setDataLoading(false);
      });
    }
  }, [activeOrg]);

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-[#0b0f17] flex items-center justify-center font-mono text-xs text-gray-500">
        Loading engineering session...
      </div>
    );
  }

  // Calculate stats
  const totalEnvironments = Array.from(
    new Set(projects.flatMap((p) => p.environments))
  ).length;

  return (
    <div className="min-h-screen bg-[#0b0f17] flex flex-col">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
          {/* Executive Overview Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#1f2937] gap-3">
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold text-gray-100 tracking-tight">
                  Executive Intelligence Overview
                </h1>
                <span className="text-[10px] px-2 py-0.5 rounded bg-[#1a2234] border border-[#1f2937] text-[#10b981] font-mono uppercase">
                  {activeOrg?.name || "Workspace"}
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-1">
                Real-time software consequence tracking, blast radius topologies, and tenant auditing.
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#10b981] text-gray-950 font-medium text-xs hover:bg-[#059669] transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Register Service</span>
              </button>
            </div>
          </div>

          {/* Metric KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="enterprise-card p-4">
              <div className="flex items-center justify-between text-gray-400 mb-2">
                <span className="text-xs font-mono uppercase">Registered Services</span>
                <Boxes className="w-4 h-4 text-[#10b981]" />
              </div>
              <div className="text-2xl font-bold font-mono text-gray-100">
                {dataLoading ? "..." : projects.length}
              </div>
              <div className="text-[11px] text-gray-500 mt-1 flex items-center space-x-1">
                <span>Active microservices in catalog</span>
              </div>
            </div>

            <div className="enterprise-card p-4">
              <div className="flex items-center justify-between text-gray-400 mb-2">
                <span className="text-xs font-mono uppercase">Tracked Environments</span>
                <Layers className="w-4 h-4 text-[#06b6d4]" />
              </div>
              <div className="text-2xl font-bold font-mono text-gray-100">
                {dataLoading ? "..." : totalEnvironments || 1}
              </div>
              <div className="text-[11px] text-gray-500 mt-1">
                Production, Staging & Sandbox
              </div>
            </div>

            <div className="enterprise-card p-4">
              <div className="flex items-center justify-between text-gray-400 mb-2">
                <span className="text-xs font-mono uppercase">Audit Log Stream</span>
                <ShieldCheck className="w-4 h-4 text-[#10b981]" />
              </div>
              <div className="text-2xl font-bold font-mono text-gray-100">
                {dataLoading ? "..." : auditLogs.length}
              </div>
              <div className="text-[11px] text-gray-500 mt-1">
                Immutable security records
              </div>
            </div>

            <div className="enterprise-card p-4">
              <div className="flex items-center justify-between text-gray-400 mb-2">
                <span className="text-xs font-mono uppercase">Topology Engine</span>
                <span className="w-2 h-2 rounded-full bg-[#10b981]" />
              </div>
              <div className="text-sm font-bold text-gray-200 mt-1">
                NetworkX Deterministic
              </div>
              <div className="text-[11px] text-[#10b981] font-mono mt-1">
                READY FOR PHASE 2 AST
              </div>
            </div>
          </div>

          {/* Catalog & Audit Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Services Overview List */}
            <div className="lg:col-span-2 enterprise-card p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Server className="w-4 h-4 text-[#10b981]" />
                  <h3 className="text-sm font-semibold text-gray-100">
                    Registered Microservices & Systems
                  </h3>
                </div>
                <Link
                  href="/projects"
                  className="text-xs text-[#06b6d4] hover:underline flex items-center space-x-1"
                >
                  <span>View All Projects</span>
                  <ArrowUpRight className="w-3 h-3" />
                </Link>
              </div>

              {projects.length === 0 ? (
                <div className="py-8 text-center text-gray-500">
                  <p className="text-xs">No services registered in this organization yet.</p>
                  <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="mt-2 text-xs text-[#10b981] hover:underline font-mono"
                  >
                    + Register first component
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  {projects.slice(0, 5).map((p) => (
                    <div
                      key={p.id}
                      className="p-3 rounded bg-[#0b0f17] border border-[#1f2937] flex items-center justify-between hover:border-gray-700 transition-colors"
                    >
                      <div>
                        <div className="font-semibold text-xs text-gray-200 flex items-center space-x-2">
                          <span>{p.name}</span>
                          <span className="text-[10px] px-1 rounded bg-[#1a2234] text-gray-400 font-mono">
                            {p.slug}
                          </span>
                        </div>
                        <div className="text-[11px] text-gray-500 truncate max-w-md mt-0.5">
                          {p.description || p.repository_url || "Registered service"}
                        </div>
                      </div>
                      <div className="flex items-center space-x-1">
                        {p.environments.slice(0, 2).map((env) => (
                          <span
                            key={env}
                            className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-[#111827] border border-[#1f2937] text-gray-400"
                          >
                            {env}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recent Audit Feed */}
            <div className="enterprise-card p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-[#06b6d4]" />
                  <h3 className="text-sm font-semibold text-gray-100">Live Audit Activity</h3>
                </div>
                <Link
                  href="/audit"
                  className="text-xs text-[#06b6d4] hover:underline flex items-center space-x-1"
                >
                  <span>Full Log</span>
                  <ArrowUpRight className="w-3 h-3" />
                </Link>
              </div>

              {auditLogs.length === 0 ? (
                <div className="py-8 text-center text-gray-500 text-xs">
                  No recent audit records.
                </div>
              ) : (
                <div className="space-y-3 font-mono text-[11px]">
                  {auditLogs.slice(0, 6).map((log) => (
                    <div
                      key={log.id}
                      className="pb-2 border-b border-[#1f2937] last:border-0 flex items-start justify-between"
                    >
                      <div>
                        <div className="text-gray-300 font-medium">{log.action}</div>
                        <div className="text-[10px] text-gray-500 truncate max-w-[180px]">
                          {log.user_email || "System"}
                        </div>
                      </div>
                      <span className="text-[10px] text-gray-500">
                        {new Date(log.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>

      <CreateProjectModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={(p) => setProjects([p, ...projects])}
      />
    </div>
  );
}
