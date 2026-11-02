"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Header } from "@/components/navigation/header";
import { Sidebar } from "@/components/navigation/sidebar";
import { MembersList } from "@/components/organizations/members-list";
import { AuditLogView } from "@/components/organizations/audit-log-view";
import { api } from "@/lib/api";
import { Settings, Building2, Users2, ShieldCheck, Plus, CheckCircle2, AlertCircle } from "lucide-react";

export default function SettingsPage() {
  const router = useRouter();
  const { user, activeOrg, refreshOrganizations, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<"general" | "members" | "audit">("general");

  // Create organization modal
  const [isNewOrgOpen, setIsNewOrgOpen] = useState(false);
  const [newOrgName, setNewOrgName] = useState("");
  const [newOrgDesc, setNewOrgDesc] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [user, isLoading, router]);

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-[#0b0f17] flex items-center justify-center font-mono text-xs text-gray-500">
        Loading settings...
      </div>
    );
  }

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrgName.trim()) return;

    setErrorMsg(null);
    setIsSubmitting(true);
    try {
      await api.createOrganization({
        name: newOrgName.trim(),
        description: newOrgDesc.trim() || undefined,
      });
      await refreshOrganizations();
      setSuccessMsg("Organization created successfully");
      setNewOrgName("");
      setNewOrgDesc("");
      setIsNewOrgOpen(false);
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to create organization");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f17] flex flex-col">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
          <div className="pb-4 border-b border-[#1f2937]">
            <div className="flex items-center space-x-2">
              <Settings className="w-5 h-5 text-[#10b981]" />
              <h1 className="text-xl font-bold text-gray-100 tracking-tight">
                Organization & Security Settings
              </h1>
            </div>
            <p className="text-xs text-gray-400 mt-1">
              Configure tenant parameters, access control lists, team memberships, and audit trails.
            </p>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center space-x-1 border-b border-[#1f2937] text-xs font-mono">
            <button
              onClick={() => setActiveTab("general")}
              className={`flex items-center space-x-2 py-2.5 px-4 border-b-2 transition-colors ${
                activeTab === "general"
                  ? "border-[#10b981] text-[#10b981] font-medium"
                  : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              <Building2 className="w-3.5 h-3.5" />
              <span>General & Tenants</span>
            </button>
            <button
              onClick={() => setActiveTab("members")}
              className={`flex items-center space-x-2 py-2.5 px-4 border-b-2 transition-colors ${
                activeTab === "members"
                  ? "border-[#10b981] text-[#10b981] font-medium"
                  : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              <Users2 className="w-3.5 h-3.5" />
              <span>Team Members ({activeOrg?.member_count || 1})</span>
            </button>
            <button
              onClick={() => setActiveTab("audit")}
              className={`flex items-center space-x-2 py-2.5 px-4 border-b-2 transition-colors ${
                activeTab === "audit"
                  ? "border-[#10b981] text-[#10b981] font-medium"
                  : "border-transparent text-gray-400 hover:text-gray-200"
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Security Audit Logs</span>
            </button>
          </div>

          {successMsg && (
            <div className="p-3 rounded bg-emerald-950/40 border border-emerald-800 text-xs text-emerald-300 flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {errorMsg && (
            <div className="p-3 rounded bg-rose-950/40 border border-rose-800 text-xs text-rose-300 flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Tab 1: General Info */}
          {activeTab === "general" && (
            <div className="space-y-6 max-w-3xl">
              <div className="enterprise-card p-5 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-[#1f2937]">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-100">Active Tenant Metadata</h3>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Unique identifier and organization scope.
                    </p>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-[#10b981]/10 border border-[#10b981]/30 text-[#10b981] font-mono uppercase">
                    Your Role: {activeOrg?.user_role || "Owner"}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <label className="text-gray-500 font-mono block mb-1">Organization Name</label>
                    <div className="font-semibold text-gray-200">{activeOrg?.name}</div>
                  </div>
                  <div>
                    <label className="text-gray-500 font-mono block mb-1">Slug Identifier</label>
                    <div className="font-mono text-gray-300">{activeOrg?.slug}</div>
                  </div>
                  <div>
                    <label className="text-gray-500 font-mono block mb-1">Tenant ID</label>
                    <div className="font-mono text-[11px] text-gray-400">{activeOrg?.id}</div>
                  </div>
                  <div>
                    <label className="text-gray-500 font-mono block mb-1">Created</label>
                    <div className="text-gray-400">
                      {activeOrg?.created_at ? new Date(activeOrg.created_at).toLocaleString() : "—"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Add New Organization section */}
              <div className="enterprise-card p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-100">Multiple Organizations</h3>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Create separate isolated workspaces for distinct teams, business units, or customers.
                    </p>
                  </div>
                  <button
                    onClick={() => setIsNewOrgOpen(!isNewOrgOpen)}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#1f2937] text-gray-200 hover:bg-[#374151] font-medium text-xs transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Create Organization</span>
                  </button>
                </div>

                {isNewOrgOpen && (
                  <form onSubmit={handleCreateOrg} className="p-4 rounded bg-[#0b0f17] border border-[#1f2937] space-y-3 mt-3 text-xs">
                    <div>
                      <label className="block text-gray-300 font-medium mb-1">Organization Name *</label>
                      <input
                        type="text"
                        value={newOrgName}
                        onChange={(e) => setNewOrgName(e.target.value)}
                        placeholder="e.g. Acme Cloud Corp"
                        className="w-full px-3 py-2 rounded bg-[#111827] border border-[#1f2937] text-gray-100 focus:outline-none focus:border-[#10b981]"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-gray-300 font-medium mb-1">Description</label>
                      <textarea
                        value={newOrgDesc}
                        onChange={(e) => setNewOrgDesc(e.target.value)}
                        placeholder="Purpose of this organization"
                        rows={2}
                        className="w-full px-3 py-2 rounded bg-[#111827] border border-[#1f2937] text-gray-100 focus:outline-none focus:border-[#10b981]"
                      />
                    </div>
                    <div className="flex justify-end space-x-2 pt-2">
                      <button
                        type="button"
                        onClick={() => setIsNewOrgOpen(false)}
                        className="px-3 py-1 text-gray-400 hover:text-gray-200"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={isSubmitting}
                        className="px-4 py-1.5 rounded bg-[#10b981] text-gray-950 font-semibold hover:bg-[#059669] disabled:opacity-50"
                      >
                        {isSubmitting ? "Creating..." : "Save Workspace"}
                      </button>
                    </div>
                  </form>
                )}
              </div>
            </div>
          )}

          {/* Tab 2: Members */}
          {activeTab === "members" && <MembersList />}

          {/* Tab 3: Security Audit */}
          {activeTab === "audit" && <AuditLogView />}
        </main>
      </div>
    </div>
  );
}
