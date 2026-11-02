"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AuditLog } from "@/types";
import { useAuth } from "@/context/auth-context";
import { ShieldCheck, RefreshCw, KeyRound, FolderGit2, UserCog, Activity } from "lucide-react";

export function AuditLogView() {
  const { activeOrg } = useAuth();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchLogs = async () => {
    if (!activeOrg) return;
    setIsLoading(true);
    try {
      const data = await api.getAuditLogs(activeOrg.id);
      setLogs(data);
    } catch (err) {
      console.error("Failed to fetch audit logs:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [activeOrg]);

  const getActionBadge = (action: string) => {
    if (action.startsWith("auth.")) {
      return (
        <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-cyan-950/40 border border-cyan-800 text-cyan-400">
          <KeyRound className="w-2.5 h-2.5" />
          <span>{action}</span>
        </span>
      );
    }
    if (action.startsWith("project.")) {
      return (
        <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-950/40 border border-emerald-800 text-emerald-400">
          <FolderGit2 className="w-2.5 h-2.5" />
          <span>{action}</span>
        </span>
      );
    }
    if (action.startsWith("member.")) {
      return (
        <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-950/40 border border-amber-800 text-amber-400">
          <UserCog className="w-2.5 h-2.5" />
          <span>{action}</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-gray-800 text-gray-300">
        <Activity className="w-2.5 h-2.5" />
        <span>{action}</span>
      </span>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-100 flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-[#10b981]" />
            <span>Immutable Security & Operations Audit Trail</span>
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Cryptographically timestamped log of authentication, workspace mutations, and access control changes.
          </p>
        </div>

        <button
          onClick={fetchLogs}
          className="p-1.5 rounded hover:bg-[#111827] border border-[#1f2937] text-gray-400 hover:text-gray-200 transition-colors"
          title="Refresh logs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
        </button>
      </div>

      <div className="enterprise-card overflow-hidden">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="table-header text-gray-400 font-mono uppercase text-[10px] tracking-wider">
              <th className="py-2.5 px-4">Timestamp (UTC)</th>
              <th className="py-2.5 px-4">Action Event</th>
              <th className="py-2.5 px-4">Actor</th>
              <th className="py-2.5 px-4">Target</th>
              <th className="py-2.5 px-4">Metadata Payload</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1f2937] text-gray-200 font-mono">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="py-6 text-center text-gray-500">
                  Streaming audit trail...
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-6 text-center text-gray-500">
                  No audit entries recorded for this organization yet.
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id} className="hover:bg-[#151c2a] transition-colors">
                  <td className="py-2.5 px-4 text-gray-400 text-[11px] whitespace-nowrap">
                    {new Date(log.created_at).toISOString().replace("T", " ").replace("Z", "")}
                  </td>
                  <td className="py-2.5 px-4 whitespace-nowrap">{getActionBadge(log.action)}</td>
                  <td className="py-2.5 px-4 text-gray-300">
                    {log.user_email || log.user_name || "System"}
                  </td>
                  <td className="py-2.5 px-4 text-gray-400 text-[11px]">
                    {log.target_type ? `${log.target_type}:${log.target_id?.slice(0, 8)}...` : "—"}
                  </td>
                  <td className="py-2.5 px-4 text-gray-400 text-[10px] truncate max-w-xs">
                    {JSON.stringify(log.details)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
