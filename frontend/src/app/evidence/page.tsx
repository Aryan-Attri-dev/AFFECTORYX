"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Header } from "@/components/navigation/header";
import { Sidebar } from "@/components/navigation/sidebar";
import { api } from "@/lib/api";
import { Project, EvidenceRecord, EvidenceConfidence, EvidenceSourceKind } from "@/types";
import {
  FileCheck2,
  Filter,
  CheckCircle2,
  HelpCircle,
  AlertTriangle,
  Code2,
  Database,
  FileCode2,
  Users2,
  RefreshCw,
} from "lucide-react";

export default function EvidenceRegistryPage() {
  const router = useRouter();
  const { user, activeOrg, isLoading } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [records, setRecords] = useState<EvidenceRecord[]>([]);
  const [confidenceFilter, setConfidenceFilter] = useState<string>("all");
  const [sourceFilter, setSourceFilter] = useState<string>("all");
  const [isDataLoading, setIsDataLoading] = useState(true);

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

  const fetchEvidence = async () => {
    if (!selectedProjectId) return;
    setIsDataLoading(true);
    try {
      const conf = confidenceFilter !== "all" ? (confidenceFilter as EvidenceConfidence) : undefined;
      const src = sourceFilter !== "all" ? (sourceFilter as EvidenceSourceKind) : undefined;
      const data = await api.listEvidence(selectedProjectId, conf, src);
      setRecords(data);
    } catch (err) {
      console.error("Failed to load evidence records:", err);
    } finally {
      setIsDataLoading(false);
    }
  };

  useEffect(() => {
    if (selectedProjectId) {
      fetchEvidence();
    }
  }, [selectedProjectId, confidenceFilter, sourceFilter]);

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-[#0b0f17] flex items-center justify-center font-mono text-xs text-gray-500">
        Loading evidence registry...
      </div>
    );
  }

  const getSourceIcon = (kind: string) => {
    switch (kind) {
      case "openapi_spec":
        return <FileCode2 className="w-3.5 h-3.5 text-[#10b981]" />;
      case "code_ast":
        return <Code2 className="w-3.5 h-3.5 text-[#06b6d4]" />;
      case "sql_migration":
        return <Database className="w-3.5 h-3.5 text-amber-400" />;
      case "customer_contract":
        return <Users2 className="w-3.5 h-3.5 text-rose-400" />;
      default:
        return <FileCheck2 className="w-3.5 h-3.5 text-gray-400" />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f17] flex flex-col">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-5">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#1f2937] gap-3">
            <div>
              <div className="flex items-center space-x-2">
                <FileCheck2 className="w-5 h-5 text-[#10b981]" />
                <h1 className="text-xl font-bold text-gray-100 tracking-tight">
                  Evidence Provenance Registry
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
                Verifiable, immutable proofs supporting each dependency edge. Distinguishes confirmed contracts, static AST inferences, and unknown links.
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={fetchEvidence}
                className="p-1.5 rounded hover:bg-[#111827] border border-[#1f2937] text-gray-400 hover:text-gray-200 transition-colors"
                title="Refresh"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isDataLoading ? "animate-spin" : ""}`} />
              </button>
            </div>
          </div>

          {/* Filters Bar */}
          <div className="flex flex-wrap items-center gap-3 p-3 rounded enterprise-card bg-[#0d131f] text-xs">
            <div className="flex items-center space-x-1.5 text-gray-400">
              <Filter className="w-3.5 h-3.5" />
              <span className="font-mono text-[11px] uppercase">Filter Provenance:</span>
            </div>

            <select
              value={confidenceFilter}
              onChange={(e) => setConfidenceFilter(e.target.value)}
              className="px-2.5 py-1 rounded bg-[#111827] border border-[#1f2937] text-gray-200 font-mono text-xs focus:outline-none"
            >
              <option value="all">All Confidence Levels</option>
              <option value="confirmed">Confirmed (Machine-Verified)</option>
              <option value="inferred">Inferred (AST / Call Heuristics)</option>
              <option value="unknown">Unknown (Ambiguous / Cautionary)</option>
            </select>

            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="px-2.5 py-1 rounded bg-[#111827] border border-[#1f2937] text-gray-200 font-mono text-xs focus:outline-none"
            >
              <option value="all">All Evidence Sources</option>
              <option value="openapi_spec">OpenAPI v3 Specifications</option>
              <option value="code_ast">Code Callsite AST</option>
              <option value="sql_migration">SQL Migration DDL</option>
              <option value="customer_contract">Customer SLA Contracts</option>
            </select>
          </div>

          {/* Evidence Registry Table */}
          <div className="enterprise-card overflow-hidden">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="table-header text-gray-400 font-mono uppercase text-[10px] tracking-wider">
                  <th className="py-2.5 px-4">Confidence Level</th>
                  <th className="py-2.5 px-4">Source Kind</th>
                  <th className="py-2.5 px-4">Evidence Summary</th>
                  <th className="py-2.5 px-4">Verifiable Code / Schema Fragment</th>
                  <th className="py-2.5 px-4">Recorded At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1f2937] text-gray-200">
                {isDataLoading ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-gray-500 font-mono">
                      Querying evidence provenance registry...
                    </td>
                  </tr>
                ) : records.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-gray-500">
                      <FileCheck2 className="w-8 h-8 mx-auto mb-2 text-gray-600" />
                      <p className="text-sm font-medium text-gray-400">No Evidence Records Found</p>
                      <p className="text-xs text-gray-600 mt-1">
                        Ingest an OpenAPI specification or scan repository callsites to establish evidence.
                      </p>
                    </td>
                  </tr>
                ) : (
                  records.map((r) => (
                    <tr key={r.id} className="hover:bg-[#151c2a] transition-colors">
                      <td className="py-3 px-4 whitespace-nowrap">
                        {r.confidence === "confirmed" && (
                          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-emerald-950/40 border border-emerald-800 text-emerald-400">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Confirmed</span>
                          </span>
                        )}
                        {r.confidence === "inferred" && (
                          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-cyan-950/40 border border-cyan-800 text-cyan-400">
                            <HelpCircle className="w-3 h-3" />
                            <span>Inferred</span>
                          </span>
                        )}
                        {r.confidence === "unknown" && (
                          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-amber-950/40 border border-amber-800 text-amber-400">
                            <AlertTriangle className="w-3 h-3" />
                            <span>Unknown (Unsafe)</span>
                          </span>
                        )}
                      </td>

                      <td className="py-3 px-4 font-mono text-[11px] whitespace-nowrap">
                        <div className="flex items-center space-x-1.5">
                          {getSourceIcon(r.source_kind)}
                          <span className="capitalize">{r.source_kind.replace("_", " ")}</span>
                        </div>
                      </td>

                      <td className="py-3 px-4 font-medium text-gray-200">
                        {r.summary}
                      </td>

                      <td className="py-3 px-4 font-mono text-[11px] text-gray-400 max-w-sm truncate">
                        {r.raw_snippet ? (
                          <code className="px-1.5 py-0.5 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-300">
                            {r.raw_snippet}
                          </code>
                        ) : (
                          "—"
                        )}
                      </td>

                      <td className="py-3 px-4 text-gray-500 font-mono text-[11px] whitespace-nowrap">
                        {new Date(r.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </main>
      </div>
    </div>
  );
}
