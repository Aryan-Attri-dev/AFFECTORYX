"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Header } from "@/components/navigation/header";
import { Sidebar } from "@/components/navigation/sidebar";
import { api } from "@/lib/api";
import { Project, SimulationReportResponse, RiskLevel, DeploymentVerdict } from "@/types";
import {
  Zap,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Users2,
  FileText,
  Download,
  Copy,
  CheckCircle2,
  AlertOctagon,
  Network,
  RotateCcw,
  Play,
  History,
  CheckSquare,
  Square,
  ExternalLink,
} from "lucide-react";

function ImpactSimulatorContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, activeOrg, isLoading } = useAuth();

  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [history, setHistory] = useState<SimulationReportResponse[]>([]);
  const [currentReport, setCurrentReport] = useState<SimulationReportResponse | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [isDataLoading, setIsDataLoading] = useState(true);

  // Simulation Form State
  const [targetComponent, setTargetComponent] = useState("POST /api/v1/payments");
  const [changeSummary, setChangeSummary] = useState("Deprecate legacy charge token and enforce idempotency key");
  const [analysisId, setAnalysisId] = useState<string | undefined>(undefined);
  const [checklistState, setChecklistState] = useState<Record<number, boolean>>({});
  const [copiedMarkdown, setCopiedMarkdown] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [user, isLoading, router]);

  useEffect(() => {
    if (activeOrg) {
      api.listProjects().then((projs) => {
        setProjects(projs);
        const queryProjectId = searchParams.get("projectId");
        if (queryProjectId && projs.some((p) => p.id === queryProjectId)) {
          setSelectedProjectId(queryProjectId);
        } else if (projs.length > 0) {
          setSelectedProjectId(projs[0].id);
        } else {
          setIsDataLoading(false);
        }
      });
    }
  }, [activeOrg, searchParams]);

  useEffect(() => {
    const qTarget = searchParams.get("targetComponent");
    const qSummary = searchParams.get("summary");
    const qAnalysisId = searchParams.get("analysisId");

    if (qTarget) setTargetComponent(qTarget);
    if (qSummary) setChangeSummary(qSummary);
    if (qAnalysisId) setAnalysisId(qAnalysisId);
  }, [searchParams]);

  const loadReports = async (pId: string) => {
    try {
      const reports = await api.listSimulationReports(pId);
      setHistory(reports);
      if (reports.length > 0 && !currentReport) {
        setCurrentReport(reports[0]);
      }
    } catch (err) {
      console.error("Failed to load simulation reports:", err);
    } finally {
      setIsDataLoading(false);
    }
  };

  useEffect(() => {
    if (selectedProjectId) {
      loadReports(selectedProjectId);
    }
  }, [selectedProjectId]);

  const handleRunSimulation = async () => {
    if (!selectedProjectId) return;
    setIsSimulating(true);
    try {
      const rep = await api.simulateImpact(selectedProjectId, {
        target_component: targetComponent,
        change_summary: changeSummary,
        analysis_id: analysisId || undefined,
      });
      setCurrentReport(rep);
      setHistory([rep, ...history]);
      setChecklistState({});
    } catch (err) {
      alert(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setIsSimulating(false);
    }
  };

  const handleCopyMarkdown = () => {
    if (!currentReport?.markdown_report) return;
    navigator.clipboard.writeText(currentReport.markdown_report);
    setCopiedMarkdown(true);
    setTimeout(() => setCopiedMarkdown(false), 2000);
  };

  const handleDownloadMarkdown = () => {
    if (!currentReport?.markdown_report) return;
    const blob = new Blob([currentReport.markdown_report], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `affactoryx_impact_report_${currentReport.id}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const toggleChecklist = (idx: number) => {
    setChecklistState((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const getVerdictStyle = (verdict: DeploymentVerdict) => {
    switch (verdict) {
      case "SAFE":
        return {
          bg: "bg-emerald-950/20 border-emerald-500/40 text-emerald-300",
          badge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
          icon: ShieldCheck,
          label: "DEPLOYMENT APPROVED — SAFE TO MERGE",
        };
      case "SAFE_WITH_MITIGATION":
        return {
          bg: "bg-amber-950/20 border-amber-500/40 text-amber-300",
          badge: "bg-amber-500/20 text-amber-300 border-amber-500/40",
          icon: AlertTriangle,
          label: "CONDITIONAL RELEASE — MITIGATION MANDATORY",
        };
      case "BLOCKED":
      default:
        return {
          bg: "bg-rose-950/20 border-rose-500/40 text-rose-300",
          badge: "bg-rose-500/20 text-rose-300 border-rose-500/40",
          icon: AlertOctagon,
          label: "DEPLOYMENT BLOCKED — HIGH RISK DETECTED",
        };
    }
  };

  const getRiskStyle = (risk: RiskLevel) => {
    switch (risk) {
      case "CRITICAL":
        return "bg-rose-600 text-white font-bold";
      case "HIGH":
        return "bg-rose-500/20 text-rose-300 border border-rose-500/40";
      case "MEDIUM":
        return "bg-amber-500/20 text-amber-300 border border-amber-500/40";
      case "LOW":
      default:
        return "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40";
    }
  };

  return (
    <div className="min-h-screen bg-[#070b12] text-gray-100 flex flex-col font-sans">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 space-y-6 overflow-y-auto max-w-7xl">
          {/* Top Bar */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#1f2937]">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                  PHASE 3: BLAST RADIUS & IMPACT SIMULATOR
                </span>
                <span className="text-xs text-gray-500 font-mono">Predictive Blast Radius Graph Engine</span>
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-white mt-1">
                Deployment Impact Simulator
              </h1>
              <p className="text-xs text-gray-400 mt-0.5">
                Simulate change propagation across microservices, database schemas, third-party consumers, and SLA-bound enterprise customers before merging code.
              </p>
            </div>

            {/* Scope Selection */}
            <div className="flex items-center gap-3">
              <label className="text-xs text-gray-400 font-medium">Scope:</label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="bg-[#111827] border border-[#1f2937] text-xs text-gray-200 rounded px-3 py-2 focus:outline-none focus:border-amber-500"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.slug})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Simulation Setup Column (4 cols) */}
            <div className="lg:col-span-4 space-y-4">
              <div className="bg-[#0e1420] border border-[#1f2937] rounded-lg p-5 space-y-4">
                <h3 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-amber-400 fill-current" />
                  Simulation Parameters
                </h3>

                <div className="space-y-3">
                  <div>
                    <label className="text-[11px] font-mono text-gray-400">Target Component / Service</label>
                    <input
                      type="text"
                      value={targetComponent}
                      onChange={(e) => setTargetComponent(e.target.value)}
                      placeholder="e.g. POST /api/v1/payments or service:billing"
                      className="w-full bg-[#111827] border border-[#1f2937] text-xs font-mono rounded px-3 py-2 mt-1 text-gray-200 focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-gray-400">Change Description & Context</label>
                    <textarea
                      rows={4}
                      value={changeSummary}
                      onChange={(e) => setChangeSummary(e.target.value)}
                      placeholder="Describe proposed changes or pull request details"
                      className="w-full bg-[#111827] border border-[#1f2937] text-xs rounded px-3 py-2 mt-1 text-gray-200 focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  {analysisId && (
                    <div className="bg-amber-500/5 border border-amber-500/20 p-2.5 rounded text-xs text-amber-300">
                      <span className="font-semibold">Linked Analysis:</span> {analysisId.slice(0, 8)}...
                    </div>
                  )}

                  <button
                    onClick={handleRunSimulation}
                    disabled={isSimulating || !selectedProjectId}
                    className="w-full py-2.5 rounded text-xs font-semibold bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-500 hover:to-rose-500 text-white flex items-center justify-center gap-2 transition-all shadow-md disabled:opacity-50"
                  >
                    {isSimulating ? (
                      <>
                        <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                        Calculating Graph Transitive Closure...
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5 fill-current" />
                        Run Predictive Blast Radius Simulation
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Simulation Run History */}
              <div className="bg-[#0e1420] border border-[#1f2937] rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between text-xs font-semibold text-gray-300">
                  <span className="flex items-center gap-1.5">
                    <History className="w-3.5 h-3.5 text-gray-400" />
                    Simulation Runs ({history.length})
                  </span>
                </div>
                <div className="space-y-1.5 max-h-56 overflow-y-auto">
                  {history.map((r) => {
                    const vStyle = getVerdictStyle(r.verdict);
                    const VIcon = vStyle.icon;
                    return (
                      <div
                        key={r.id}
                        onClick={() => setCurrentReport(r)}
                        className={`p-2.5 rounded text-xs cursor-pointer border transition-colors flex items-center justify-between ${
                          currentReport?.id === r.id
                            ? "bg-amber-500/10 border-amber-500/40 text-gray-200"
                            : "bg-[#111827]/40 border-[#1f2937] text-gray-400 hover:bg-[#111827]"
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate">
                          <VIcon className="w-3.5 h-3.5 shrink-0" />
                          <span className="truncate font-medium">{r.target_component_name}</span>
                        </div>
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono shrink-0 ${vStyle.badge}`}>
                          {r.verdict}
                        </span>
                      </div>
                    );
                  })}
                  {history.length === 0 && (
                    <p className="text-xs text-gray-500 text-center py-4">No simulations executed yet.</p>
                  )}
                </div>
              </div>
            </div>

            {/* Results Column (8 cols) */}
            <div className="lg:col-span-8 space-y-4">
              {currentReport ? (
                <div className="space-y-4">
                  {/* Executive Deployment Safety Verdict Card */}
                  {(() => {
                    const vStyle = getVerdictStyle(currentReport.verdict);
                    const VIcon = vStyle.icon;
                    return (
                      <div className={`border rounded-lg p-5 ${vStyle.bg} border-l-4 space-y-3`}>
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="flex items-center gap-2.5">
                            <VIcon className="w-6 h-6" />
                            <div>
                              <div className="text-[10px] font-mono uppercase tracking-wider font-bold">
                                EXECUTIVE VERDICT
                              </div>
                              <h2 className="text-base font-bold">{vStyle.label}</h2>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-1 rounded text-xs font-mono font-bold ${getRiskStyle(currentReport.risk_level)}`}>
                              RISK: {currentReport.risk_level}
                            </span>
                            <span className="text-xs font-mono text-gray-400">
                              {new Date(currentReport.created_at).toLocaleTimeString()}
                            </span>
                          </div>
                        </div>

                        <p className="text-xs text-gray-200 leading-relaxed font-sans">
                          {currentReport.summary}
                        </p>

                        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-[#1f2937]/50 text-xs font-mono">
                          <div>
                            <span className="text-gray-400">Target:</span>{" "}
                            <span className="font-bold text-white">{currentReport.target_component_name}</span>
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={handleCopyMarkdown}
                              className="px-2.5 py-1 bg-[#111827] hover:bg-[#1a2333] border border-[#26334d] text-gray-300 rounded text-xs flex items-center gap-1.5 transition-colors"
                            >
                              <Copy className="w-3 h-3" />
                              {copiedMarkdown ? "Copied!" : "Copy Report"}
                            </button>
                            <button
                              onClick={handleDownloadMarkdown}
                              className="px-2.5 py-1 bg-amber-600 hover:bg-amber-500 text-white rounded text-xs flex items-center gap-1.5 font-sans font-medium transition-colors"
                            >
                              <Download className="w-3 h-3" />
                              Export Markdown
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })()}

                  {/* Blast Radius & Dependencies Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Directly Affected Services */}
                    <div className="bg-[#0e1420] border border-[#1f2937] rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                          <Network className="w-3.5 h-3.5 text-amber-400" />
                          Direct Downstream Services ({currentReport.directly_affected_services.length})
                        </h4>
                      </div>
                      <div className="space-y-1.5 max-h-36 overflow-y-auto">
                        {currentReport.directly_affected_services.map((svc, i) => (
                          <div key={i} className="px-2.5 py-1.5 rounded bg-[#111827] border border-[#1f2937] text-xs font-mono text-gray-200">
                            {svc}
                          </div>
                        ))}
                        {currentReport.directly_affected_services.length === 0 && (
                          <p className="text-xs text-gray-500 py-2">No direct downstream services affected.</p>
                        )}
                      </div>
                    </div>

                    {/* Transitive Blast Radius */}
                    <div className="bg-[#0e1420] border border-[#1f2937] rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                          <Network className="w-3.5 h-3.5 text-rose-400" />
                          Transitive Blast Radius Services ({currentReport.transitive_affected_services.length})
                        </h4>
                      </div>
                      <div className="space-y-1.5 max-h-36 overflow-y-auto">
                        {currentReport.transitive_affected_services.map((svc, i) => (
                          <div key={i} className="px-2.5 py-1.5 rounded bg-[#111827] border border-[#1f2937] text-xs font-mono text-rose-300">
                            {svc}
                          </div>
                        ))}
                        {currentReport.transitive_affected_services.length === 0 && (
                          <p className="text-xs text-gray-500 py-2">No transitive blast radius detected.</p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* SPOFs Alert if any */}
                  {currentReport.spof_identified.length > 0 && (
                    <div className="bg-rose-950/20 border border-rose-900/60 rounded-lg p-4 space-y-2">
                      <div className="flex items-center gap-2 text-rose-400 font-semibold text-xs">
                        <AlertOctagon className="w-4 h-4" />
                        Single Points of Failure (SPOFs) In Blast Path:
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {currentReport.spof_identified.map((spof, idx) => (
                          <span key={idx} className="px-2 py-1 rounded bg-rose-500/20 text-rose-200 text-xs font-mono border border-rose-500/40">
                            {spof}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Impacted Enterprise Customers */}
                  <div className="bg-[#0e1420] border border-[#1f2937] rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                        <Users2 className="w-3.5 h-3.5 text-indigo-400" />
                        Impacted Enterprise Customers & SLA Exposure ({currentReport.affected_customers.length})
                      </h4>
                    </div>

                    <div className="space-y-2">
                      {currentReport.affected_customers.map((c, i) => (
                        <div
                          key={i}
                          className="p-3 rounded-lg bg-[#111827] border border-[#1f2937] flex flex-col md:flex-row md:items-center justify-between gap-2 text-xs"
                        >
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-white text-sm">{c.customer_name}</span>
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-indigo-500/20 text-indigo-300 font-semibold">
                                {c.tier}
                              </span>
                              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-[#1c2438] text-gray-300">
                                SLA: {c.contract_sla}
                              </span>
                            </div>
                            <div className="text-[11px] text-gray-400 font-mono mt-1">
                              Impacted Workflows: {c.impacted_workflows.join(", ") || "All critical workflows"}
                            </div>
                          </div>
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30 self-start md:self-auto">
                            SLA BREACH RISK
                          </span>
                        </div>
                      ))}

                      {currentReport.affected_customers.length === 0 && (
                        <p className="text-xs text-gray-500 text-center py-4">No external enterprise customer contracts affected.</p>
                      )}
                    </div>
                  </div>

                  {/* Pre-Deployment Verification Checklist */}
                  <div className="bg-[#0e1420] border border-[#1f2937] rounded-lg p-4 space-y-3">
                    <h4 className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      Mandatory Pre-Deployment Verification Checklist
                    </h4>
                    <div className="space-y-2">
                      {currentReport.verification_checklist.map((item, idx) => {
                        const isChecked = !!checklistState[idx];
                        return (
                          <div
                            key={idx}
                            onClick={() => toggleChecklist(idx)}
                            className={`p-2.5 rounded text-xs border flex items-start gap-2.5 cursor-pointer transition-colors ${
                              isChecked
                                ? "bg-emerald-950/20 border-emerald-500/40 text-emerald-200"
                                : "bg-[#111827] border-[#1f2937] text-gray-300 hover:bg-[#151e30]"
                            }`}
                          >
                            {isChecked ? (
                              <CheckSquare className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                            ) : (
                              <Square className="w-4 h-4 text-gray-500 shrink-0 mt-0.5" />
                            )}
                            <span className={isChecked ? "line-through text-gray-400" : ""}>{item}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-[#0e1420] border border-[#1f2937] rounded-lg p-12 text-center space-y-3">
                  <Zap className="w-10 h-10 text-gray-600 mx-auto" />
                  <h3 className="text-sm font-semibold text-gray-300">No Simulation Executed</h3>
                  <p className="text-xs text-gray-500 max-w-sm mx-auto">
                    Configure a target component on the left or select a previous run from history to inspect the blast radius report.
                  </p>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default function ImpactSimulatorPage() {
  return (
    <React.Suspense
      fallback={
        <div className="min-h-screen bg-[#070b12] text-gray-400 p-8 flex items-center justify-center font-mono text-xs">
          Loading Impact Simulator Engine...
        </div>
      }
    >
      <ImpactSimulatorContent />
    </React.Suspense>
  );
}
