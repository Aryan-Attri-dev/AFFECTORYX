"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Member } from "@/types";
import { useAuth } from "@/context/auth-context";
import { Users2, UserPlus, Shield, Trash2, X, AlertCircle } from "lucide-react";

export function MembersList() {
  const { activeOrg, user } = useAuth();
  const [members, setMembers] = useState<Member[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"admin" | "member" | "viewer">("member");
  const [error, setError] = useState<string | null>(null);

  const fetchMembers = async () => {
    if (!activeOrg) return;
    setIsLoading(true);
    try {
      const data = await api.listMembers(activeOrg.id);
      setMembers(data);
    } catch (err) {
      console.error("Failed to load members:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMembers();
  }, [activeOrg]);

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeOrg || !inviteEmail.trim()) return;

    setError(null);
    try {
      const newMember = await api.addMember(activeOrg.id, inviteEmail.trim(), inviteRole);
      setMembers([...members, newMember]);
      setInviteEmail("");
      setIsAddModalOpen(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add member");
    }
  };

  const handleRoleChange = async (targetUserId: string, newRole: string) => {
    if (!activeOrg) return;
    try {
      const updated = await api.updateMemberRole(activeOrg.id, targetUserId, newRole);
      setMembers(members.map((m) => (m.user_id === targetUserId ? updated : m)));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to update role");
    }
  };

  const handleRemoveMember = async (targetUserId: string) => {
    if (!activeOrg || !confirm("Are you sure you want to remove this member?")) return;
    try {
      await api.removeMember(activeOrg.id, targetUserId);
      setMembers(members.filter((m) => m.user_id !== targetUserId));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to remove member");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-100 flex items-center space-x-2">
            <Users2 className="w-4 h-4 text-[#10b981]" />
            <span>Organization Members & Access Control</span>
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Manage who has permission to view dependency graphs, register services, and trigger impact simulations.
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#10b981] text-gray-950 font-medium text-xs hover:bg-[#059669] transition-colors"
        >
          <UserPlus className="w-3.5 h-3.5" />
          <span>Add Member</span>
        </button>
      </div>

      <div className="enterprise-card overflow-hidden">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="table-header text-gray-400 font-mono uppercase text-[10px] tracking-wider">
              <th className="py-2.5 px-4">Member Name</th>
              <th className="py-2.5 px-4">Email</th>
              <th className="py-2.5 px-4">Role</th>
              <th className="py-2.5 px-4">Joined Date</th>
              <th className="py-2.5 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1f2937] text-gray-200">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="py-6 text-center text-gray-500 font-mono">
                  Loading member directory...
                </td>
              </tr>
            ) : (
              members.map((m) => (
                <tr key={m.membership_id} className="hover:bg-[#151c2a] transition-colors">
                  <td className="py-3 px-4 font-medium text-gray-100">
                    {m.full_name}
                    {m.user_id === user?.id && (
                      <span className="ml-2 text-[10px] px-1.5 py-0.2 rounded bg-[#1f2937] text-gray-400 font-mono">
                        You
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 font-mono text-gray-400">{m.email}</td>
                  <td className="py-3 px-4">
                    {m.role === "owner" ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-amber-950/40 border border-amber-800 text-amber-400">
                        Owner
                      </span>
                    ) : (
                      <select
                        value={m.role}
                        onChange={(e) => handleRoleChange(m.user_id, e.target.value)}
                        className="bg-[#0b0f17] border border-[#1f2937] text-gray-300 text-xs rounded px-2 py-1 font-mono focus:outline-none focus:border-[#10b981]"
                      >
                        <option value="admin">Admin</option>
                        <option value="member">Member</option>
                        <option value="viewer">Viewer</option>
                      </select>
                    )}
                  </td>
                  <td className="py-3 px-4 text-gray-400 text-[11px]">
                    {new Date(m.joined_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4 text-right">
                    {m.role !== "owner" && m.user_id !== user?.id && (
                      <button
                        onClick={() => handleRemoveMember(m.user_id)}
                        className="p-1.5 rounded hover:bg-rose-950/40 text-gray-500 hover:text-rose-400 transition-colors"
                        title="Remove member"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Add Member Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-[#111827] border border-[#1f2937] rounded-lg max-w-md w-full overflow-hidden shadow-2xl">
            <div className="px-5 py-4 border-b border-[#1f2937] flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-100 flex items-center space-x-2">
                <UserPlus className="w-4 h-4 text-[#10b981]" />
                <span>Add Team Member</span>
              </h3>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="text-gray-400 hover:text-gray-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddMember} className="p-5 space-y-4">
              {error && (
                <div className="p-3 rounded bg-rose-950/40 border border-rose-800 text-xs text-rose-300 flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Registered Email Address <span className="text-rose-400">*</span>
                </label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="engineer@company.com"
                  className="w-full px-3 py-2 text-xs rounded bg-[#0b0f17] border border-[#1f2937] text-gray-100 focus:outline-none focus:border-[#10b981]"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Role</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as "admin" | "member" | "viewer")}
                  className="w-full px-3 py-2 text-xs rounded bg-[#0b0f17] border border-[#1f2937] text-gray-100 focus:outline-none focus:border-[#10b981]"
                >
                  <option value="member">Member (Can create projects and run simulations)</option>
                  <option value="admin">Admin (Can manage settings and invite members)</option>
                  <option value="viewer">Viewer (Read-only access)</option>
                </select>
              </div>

              <div className="pt-3 border-t border-[#1f2937] flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-3 py-1.5 text-xs text-gray-400 hover:text-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs font-medium bg-[#10b981] text-gray-950 rounded hover:bg-[#059669]"
                >
                  Add Member
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
