"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Header } from "@/components/navigation/header";
import { Sidebar } from "@/components/navigation/sidebar";
import { IngestModal } from "@/components/graph/ingest-modal";
import { api } from "@/lib/api";
import { Project, CustomerMapping } from "@/types";
import {
  Users2,
  Plus,
  Shield,
  Layers,
  Globe,
  RefreshCw,
  Building,
} from "lucide-react";

export default function CustomersPage() {
  const router = useRouter();
  const { user, activeOrg, isLoading } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [customers, setCustomers] = useState<CustomerMapping[]>([]);
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

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

  const fetchCustomers = async () => {
    if (!selectedProjectId) return;
    setIsDataLoading(true);
    try {
      const data = await api.listCustomers(selectedProjectId);
      setCustomers(data);
    } catch (err) {
      console.error("Failed to load customer mappings:", err);
    } finally {
      setIsDataLoading(false);
    }
  };

  useEffect(() => {
    if (selectedProjectId) {
      fetchCustomers();
    }
  }, [selectedProjectId]);

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-[#0b0f17] flex items-center justify-center font-mono text-xs text-gray-500">
        Loading customer intelligence...
      </div>
    );
  }

  const getTierBadge = (tier: string) => {
    if (tier === "tier-1") {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-rose-950/40 border border-rose-800 text-rose-400 font-semibold">
          Tier 1 (Mission-Critical)
        </span>
      );
    }
    if (tier === "enterprise") {
      return (
        <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-amber-950/40 border border-amber-800 text-amber-400">
          Enterprise
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-gray-800 text-gray-300">
        Standard
      </span>
    );
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
                <Users2 className="w-5 h-5 text-[#10b981]" />
                <h1 className="text-xl font-bold text-gray-100 tracking-tight">
                  Customer Intelligence & SLA Mappings
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
                Deterministic mapping of enterprise customers to specific contracted API endpoints and revenue-critical business workflows.
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={fetchCustomers}
                className="p-1.5 rounded hover:bg-[#111827] border border-[#1f2937] text-gray-400 hover:text-gray-200 transition-colors"
                title="Refresh"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isDataLoading ? "animate-spin" : ""}`} />
              </button>
              <button
                onClick={() => setIsModalOpen(true)}
                disabled={!selectedProjectId}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#10b981] text-gray-950 font-medium text-xs hover:bg-[#059669] transition-colors disabled:opacity-50"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Map Customer SLA</span>
              </button>
            </div>
          </div>

          {/* Customer Matrix Table */}
          <div className="enterprise-card overflow-hidden">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="table-header text-gray-400 font-mono uppercase text-[10px] tracking-wider">
                  <th className="py-2.5 px-4">Customer / Enterprise</th>
                  <th className="py-2.5 px-4">Contract Tier</th>
                  <th className="py-2.5 px-4">SLA Commitment</th>
                  <th className="py-2.5 px-4">Contracted Workflows</th>
                  <th className="py-2.5 px-4">Consumed Endpoints</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1f2937] text-gray-200">
                {isDataLoading ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-gray-500 font-mono">
                      Querying customer intelligence matrix...
                    </td>
                  </tr>
                ) : customers.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-gray-500">
                      <Users2 className="w-8 h-8 mx-auto mb-2 text-gray-600" />
                      <p className="text-sm font-medium text-gray-400">No Customers Mapped Yet</p>
                      <p className="text-xs text-gray-600 mt-1">
                        Map enterprise customers to API endpoints to assess SLA breach risk during deployments.
                      </p>
                    </td>
                  </tr>
                ) : (
                  customers.map((c) => (
                    <tr key={c.id} className="hover:bg-[#151c2a] transition-colors">
                      <td className="py-3 px-4 font-semibold text-gray-100">
                        <div className="flex items-center space-x-2">
                          <Building className="w-3.5 h-3.5 text-gray-400" />
                          <span>{c.customer_name}</span>
                        </div>
                      </td>

                      <td className="py-3 px-4">{getTierBadge(c.tier)}</td>

                      <td className="py-3 px-4 font-mono font-semibold text-[#10b981]">
                        {c.contract_sla}
                      </td>

                      <td className="py-3 px-4">
                        <div className="flex flex-wrap gap-1">
                          {c.workflows.map((wf) => (
                            <span
                              key={wf}
                              className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-rose-950/30 border border-rose-900/50 text-rose-300"
                            >
                              {wf}
                            </span>
                          ))}
                        </div>
                      </td>

                      <td className="py-3 px-4 font-mono text-[11px] text-gray-400">
                        <div className="flex flex-wrap gap-1">
                          {c.consumed_endpoints.map((ep) => (
                            <span
                              key={ep}
                              className="px-1.5 py-0.5 rounded text-[10px] bg-[#0b0f17] border border-[#1f2937] text-gray-300"
                            >
                              {ep}
                            </span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </main>
      </div>

      {selectedProjectId && (
        <IngestModal
          projectId={selectedProjectId}
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSuccess={fetchCustomers}
        />
      )}
    </div>
  );
}
