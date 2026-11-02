"use client";

import React, { useState, useMemo } from "react";
import { GraphNode, GraphEdge, DownstreamImpactResult, EvidenceConfidence } from "@/types";
import { api } from "@/lib/api";
import {
  Server,
  Globe,
  Database,
  Users2,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Zap,
  X,
  FileCheck2,
  ArrowRight,
  Search,
} from "lucide-react";

interface TopologyCanvasProps {
  projectId: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  onRefresh: () => void;
}

export function TopologyCanvas({ projectId, nodes, edges, onRefresh }: TopologyCanvasProps) {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [impactResult, setImpactResult] = useState<DownstreamImpactResult | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [searchFilter, setSearchFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");

  const getNodeColor = (type: string) => {
    switch (type) {
      case "service":
        return "border-[#10b981] bg-[#10b981]/10 text-[#10b981]";
      case "endpoint":
        return "border-[#06b6d4] bg-[#06b6d4]/10 text-[#06b6d4]";
      case "database_table":
        return "border-amber-500 bg-amber-500/10 text-amber-400";
      case "customer_workflow":
        return "border-rose-500 bg-rose-500/10 text-rose-400";
      default:
        return "border-gray-500 bg-gray-500/10 text-gray-400";
    }
  };

  const getNodeIcon = (type: string) => {
    switch (type) {
      case "service":
        return <Server className="w-3.5 h-3.5 shrink-0" />;
      case "endpoint":
        return <Globe className="w-3.5 h-3.5 shrink-0" />;
      case "database_table":
        return <Database className="w-3.5 h-3.5 shrink-0" />;
      case "customer_workflow":
        return <Users2 className="w-3.5 h-3.5 shrink-0" />;
      default:
        return <HelpCircle className="w-3.5 h-3.5 shrink-0" />;
    }
  };

  const filteredNodes = useMemo(() => {
    return nodes.filter((n) => {
      const matchesSearch =
        n.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
        n.identifier.toLowerCase().includes(searchFilter.toLowerCase());
      const matchesType = typeFilter === "all" || n.node_type === typeFilter;
      return matchesSearch && matchesType;
    });
  }, [nodes, searchFilter, typeFilter]);

  const handleSimulateImpact = async (node: GraphNode) => {
    setIsSimulating(true);
    setImpactResult(null);
    try {
      const res = await api.getDownstreamImpact(projectId, node.id);
      setImpactResult(res);
    } catch (e) {
      console.error("Failed to simulate impact:", e);
    } finally {
      setIsSimulating(false);
    }
  };

  // Group nodes by type for high-density structural view
  const services = filteredNodes.filter((n) => n.node_type === "service");
  const endpoints = filteredNodes.filter((n) => n.node_type === "endpoint");
  const tables = filteredNodes.filter((n) => n.node_type === "database_table");
  const customers = filteredNodes.filter((n) => n.node_type === "customer_workflow");

  return (
    <div className="flex flex-col lg:flex-row gap-4 h-[720px] relative">
      {/* Topology Canvas Main Area */}
      <div className="flex-1 enterprise-card flex flex-col overflow-hidden">
        {/* Controls Bar */}
        <div className="p-3 border-b border-[#1f2937] flex flex-wrap items-center justify-between gap-2 bg-[#0d131f]">
          <div className="flex items-center space-x-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-gray-500" />
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Search components..."
                className="pl-8 pr-3 py-1 text-xs rounded bg-[#111827] border border-[#1f2937] text-gray-200 focus:outline-none focus:border-[#10b981] w-48"
              />
            </div>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-2 py-1 text-xs rounded bg-[#111827] border border-[#1f2937] text-gray-300 focus:outline-none font-mono"
            >
              <option value="all">All Types ({nodes.length})</option>
              <option value="service">Services ({nodes.filter((n) => n.node_type === "service").length})</option>
              <option value="endpoint">Endpoints ({nodes.filter((n) => n.node_type === "endpoint").length})</option>
              <option value="database_table">Tables ({nodes.filter((n) => n.node_type === "database_table").length})</option>
              <option value="customer_workflow">Customers ({nodes.filter((n) => n.node_type === "customer_workflow").length})</option>
            </select>
          </div>

          {/* Legend */}
          <div className="flex items-center space-x-3 text-[10px] font-mono text-gray-400">
            <div className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-[#10b981]" />
              <span>Service</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-[#06b6d4]" />
              <span>Endpoint</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-amber-400" />
              <span>DB Table</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-rose-400" />
              <span>Customer</span>
            </div>
          </div>
        </div>

        {/* Topology Grid Matrix */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6 bg-[#080c14]">
          {nodes.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center text-gray-500 py-16">
              <Server className="w-10 h-10 mb-3 text-gray-600" />
              <p className="text-sm font-medium text-gray-300">Topology Graph is Empty</p>
              <p className="text-xs text-gray-500 max-w-sm mt-1">
                Ingest an OpenAPI specification, scan code callsites, or map customer workflows to build the evidence graph.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Column 1: Services */}
              <div className="space-y-2">
                <div className="text-[11px] font-mono uppercase tracking-wider text-[#10b981] flex items-center justify-between pb-1 border-b border-[#1f2937]">
                  <span>Services ({services.length})</span>
                  <Server className="w-3.5 h-3.5" />
                </div>
                {services.map((node) => (
                  <button
                    key={node.id}
                    onClick={() => {
                      setSelectedNode(node);
                      setImpactResult(null);
                    }}
                    className={`w-full text-left p-3 rounded border text-xs transition-all ${
                      selectedNode?.id === node.id
                        ? "border-[#10b981] bg-[#10b981]/20 shadow-md"
                        : "border-[#1f2937] bg-[#111827] hover:border-gray-600"
                    }`}
                  >
                    <div className="font-semibold text-gray-100 truncate">{node.name}</div>
                    <div className="text-[10px] text-gray-400 font-mono truncate mt-0.5">{node.identifier}</div>
                  </button>
                ))}
              </div>

              {/* Column 2: Endpoints */}
              <div className="space-y-2">
                <div className="text-[11px] font-mono uppercase tracking-wider text-[#06b6d4] flex items-center justify-between pb-1 border-b border-[#1f2937]">
                  <span>API Endpoints ({endpoints.length})</span>
                  <Globe className="w-3.5 h-3.5" />
                </div>
                {endpoints.map((node) => (
                  <button
                    key={node.id}
                    onClick={() => {
                      setSelectedNode(node);
                      setImpactResult(null);
                    }}
                    className={`w-full text-left p-3 rounded border text-xs transition-all ${
                      selectedNode?.id === node.id
                        ? "border-[#06b6d4] bg-[#06b6d4]/20 shadow-md"
                        : "border-[#1f2937] bg-[#111827] hover:border-gray-600"
                    }`}
                  >
                    <div className="font-semibold text-gray-100 truncate font-mono text-[11px]">{node.name}</div>
                    <div className="text-[10px] text-gray-400 truncate mt-0.5">{node.description || "Endpoint"}</div>
                  </button>
                ))}
              </div>

              {/* Column 3: Database Tables */}
              <div className="space-y-2">
                <div className="text-[11px] font-mono uppercase tracking-wider text-amber-400 flex items-center justify-between pb-1 border-b border-[#1f2937]">
                  <span>Tables & Schemas ({tables.length})</span>
                  <Database className="w-3.5 h-3.5" />
                </div>
                {tables.map((node) => (
                  <button
                    key={node.id}
                    onClick={() => {
                      setSelectedNode(node);
                      setImpactResult(null);
                    }}
                    className={`w-full text-left p-3 rounded border text-xs transition-all ${
                      selectedNode?.id === node.id
                        ? "border-amber-400 bg-amber-400/20 shadow-md"
                        : "border-[#1f2937] bg-[#111827] hover:border-gray-600"
                    }`}
                  >
                    <div className="font-semibold text-gray-100 truncate font-mono text-[11px]">{node.name}</div>
                    <div className="text-[10px] text-gray-400 truncate mt-0.5">{node.description || "DB Table"}</div>
                  </button>
                ))}
              </div>

              {/* Column 4: Customer Workflows */}
              <div className="space-y-2">
                <div className="text-[11px] font-mono uppercase tracking-wider text-rose-400 flex items-center justify-between pb-1 border-b border-[#1f2937]">
                  <span>Customer Workflows ({customers.length})</span>
                  <Users2 className="w-3.5 h-3.5" />
                </div>
                {customers.map((node) => (
                  <button
                    key={node.id}
                    onClick={() => {
                      setSelectedNode(node);
                      setImpactResult(null);
                    }}
                    className={`w-full text-left p-3 rounded border text-xs transition-all ${
                      selectedNode?.id === node.id
                        ? "border-rose-400 bg-rose-400/20 shadow-md"
                        : "border-[#1f2937] bg-[#111827] hover:border-gray-600"
                    }`}
                  >
                    <div className="font-semibold text-gray-100 truncate">{node.name}</div>
                    <div className="text-[10px] text-gray-400 font-mono truncate mt-0.5">{node.identifier}</div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Side Inspector Panel */}
      {selectedNode && (
        <div className="w-full lg:w-96 enterprise-card flex flex-col p-5 bg-[#111827] shadow-2xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#1f2937]">
            <div className="flex items-center space-x-2">
              <span className={`p-1.5 rounded border ${getNodeColor(selectedNode.node_type)}`}>
                {getNodeIcon(selectedNode.node_type)}
              </span>
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-gray-400">
                  {selectedNode.node_type}
                </span>
                <h4 className="text-sm font-semibold text-gray-100 truncate max-w-[200px]">
                  {selectedNode.name}
                </h4>
              </div>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="p-1 rounded text-gray-400 hover:text-gray-200 hover:bg-[#1f2937]"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-[10px] font-mono text-gray-500 uppercase">Identifier</span>
              <div className="font-mono text-gray-200 bg-[#0b0f17] p-2 rounded border border-[#1f2937] truncate mt-1">
                {selectedNode.identifier}
              </div>
            </div>

            {selectedNode.description && (
              <div>
                <span className="text-[10px] font-mono text-gray-500 uppercase">Description</span>
                <p className="text-gray-300 mt-0.5">{selectedNode.description}</p>
              </div>
            )}

            {/* Downstream Blast Radius Action */}
            <div className="pt-2">
              <button
                onClick={() => handleSimulateImpact(selectedNode)}
                disabled={isSimulating}
                className="w-full py-2 px-3 rounded bg-[#06b6d4] text-gray-950 font-semibold text-xs flex items-center justify-center space-x-1.5 hover:bg-[#0891b2] transition-colors disabled:opacity-50"
              >
                <Zap className="w-3.5 h-3.5 fill-current" />
                <span>{isSimulating ? "Traversing Graph..." : "Simulate Blast Radius"}</span>
              </button>
            </div>

            {/* Impact Results View */}
            {impactResult && (
              <div className="p-3.5 rounded bg-[#0b0f17] border border-[#1f2937] space-y-3 mt-3">
                <div className="flex items-center justify-between pb-2 border-b border-[#1f2937]">
                  <span className="font-mono text-[10px] uppercase text-gray-400">
                    Transitive Downstream Impact
                  </span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[9px] font-mono ${
                      impactResult.safety_verdict === "CAUTION_REQUIRED"
                        ? "bg-amber-950/40 text-amber-400 border border-amber-800"
                        : "bg-emerald-950/40 text-emerald-400 border border-emerald-800"
                    }`}
                  >
                    {impactResult.safety_verdict}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-center font-mono">
                  <div className="p-2 rounded bg-[#111827]">
                    <div className="text-base font-bold text-gray-100">{impactResult.total_impacted_nodes}</div>
                    <div className="text-[9px] text-gray-500">Total Nodes</div>
                  </div>
                  <div className="p-2 rounded bg-[#111827]">
                    <div className="text-base font-bold text-rose-400">{impactResult.impacted_customers.length}</div>
                    <div className="text-[9px] text-gray-500">Customers Affected</div>
                  </div>
                </div>

                {impactResult.impacted_customers.length > 0 && (
                  <div>
                    <span className="text-[10px] font-mono text-rose-400 uppercase">
                      Contracted Customers At Risk:
                    </span>
                    <ul className="mt-1 space-y-1">
                      {impactResult.impacted_customers.map((c) => (
                        <li key={c} className="text-rose-300 text-[11px] flex items-center space-x-1">
                          <AlertTriangle className="w-3 h-3 text-rose-400 shrink-0" />
                          <span className="truncate">{c}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {impactResult.impacted_services.length > 0 && (
                  <div>
                    <span className="text-[10px] font-mono text-gray-400 uppercase">
                      Dependent Services:
                    </span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {impactResult.impacted_services.map((s) => (
                        <span key={s} className="px-1.5 py-0.5 rounded bg-[#111827] text-gray-300 text-[10px] font-mono">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
