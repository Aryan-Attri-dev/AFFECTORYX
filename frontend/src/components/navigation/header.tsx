"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/auth-context";
import { Building2, ChevronDown, Shield, LogOut, CheckCircle2, User } from "lucide-react";

export function Header() {
  const { user, activeOrg, organizations, switchOrganization, logout } = useAuth();
  const [isOrgDropdownOpen, setIsOrgDropdownOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  return (
    <header className="h-14 border-b border-[#1f2937] bg-[#0b0f17] px-4 flex items-center justify-between z-30 sticky top-0">
      {/* Brand & Organization Selector */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded bg-[#10b981]/10 border border-[#10b981]/30 flex items-center justify-center text-[#10b981] font-mono font-bold text-sm">
            AX
          </div>
          <span className="font-semibold tracking-wider text-sm text-gray-100 uppercase">
            AFFECTORYX
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#1f2937] text-gray-400 font-mono">
            CORE v0.1
          </span>
        </div>

        <div className="h-4 w-px bg-[#1f2937]" />

        {/* Multi-Tenant Organization Switcher */}
        {activeOrg && (
          <div className="relative">
            <button
              onClick={() => setIsOrgDropdownOpen(!isOrgDropdownOpen)}
              className="flex items-center space-x-2 px-2.5 py-1.5 rounded bg-[#111827] border border-[#1f2937] hover:border-gray-700 text-xs text-gray-200 transition-colors"
            >
              <Building2 className="w-3.5 h-3.5 text-gray-400" />
              <span className="font-medium max-w-[150px] truncate">{activeOrg.name}</span>
              <span className="text-[10px] px-1 rounded bg-[#1a2234] text-[#10b981] uppercase font-mono">
                {activeOrg.user_role || "member"}
              </span>
              <ChevronDown className="w-3 h-3 text-gray-400" />
            </button>

            {isOrgDropdownOpen && (
              <div
                className="absolute left-0 mt-1 w-64 rounded bg-[#111827] border border-[#1f2937] shadow-xl py-1 z-50"
                onMouseLeave={() => setIsOrgDropdownOpen(false)}
              >
                <div className="px-3 py-1.5 text-[10px] font-mono uppercase tracking-wider text-gray-400 border-b border-[#1f2937]">
                  Switch Organization
                </div>
                {organizations.map((org) => (
                  <button
                    key={org.id}
                    onClick={() => {
                      switchOrganization(org.id);
                      setIsOrgDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-[#1a2234] transition-colors ${
                      org.id === activeOrg.id ? "text-[#10b981] bg-[#10b981]/5" : "text-gray-300"
                    }`}
                  >
                    <div className="truncate">
                      <div className="font-medium truncate">{org.name}</div>
                      <div className="text-[10px] text-gray-500 font-mono">slug: {org.slug}</div>
                    </div>
                    {org.id === activeOrg.id && <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0 ml-2" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right System Info & User Menu */}
      <div className="flex items-center space-x-4">
        {/* Real-time System status badge */}
        <div className="flex items-center space-x-1.5 px-2 py-1 rounded bg-[#111827] border border-[#1f2937] text-[11px] text-gray-300 font-mono">
          <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
          <span>AIR-GAP VALIDATION: READY</span>
        </div>

        {/* User profile dropdown */}
        {user && (
          <div className="relative">
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center space-x-2 px-2.5 py-1.5 rounded hover:bg-[#111827] border border-transparent hover:border-[#1f2937] text-xs text-gray-200 transition-colors"
            >
              <div className="w-6 h-6 rounded bg-[#1a2234] border border-[#1f2937] flex items-center justify-center text-xs font-mono text-gray-300">
                {user.full_name.charAt(0).toUpperCase()}
              </div>
              <span className="max-w-[120px] truncate">{user.full_name}</span>
              <ChevronDown className="w-3 h-3 text-gray-400" />
            </button>

            {isUserMenuOpen && (
              <div
                className="absolute right-0 mt-1 w-52 rounded bg-[#111827] border border-[#1f2937] shadow-xl py-1 z-50 text-xs"
                onMouseLeave={() => setIsUserMenuOpen(false)}
              >
                <div className="px-3 py-2 border-b border-[#1f2937]">
                  <div className="font-medium text-gray-200 truncate">{user.full_name}</div>
                  <div className="text-[11px] text-gray-400 font-mono truncate">{user.email}</div>
                </div>
                <button
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    logout();
                  }}
                  className="w-full text-left px-3 py-2 flex items-center space-x-2 text-rose-400 hover:bg-rose-950/20 transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign out</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
