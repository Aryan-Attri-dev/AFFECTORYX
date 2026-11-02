"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Header } from "@/components/navigation/header";
import { Sidebar } from "@/components/navigation/sidebar";
import { TopologyCanvas } from "@/components/graph/topology-canvas";
import { IngestModal } from "@/components/graph/ingest-modal";
import { api } from "@/lib/api";
import { Project, TopologyGraphResponse } from "@/types";
import {
  GitFork,
  Sparkles,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  ShieldAlert,
} from "lucide-react";

export default function DependencyGraphPage() {
  const router = useRouter();
  const { user, activeOrg, isLoading } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [topology, setTopology] = useState<TopologyGraphResponse | null>(null);
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [isIngestModalOpen, setIsIngestModalOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [user, isLoading, router]);

  useEffect(() => {
    if (activeOrg) {
      api.listProjects().then((projs) => {
        setProjects(projs);
        if (projs.length > 0) {
          setSelectedProjectId(projs[0].id);
        } else {
          setIsDataLoading(false);
        }
      });
    }
  }, [activeOrg]);

  const fetchTopology = async (pId: string) => {
    if (!pId) return;
    setIsDataLoading(true);
    try {
      const data = await api.getTopology(pId);
      setTopology(data);
    } catch (err) {
      console.error("Failed to load topology:", err);
    } finally {
      setIsDataLoading(false);
    }
  };

  useEffect(() => {
    if (selectedProjectId) {
      fetchTopology(selectedProjectId);
    }
  }, [selectedProjectId]);

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-[#0b0f17] flex items-center justify-center font-mono text-xs text-gray-500">
        Loading topology engine...
      </div>
    );
  }

  const metrics = topology?.metrics;

  return (
    <div className="min-h-screen bg-[#0b0f17] flex flex-col">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-5">
          {/* Header & Controls */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#1f2937] gap-3">
            <div>
              <div className="flex items-center space-x-2">
                <GitFork className="w-5 h-5 text-[#10b981]" />
                <h1 className="text-xl font-bold text-gray-100 tracking-tight">
                  Evidence-Based Dependency Topology
                </h1>
                {projects.length > 0 && (
                  <select
                    value={selectedProjectId}
                    onChange={(e) => setSelectedProjectId(e.target.value)}
                    className="ml-2 px-2.5 py-1 text-xs font-mono rounded bg-[#111827] border border-[#1f2937] text-gray-200 focus:outline-none focus:border-[#10b981]"
                  >
                    {projects.map((p) => (
                      <option key={p.id} value={p.id}>
                        Project: {p.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>
              <p className="text-xs text-gray-400 mt-1">
                Directed graph connecting services, endpoints, schemas, database tables, and contracted customers.
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => fetchTopology(selectedProjectId)}
                className="p-1.5 rounded hover:bg-[#111827] border border-[#1f2937] text-gray-400 hover:text-gray-200 transition-colors"
                title="Refresh Graph"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isDataLoading ? "animate-spin" : ""}`} />
              </button>
              <button
                onClick={() => setIsIngestModalOpen(true)}
                disabled={!selectedProjectId}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#10b981] text-gray-950 font-medium text-xs hover:bg-[#059669] transition-colors disabled:opacity-50"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Ingest Evidence</span>
              </button>
            </div>
          </div>

          {/* Topology Metric Badges */}
          {metrics && (
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 font-mono text-xs">
              <div className="enterprise-card p-3">
                <div className="text-gray-500 text-[10px] uppercase">Total Components</div>
                <div className="text-lg font-bold text-gray-100">{metrics.total_nodes}</div>
              </div>
              <div className="enterprise-card p-3">
                <div className="text-gray-500 text-[10px] uppercase">Dependency Edges</div>
                <div className="text-lg font-bold text-gray-100">{metrics.total_edges}</div>
              </div>
              <div className="enterprise-card p-3 border-[#10b981]/30">
                <div className="text-[#10b981] text-[10px] uppercase flex items-center space-x-1">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Confirmed</span>
                </div>
                <div className="text-lg font-bold text-[#10b981]">{metrics.confirmed_edges}</div>
              </div>
              <div className="enterprise-card p-3 border-[#06b6d4]/30">
                <div className="text-[#06b6d4] text-[10px] uppercase flex items-center space-x-1">
                  <HelpCircle className="w-3 h-3" />
                  <span>Inferred</span>
                </div>
                <div className="text-lg font-bold text-[#06b6d4]">{metrics.inferred_edges}</div>
              </div>
              <div className="enterprise-card p-3 border-amber-600/30">
                <div className="text-amber-400 text-[10px] uppercase flex items-center space-x-1">
                  <AlertTriangle className="w-3 h-3" />
                  <span>Unknown Risk</span>
                </div>
                <div className="text-lg font-bold text-amber-400">{metrics.unknown_edges}</div>
              </div>
              <div className="enterprise-card p-3 border-rose-600/30">
                <div className="text-rose-400 text-[10px] uppercase flex items-center space-x-1">
                  <ShieldAlert className="w-3 h-3" />
                  <span>SPOF Hotspots</span>
                </div>
                <div className="text-sm font-bold text-rose-300 truncate mt-1">
                  {metrics.spof_candidates.length > 0 ? metrics.spof_candidates.join(", ") : "None Detected"}
                </div>
              </div>
            </div>
          )}

          {/* Interactive Canvas */}
          {selectedProjectId ? (
            <TopologyCanvas
              projectId={selectedProjectId}
              nodes={topology?.nodes || []}
              edges={topology?.edges || []}
              onRefresh={() => fetchTopology(selectedProjectId)}
            />
          ) : (
            <div className="enterprise-card p-12 text-center text-gray-500 text-xs">
              Please register or select a project first to view its topology.
            </div>
          )}
        </main>
      </div>

      {selectedProjectId && (
        <IngestModal
          projectId={selectedProjectId}
          isOpen={isIngestModalOpen}
          onClose={() => setIsIngestModalOpen(false)}
          onSuccess={() => fetchTopology(selectedProjectId)}
        />
      )}
    </div>
  );
}
