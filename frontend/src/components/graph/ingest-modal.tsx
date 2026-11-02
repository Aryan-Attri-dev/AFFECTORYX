"use client";

import React, { useState } from "react";
import { api } from "@/lib/api";
import {
  X,
  FileCode2,
  Database,
  Users2,
  Code2,
  AlertCircle,
  CheckCircle2,
  Sparkles,
} from "lucide-react";

interface IngestModalProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const SAMPLE_PAYMENT_SPEC = JSON.stringify(
  {
    openapi: "3.0.0",
    info: {
      title: "Core Ledger & Settlement Service",
      version: "3.1.0",
      description: "Financial ledger settlement, dispute orchestration, and payout processing",
    },
    paths: {
      "/api/v1/settlements": {
        post: {
          operationId: "create_settlement",
          summary: "Execute payout settlement batch",
          requestBody: { content: { "application/json": { schema: { type: "object" } } } },
          responses: { "201": { description: "Settled" }, "400": { description: "Invalid" } },
        },
        get: {
          operationId: "list_settlements",
          summary: "Query ledger transaction stream",
          responses: { "200": { description: "OK" } },
        },
      },
      "/api/v1/settlements/{id}": {
        get: {
          operationId: "get_settlement_by_id",
          summary: "Fetch settlement audit record",
          parameters: [{ name: "id", in: "path", required: true }],
          responses: { "200": { description: "OK" } },
        },
      },
      "/api/v1/accounts/verify": {
        post: {
          operationId: "verify_account_standing",
          summary: "Verify banking account compliance status",
          responses: { "200": { description: "Verified" } },
        },
      },
    },
  },
  null,
  2
);

export function IngestModal({ projectId, isOpen, onClose, onSuccess }: IngestModalProps) {
  const [tab, setTab] = useState<"openapi" | "ast" | "migration" | "customer">("openapi");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // OpenAPI state
  const [specContent, setSpecContent] = useState(SAMPLE_PAYMENT_SPEC);
  const [specSource, setSpecSource] = useState("ledger_service_v3.json");

  // AST state
  const [callerName, setCallerName] = useState("CheckoutOrchestrator");
  const [filePath, setFilePath] = useState("services/checkout/orchestrator.py");
  const [codeContent, setCodeContent] = useState(
    `import requests\n\ndef execute_checkout(order_id, user_id):\n    # Confirmed callsite\n    resp = requests.post("http://billing-service/api/v1/settlements", json={"order_id": order_id})\n    # Dynamic callsite\n    dynamic_url = get_payout_webhook()\n    requests.get(dynamic_url)\n    return resp.json()`
  );

  // Migration state
  const [migrationFilename, setMigrationFilename] = useState("V24__settlement_ledger.sql");
  const [sqlContent, setSqlContent] = useState(
    `CREATE TABLE ledger_accounts (\n    id VARCHAR(36) PRIMARY KEY,\n    balance NUMERIC(18, 4) NOT NULL\n);\n\nALTER TABLE legacy_transactions DROP COLUMN routing_code;\nDROP TABLE deprecated_cache;`
  );

  // Customer state
  const [customerName, setCustomerName] = useState("Titan Global Bank");
  const [tier, setTier] = useState("tier-1");
  const [contractSLA, setContractSLA] = useState("99.999%");
  const [workflows, setWorkflows] = useState("HighVolumePayouts, DisputeSettlement");
  const [endpoints, setEndpoints] = useState("POST /api/v1/settlements, POST /api/v1/accounts/verify");

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      if (tab === "openapi") {
        await api.ingestOpenAPI(projectId, specContent, specSource);
        setSuccessMsg("OpenAPI specification parsed and nodes registered successfully.");
      } else if (tab === "ast") {
        await api.ingestCodeAST(projectId, callerName, filePath, codeContent);
        setSuccessMsg("Static AST scanner completed and callsites registered.");
      } else if (tab === "migration") {
        await api.ingestSQLMigration(projectId, migrationFilename, sqlContent);
        setSuccessMsg("SQL migration parsed and database table nodes registered.");
      } else if (tab === "customer") {
        const wfList = workflows.split(",").map((w) => w.trim()).filter((w) => w.length > 0);
        const epList = endpoints.split(",").map((e) => e.trim()).filter((e) => e.length > 0);
        await api.addCustomer(projectId, {
          customer_name: customerName.trim(),
          tier,
          contract_sla: contractSLA.trim(),
          workflows: wfList,
          consumed_endpoints: epList,
        });
        setSuccessMsg(`Customer '${customerName}' workflow mappings registered.`);
      }

      onSuccess();
      setTimeout(() => {
        onClose();
        setSuccessMsg(null);
      }, 1200);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Ingestion failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-[#111827] border border-[#1f2937] rounded-lg max-w-2xl w-full overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-5 py-4 border-b border-[#1f2937] flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-[#10b981]" />
            <h3 className="text-sm font-semibold text-gray-100">
              Evidence & Dependency Ingestion Engine
            </h3>
          </div>
          <button onClick={onClose} className="p-1 rounded text-gray-400 hover:text-gray-200">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="grid grid-cols-4 gap-1 p-2 bg-[#0d131f] border-b border-[#1f2937] text-xs font-mono">
          <button
            type="button"
            onClick={() => setTab("openapi")}
            className={`py-1.5 px-2 rounded flex items-center justify-center space-x-1.5 transition-colors ${
              tab === "openapi" ? "bg-[#111827] text-[#10b981] border border-[#1f2937]" : "text-gray-400"
            }`}
          >
            <FileCode2 className="w-3.5 h-3.5" />
            <span>OpenAPI v3</span>
          </button>
          <button
            type="button"
            onClick={() => setTab("ast")}
            className={`py-1.5 px-2 rounded flex items-center justify-center space-x-1.5 transition-colors ${
              tab === "ast" ? "bg-[#111827] text-[#06b6d4] border border-[#1f2937]" : "text-gray-400"
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Code AST</span>
          </button>
          <button
            type="button"
            onClick={() => setTab("migration")}
            className={`py-1.5 px-2 rounded flex items-center justify-center space-x-1.5 transition-colors ${
              tab === "migration" ? "bg-[#111827] text-amber-400 border border-[#1f2937]" : "text-gray-400"
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>SQL DDL</span>
          </button>
          <button
            type="button"
            onClick={() => setTab("customer")}
            className={`py-1.5 px-2 rounded flex items-center justify-center space-x-1.5 transition-colors ${
              tab === "customer" ? "bg-[#111827] text-rose-400 border border-[#1f2937]" : "text-gray-400"
            }`}
          >
            <Users2 className="w-3.5 h-3.5" />
            <span>Customer SLA</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 overflow-y-auto space-y-4 text-xs flex-1">
          {error && (
            <div className="p-3 rounded bg-rose-950/40 border border-rose-800 text-xs text-rose-300 flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3 rounded bg-emerald-950/40 border border-emerald-800 text-xs text-emerald-300 flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* TAB 1: OPENAPI */}
          {tab === "openapi" && (
            <div className="space-y-3">
              <div>
                <label className="block text-gray-300 font-medium mb-1">Specification Name</label>
                <input
                  type="text"
                  value={specSource}
                  onChange={(e) => setSpecSource(e.target.value)}
                  className="w-full px-3 py-1.5 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-200 font-mono text-xs focus:outline-none focus:border-[#10b981]"
                />
              </div>
              <div>
                <label className="block text-gray-300 font-medium mb-1">
                  OpenAPI 3.0 / 3.1 Content (JSON or YAML)
                </label>
                <textarea
                  rows={9}
                  value={specContent}
                  onChange={(e) => setSpecContent(e.target.value)}
                  className="w-full p-3 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-200 font-mono text-[11px] focus:outline-none focus:border-[#10b981]"
                />
              </div>
            </div>
          )}

          {/* TAB 2: CODE AST */}
          {tab === "ast" && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-medium mb-1">Caller Service Name</label>
                  <input
                    type="text"
                    value={callerName}
                    onChange={(e) => setCallerName(e.target.value)}
                    className="w-full px-3 py-1.5 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-200 font-mono text-xs focus:outline-none focus:border-[#06b6d4]"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-medium mb-1">File Path</label>
                  <input
                    type="text"
                    value={filePath}
                    onChange={(e) => setFilePath(e.target.value)}
                    className="w-full px-3 py-1.5 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-200 font-mono text-xs focus:outline-none focus:border-[#06b6d4]"
                  />
                </div>
              </div>
              <div>
                <label className="block text-gray-300 font-medium mb-1">
                  Source Code (Static AST inspection — No dynamic execution)
                </label>
                <textarea
                  rows={9}
                  value={codeContent}
                  onChange={(e) => setCodeContent(e.target.value)}
                  className="w-full p-3 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-200 font-mono text-[11px] focus:outline-none focus:border-[#06b6d4]"
                />
              </div>
            </div>
          )}

          {/* TAB 3: MIGRATION */}
          {tab === "migration" && (
            <div className="space-y-3">
              <div>
                <label className="block text-gray-300 font-medium mb-1">Migration Filename</label>
                <input
                  type="text"
                  value={migrationFilename}
                  onChange={(e) => setMigrationFilename(e.target.value)}
                  className="w-full px-3 py-1.5 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-200 font-mono text-xs focus:outline-none focus:border-amber-400"
                />
              </div>
              <div>
                <label className="block text-gray-300 font-medium mb-1">SQL DDL Statements</label>
                <textarea
                  rows={9}
                  value={sqlContent}
                  onChange={(e) => setSqlContent(e.target.value)}
                  className="w-full p-3 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-200 font-mono text-[11px] focus:outline-none focus:border-amber-400"
                />
              </div>
            </div>
          )}

          {/* TAB 4: CUSTOMER */}
          {tab === "customer" && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-medium mb-1">Customer / Enterprise Name</label>
                  <input
                    type="text"
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    className="w-full px-3 py-1.5 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-200 text-xs focus:outline-none focus:border-rose-400"
                    required
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-medium mb-1">Customer Tier</label>
                  <select
                    value={tier}
                    onChange={(e) => setTier(e.target.value)}
                    className="w-full px-3 py-1.5 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-200 text-xs focus:outline-none font-mono"
                  >
                    <option value="tier-1">Tier 1 (Mission-Critical)</option>
                    <option value="enterprise">Enterprise</option>
                    <option value="standard">Standard</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-gray-300 font-medium mb-1">Contract SLA Guarantee</label>
                <input
                  type="text"
                  value={contractSLA}
                  onChange={(e) => setContractSLA(e.target.value)}
                  placeholder="e.g. 99.999%"
                  className="w-full px-3 py-1.5 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-200 font-mono text-xs focus:outline-none focus:border-rose-400"
                />
              </div>
              <div>
                <label className="block text-gray-300 font-medium mb-1">
                  Contracted Business Workflows (Comma-separated)
                </label>
                <input
                  type="text"
                  value={workflows}
                  onChange={(e) => setWorkflows(e.target.value)}
                  className="w-full px-3 py-1.5 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-200 text-xs focus:outline-none focus:border-rose-400"
                />
              </div>
              <div>
                <label className="block text-gray-300 font-medium mb-1">
                  Consumed API Endpoints (Comma-separated)
                </label>
                <input
                  type="text"
                  value={endpoints}
                  onChange={(e) => setEndpoints(e.target.value)}
                  className="w-full px-3 py-1.5 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-200 font-mono text-xs focus:outline-none focus:border-rose-400"
                />
              </div>
            </div>
          )}

          <div className="pt-3 border-t border-[#1f2937] flex items-center justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 rounded text-gray-400 hover:text-gray-200 hover:bg-[#1f2937]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-1.5 rounded bg-[#10b981] text-gray-950 font-semibold hover:bg-[#059669] disabled:opacity-50"
            >
              {isLoading ? "Ingesting..." : "Execute Ingestion"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
