"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Header } from "@/components/navigation/header";
import { Sidebar } from "@/components/navigation/sidebar";
import { api } from "@/lib/api";
import { Project, ChangeAnalysisResponse, ChangeFinding } from "@/types";
import {
  GitPullRequest,
  AlertOctagon,
  CheckCircle2,
  AlertTriangle,
  FileCode2,
  Database,
  ArrowRight,
  Zap,
  Play,
  RotateCcw,
  Clock,
  History,
  ShieldAlert,
  HelpCircle,
  Copy,
} from "lucide-react";

const SAMPLE_BASE_OPENAPI = JSON.stringify(
  {
    openapi: "3.0.0",
    info: { title: "Payment Gateway API", version: "1.0.0" },
    paths: {
      "/api/v1/payments": {
        get: {
          summary: "List payments",
          parameters: [
            { name: "status", in: "query", required: false, schema: { type: "string" } },
            { name: "limit", in: "query", required: false, schema: { type: "integer" } },
          ],
          responses: {
            "200": {
              description: "OK",
              content: {
                "application/json": {
                  schema: {
                    type: "object",
                    properties: {
                      payments: { type: "array" },
                      total: { type: "integer" },
                    },
                  },
                },
              },
            },
          },
        },
        post: {
          summary: "Create payment",
          requestBody: {
            required: true,
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  required: ["amount", "currency"],
                  properties: {
                    amount: { type: "number" },
                    currency: { type: "string" },
                    customer_id: { type: "string" },
                  },
                },
              },
            },
          },
          responses: {
            "201": {
              description: "Created",
            },
          },
        },
      },
    },
  },
  null,
  2
);

const SAMPLE_BREAKING_OPENAPI = JSON.stringify(
  {
    openapi: "3.0.0",
    info: { title: "Payment Gateway API", version: "2.0.0" },
    paths: {
      "/api/v1/payments": {
        // GET method removed completely!
        post: {
          summary: "Create payment v2",
          requestBody: {
            required: true,
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  // Added mandatory idempotency_key without default -> Breaking!
                  required: ["amount", "currency", "idempotency_key"],
                  properties: {
                    amount: { type: "number" },
                    currency: { type: "string" },
                    customer_id: { type: "string" },
                    idempotency_key: { type: "string" },
                  },
                },
              },
            },
          },
          responses: {
            "200": {
              // Status code 201 changed to 200
              description: "Success",
            },
          },
        },
      },
    },
  },
  null,
  2
);

const SAMPLE_BREAKING_SQL = `-- Proposed Migration: v2.4_drop_legacy_billing.sql
ALTER TABLE payments DROP COLUMN legacy_charge_token;
ALTER TABLE invoices ALTER COLUMN status TYPE integer;
ALTER TABLE accounts ADD COLUMN tax_jurisdiction_code varchar(32) NOT NULL;
DROP TABLE IF EXISTS customer_legacy_tokens;
`;

export default function ChangeAnalyzerPage() {
  const router = useRouter();
  const { user, activeOrg, isLoading } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"openapi" | "sql">("openapi");
  const [history, setHistory] = useState<ChangeAnalysisResponse[]>([]);
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentAnalysis, setCurrentAnalysis] = useState<ChangeAnalysisResponse | null>(null);

  // OpenAPI Form State
  const [apiTitle, setApiTitle] = useState("Payment API v2 Breaking Refactor");
  const [baseSpec, setBaseSpec] = useState(SAMPLE_BASE_OPENAPI);
  const [targetSpec, setTargetSpec] = useState(SAMPLE_BREAKING_OPENAPI);
  const [baseVersion, setBaseVersion] = useState("v1.0.0");
  const [targetVersion, setTargetVersion] = useState("v2.0.0");

  // SQL Form State
  const [sqlTitle, setSqlTitle] = useState("Billing Schema v2 Migration");
  const [migrationFilename, setMigrationFilename] = useState("v2.4_drop_legacy_billing.sql");
  const [sqlContent, setSqlContent] = useState(SAMPLE_BREAKING_SQL);

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

  const loadHistory = async (pId: string) => {
    try {
      const data = await api.listAnalyses(pId);
      setHistory(data);
      if (data.length > 0 && !currentAnalysis) {
        setCurrentAnalysis(data[0]);
      }
    } catch (err) {
      console.error("Failed to load analyses:", err);
    } finally {
      setIsDataLoading(false);
    }
  };

  useEffect(() => {
    if (selectedProjectId) {
      loadHistory(selectedProjectId);
    }
  }, [selectedProjectId]);

  const handleRunOpenAPIAnalysis = async () => {
    if (!selectedProjectId) return;
    setIsAnalyzing(true);
    try {
      const res = await api.compareOpenAPI(selectedProjectId, {
        title: apiTitle,
        base_spec: baseSpec,
        target_spec: targetSpec,
        base_version: baseVersion,
        target_version: targetVersion,
      });
      setCurrentAnalysis(res);
      setHistory([res, ...history]);
    } catch (err) {
      alert(err instanceof Error ? err.message : "OpenAPI analysis failed");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleRunSQLAnalysis = async () => {
    if (!selectedProjectId) return;
    setIsAnalyzing(true);
    try {
      const res = await api.compareSQL(selectedProjectId, {
        title: sqlTitle,
        migration_filename: migrationFilename,
        sql_content: sqlContent,
      });
      setCurrentAnalysis(res);
      setHistory([res, ...history]);
    } catch (err) {
      alert(err instanceof Error ? err.message : "SQL analysis failed");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const navigateToSimulator = (finding?: ChangeFinding) => {
    if (!selectedProjectId) return;
    const targetComp = finding ? finding.target : currentAnalysis?.findings[0]?.target || "service:payments";
    const summary = currentAnalysis ? `Simulating impact of ${currentAnalysis.title}` : "Simulated change impact";
    const analysisId = currentAnalysis?.id || "";
    router.push(
      `/simulator?projectId=${selectedProjectId}&analysisId=${analysisId}&targetComponent=${encodeURIComponent(
        targetComp
      )}&summary=${encodeURIComponent(summary)}`
    );
  };

  return (
    <div className="min-h-screen bg-[#070b12] text-gray-100 flex flex-col font-sans">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 space-y-6 overflow-y-auto max-w-7xl">
          {/* Header Bar */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#1f2937]">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">
                  PHASE 3: CHANGE ANALYZER
                </span>
                <span className="text-xs text-gray-500 font-mono">AST & Schema Diff Engine</span>
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-white mt-1">
                Deterministic Change Analyzer
              </h1>
              <p className="text-xs text-gray-400 mt-0.5">
                Detect breaking schema changes, deleted endpoints, altered contracts, and destructive SQL migrations before merge.
              </p>
            </div>

            {/* Project Selector */}
            <div className="flex items-center gap-3">
              <label className="text-xs text-gray-400 font-medium">Scope:</label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="bg-[#111827] border border-[#1f2937] text-xs text-gray-200 rounded px-3 py-2 focus:outline-none focus:border-rose-500"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.slug})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Tab Selector */}
          <div className="flex items-center justify-between border-b border-[#1f2937]">
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab("openapi")}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-all ${
                  activeTab === "openapi"
                    ? "border-rose-500 text-rose-400 bg-rose-500/5"
                    : "border-transparent text-gray-400 hover:text-gray-200"
                }`}
              >
                <FileCode2 className="w-3.5 h-3.5" />
                OpenAPI Specification Diff
              </button>
              <button
                onClick={() => setActiveTab("sql")}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-all ${
                  activeTab === "sql"
                    ? "border-rose-500 text-rose-400 bg-rose-500/5"
                    : "border-transparent text-gray-400 hover:text-gray-200"
                }`}
              >
                <Database className="w-3.5 h-3.5" />
                SQL Migration AST Analyzer
              </button>
            </div>

            {currentAnalysis && (
              <button
                onClick={() => navigateToSimulator()}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-gradient-to-r from-amber-600 to-rose-600 text-white shadow-lg hover:brightness-110 transition-all"
              >
                <Zap className="w-3.5 h-3.5 fill-current" />
                Simulate Blast Radius
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Input & Config Column (7 cols) */}
            <div className="lg:col-span-7 space-y-4">
              {activeTab === "openapi" ? (
                <div className="bg-[#0e1420] border border-[#1f2937] rounded-lg p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
                      <FileCode2 className="w-4 h-4 text-rose-400" />
                      OpenAPI Specification Comparison
                    </h3>
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          setBaseSpec(SAMPLE_BASE_OPENAPI);
                          setTargetSpec(SAMPLE_BREAKING_OPENAPI);
                        }}
                        className="text-[11px] font-mono text-gray-400 hover:text-gray-200 bg-[#161f30] px-2 py-1 rounded border border-[#26334d]"
                      >
                        Reset Sample
                      </button>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="text-[11px] font-mono text-gray-400">Analysis Title</label>
                      <input
                        type="text"
                        value={apiTitle}
                        onChange={(e) => setApiTitle(e.target.value)}
                        className="w-full bg-[#111827] border border-[#1f2937] text-xs rounded px-3 py-2 mt-1 text-gray-200 focus:outline-none focus:border-rose-500"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[11px] font-mono text-gray-400">Base Version</label>
                        <input
                          type="text"
                          value={baseVersion}
                          onChange={(e) => setBaseVersion(e.target.value)}
                          className="w-full bg-[#111827] border border-[#1f2937] text-xs rounded px-3 py-1.5 mt-1 text-gray-200 font-mono"
                        />
                      </div>
                      <div>
                        <label className="text-[11px] font-mono text-gray-400">Target Version</label>
                        <input
                          type="text"
                          value={targetVersion}
                          onChange={(e) => setTargetVersion(e.target.value)}
                          className="w-full bg-[#111827] border border-[#1f2937] text-xs rounded px-3 py-1.5 mt-1 text-gray-200 font-mono"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <label className="text-[11px] font-mono text-gray-400">Base OpenAPI Spec (JSON)</label>
                        </div>
                        <textarea
                          rows={12}
                          value={baseSpec}
                          onChange={(e) => setBaseSpec(e.target.value)}
                          className="w-full bg-[#0a0f18] border border-[#1f2937] text-[11px] font-mono rounded p-2.5 text-gray-300 focus:outline-none focus:border-rose-500"
                        />
                      </div>
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <label className="text-[11px] font-mono text-rose-300">Target OpenAPI Spec (Proposed)</label>
                        </div>
                        <textarea
                          rows={12}
                          value={targetSpec}
                          onChange={(e) => setTargetSpec(e.target.value)}
                          className="w-full bg-[#0a0f18] border border-rose-900/40 text-[11px] font-mono rounded p-2.5 text-gray-300 focus:outline-none focus:border-rose-500"
                        />
                      </div>
                    </div>

                    <button
                      onClick={handleRunOpenAPIAnalysis}
                      disabled={isAnalyzing || !selectedProjectId}
                      className="w-full py-2.5 rounded text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white flex items-center justify-center gap-2 transition-all shadow-md disabled:opacity-50"
                    >
                      {isAnalyzing ? (
                        <>
                          <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                          Analyzing AST & Schema Contracts...
                        </>
                      ) : (
                        <>
                          <Play className="w-3.5 h-3.5 fill-current" />
                          Execute OpenAPI Change Analysis
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="bg-[#0e1420] border border-[#1f2937] rounded-lg p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
                      <Database className="w-4 h-4 text-amber-400" />
                      SQL Migration AST Verification
                    </h3>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="text-[11px] font-mono text-gray-400">Migration Title</label>
                      <input
                        type="text"
                        value={sqlTitle}
                        onChange={(e) => setSqlTitle(e.target.value)}
                        className="w-full bg-[#111827] border border-[#1f2937] text-xs rounded px-3 py-2 mt-1 text-gray-200"
                      />
                    </div>

                    <div>
                      <label className="text-[11px] font-mono text-gray-400">Migration Filename</label>
                      <input
                        type="text"
                        value={migrationFilename}
                        onChange={(e) => setMigrationFilename(e.target.value)}
                        className="w-full bg-[#111827] border border-[#1f2937] text-xs rounded px-3 py-1.5 mt-1 text-gray-200 font-mono"
                      />
                    </div>

                    <div>
                      <label className="text-[11px] font-mono text-gray-400">Proposed SQL DDL Statements</label>
                      <textarea
                        rows={12}
                        value={sqlContent}
                        onChange={(e) => setSqlContent(e.target.value)}
                        className="w-full bg-[#0a0f18] border border-[#1f2937] text-[11px] font-mono rounded p-2.5 text-gray-300 focus:outline-none focus:border-amber-500 mt-1"
                      />
                    </div>

                    <button
                      onClick={handleRunSQLAnalysis}
                      disabled={isAnalyzing || !selectedProjectId}
                      className="w-full py-2.5 rounded text-xs font-semibold bg-amber-600 hover:bg-amber-500 text-white flex items-center justify-center gap-2 transition-all shadow-md disabled:opacity-50"
                    >
                      {isAnalyzing ? (
                        <>
                          <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                          Inspecting DDL AST & Destructive Statements...
                        </>
                      ) : (
                        <>
                          <Play className="w-3.5 h-3.5 fill-current" />
                          Execute SQL Migration Analysis
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Recent Analyses History */}
              <div className="bg-[#0e1420] border border-[#1f2937] rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between text-xs font-semibold text-gray-300">
                  <span className="flex items-center gap-1.5">
                    <History className="w-3.5 h-3.5 text-gray-400" />
                    Recent Analyses ({history.length})
                  </span>
                </div>
                <div className="space-y-1.5 max-h-48 overflow-y-auto">
                  {history.map((h) => (
                    <div
                      key={h.id}
                      onClick={() => setCurrentAnalysis(h)}
                      className={`p-2 rounded text-xs cursor-pointer border transition-colors flex items-center justify-between ${
                        currentAnalysis?.id === h.id
                          ? "bg-rose-500/10 border-rose-500/40 text-gray-200"
                          : "bg-[#111827]/40 border-[#1f2937] text-gray-400 hover:bg-[#111827]"
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        {h.analysis_type === "OPENAPI" ? (
                          <FileCode2 className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                        ) : (
                          <Database className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                        )}
                        <span className="truncate font-medium">{h.title}</span>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {h.breaking_count > 0 ? (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-rose-500/20 text-rose-300 font-semibold">
                            {h.breaking_count} breaking
                          </span>
                        ) : (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-300">
                            Safe
                          </span>
                        )}
                        <span className="text-[10px] font-mono text-gray-500">
                          {new Date(h.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>
                    </div>
                  ))}
                  {history.length === 0 && (
                    <p className="text-xs text-gray-500 text-center py-4">No analyses run yet for this project.</p>
                  )}
                </div>
              </div>
            </div>

            {/* Findings & Output Column (5 cols) */}
            <div className="lg:col-span-5 space-y-4">
              {currentAnalysis ? (
                <div className="bg-[#0e1420] border border-[#1f2937] rounded-lg p-5 space-y-4">
                  {/* Summary Bar */}
                  <div className="border-b border-[#1f2937] pb-4">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-gray-400">
                        ANALYSIS REPORT
                      </span>
                      <span className="text-[10px] font-mono text-gray-500">
                        {new Date(currentAnalysis.created_at).toLocaleString()}
                      </span>
                    </div>
                    <h2 className="text-base font-bold text-white mt-1">{currentAnalysis.title}</h2>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-[11px] font-mono text-gray-400">
                        {currentAnalysis.base_version} &rarr; {currentAnalysis.target_version}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-3 mt-4">
                      <div className="bg-[#111827] border border-rose-900/40 rounded p-3">
                        <div className="text-[10px] font-mono text-rose-400 uppercase">Breaking Changes</div>
                        <div className="text-2xl font-bold text-rose-300 font-mono mt-0.5">
                          {currentAnalysis.breaking_count}
                        </div>
                      </div>
                      <div className="bg-[#111827] border border-emerald-900/40 rounded p-3">
                        <div className="text-[10px] font-mono text-emerald-400 uppercase">Non-Breaking</div>
                        <div className="text-2xl font-bold text-emerald-300 font-mono mt-0.5">
                          {currentAnalysis.non_breaking_count}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Findings Breakdown */}
                  <div>
                    <h4 className="text-xs font-semibold text-gray-300 mb-2 flex items-center justify-between">
                      <span>Categorized Contract Findings ({currentAnalysis.findings.length})</span>
                    </h4>

                    <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                      {currentAnalysis.findings.map((f, idx) => (
                        <div
                          key={idx}
                          className={`border rounded-lg p-3 space-y-2 text-xs transition-all ${
                            f.severity === "BREAKING"
                              ? "bg-rose-950/10 border-rose-900/50"
                              : f.severity === "POTENTIALLY_BREAKING"
                              ? "bg-amber-950/10 border-amber-900/50"
                              : "bg-emerald-950/10 border-emerald-900/50"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                                f.severity === "BREAKING"
                                  ? "bg-rose-500/20 text-rose-300"
                                  : f.severity === "POTENTIALLY_BREAKING"
                                  ? "bg-amber-500/20 text-amber-300"
                                  : "bg-emerald-500/20 text-emerald-300"
                              }`}
                            >
                              {f.severity}
                            </span>
                            <span className="text-[10px] font-mono text-gray-400">{f.category}</span>
                          </div>

                          <div>
                            <div className="font-mono text-[11px] font-bold text-gray-200">{f.target}</div>
                            <p className="text-xs text-gray-300 mt-1">{f.description}</p>
                          </div>

                          {f.evidence && (
                            <div className="bg-[#080d14] p-2 rounded border border-[#1b2537] text-[10px] font-mono text-gray-400">
                              <span className="text-gray-500">Provenance Evidence:</span> {f.evidence}
                            </div>
                          )}

                          {f.safe_migration_advice && (
                            <div className="bg-amber-500/5 border border-amber-500/20 p-2 rounded text-[11px] text-amber-200/90 flex items-start gap-1.5">
                              <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                              <div>
                                <span className="font-semibold text-amber-300">Safe Migration Advice:</span>{" "}
                                {f.safe_migration_advice}
                              </div>
                            </div>
                          )}

                          <div className="pt-1 flex justify-end">
                            <button
                              onClick={() => navigateToSimulator(f)}
                              className="text-[10px] font-medium text-rose-400 hover:text-rose-300 flex items-center gap-1 hover:underline"
                            >
                              Simulate downstream blast radius &rarr;
                            </button>
                          </div>
                        </div>
                      ))}

                      {currentAnalysis.findings.length === 0 && (
                        <div className="text-center py-8 text-gray-500 text-xs">
                          <CheckCircle2 className="w-6 h-6 text-emerald-500 mx-auto mb-2" />
                          No breaking changes detected. Contract backward compatibility verified.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-[#0e1420] border border-[#1f2937] rounded-lg p-10 text-center space-y-3">
                  <GitPullRequest className="w-10 h-10 text-gray-600 mx-auto" />
                  <h3 className="text-sm font-semibold text-gray-300">No Analysis Selected</h3>
                  <p className="text-xs text-gray-500 max-w-sm mx-auto">
                    Select a previous analysis from history or run a new OpenAPI / SQL migration verification.
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
