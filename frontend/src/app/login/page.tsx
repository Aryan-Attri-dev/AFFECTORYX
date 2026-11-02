"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Shield, Lock, Mail, User, Building, AlertCircle, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login, register } = useAuth();
  const [tab, setTab] = useState<"login" | "register">("login");

  // Form states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (tab === "login") {
        await login(email, password);
      } else {
        if (!fullName.trim()) {
          throw new Error("Full name is required");
        }
        await register(fullName, email, password, organizationName || undefined);
      }
      router.push("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f17] flex flex-col justify-center items-center px-4 py-12">
      {/* Brand Header */}
      <div className="mb-8 text-center">
        <div className="inline-flex items-center space-x-2.5 mb-3">
          <div className="w-8 h-8 rounded bg-[#10b981]/10 border border-[#10b981]/30 flex items-center justify-center text-[#10b981] font-mono font-bold text-base">
            AX
          </div>
          <span className="font-bold tracking-wider text-xl text-gray-100 uppercase">
            AFFECTORYX
          </span>
        </div>
        <p className="text-xs text-gray-400 font-mono tracking-wide">
          ENGINEERING INTELLIGENCE PLATFORM
        </p>
      </div>

      {/* Auth Card */}
      <div className="enterprise-card w-full max-w-md p-6 sm:p-8 shadow-2xl">
        {/* Tab Toggle */}
        <div className="grid grid-cols-2 gap-1 p-1 bg-[#0b0f17] border border-[#1f2937] rounded mb-6 text-xs font-mono">
          <button
            type="button"
            onClick={() => {
              setTab("login");
              setError(null);
            }}
            className={`py-1.5 rounded transition-colors ${
              tab === "login"
                ? "bg-[#111827] text-gray-100 font-semibold shadow-xs border border-[#1f2937]"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            SIGN IN
          </button>
          <button
            type="button"
            onClick={() => {
              setTab("register");
              setError(null);
            }}
            className={`py-1.5 rounded transition-colors ${
              tab === "register"
                ? "bg-[#111827] text-gray-100 font-semibold shadow-xs border border-[#1f2937]"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            NEW WORKSPACE
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded bg-rose-950/40 border border-rose-800 text-xs text-rose-300 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {tab === "register" && (
            <>
              <div>
                <label className="block text-gray-300 font-medium mb-1">
                  Full Name <span className="text-rose-400">*</span>
                </label>
                <div className="relative">
                  <User className="w-3.5 h-3.5 absolute left-3 top-2.5 text-gray-500" />
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Linus Torvalds"
                    className="w-full pl-9 pr-3 py-2 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-100 placeholder-gray-600 focus:outline-none focus:border-[#10b981]"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-gray-300 font-medium mb-1">
                  Organization / Company Name
                </label>
                <div className="relative">
                  <Building className="w-3.5 h-3.5 absolute left-3 top-2.5 text-gray-500" />
                  <input
                    type="text"
                    value={organizationName}
                    onChange={(e) => setOrganizationName(e.target.value)}
                    placeholder="e.g. Acme Corp (optional)"
                    className="w-full pl-9 pr-3 py-2 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-100 placeholder-gray-600 focus:outline-none focus:border-[#10b981]"
                  />
                </div>
              </div>
            </>
          )}

          <div>
            <label className="block text-gray-300 font-medium mb-1">
              Email Address <span className="text-rose-400">*</span>
            </label>
            <div className="relative">
              <Mail className="w-3.5 h-3.5 absolute left-3 top-2.5 text-gray-500" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="architect@company.com"
                className="w-full pl-9 pr-3 py-2 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-100 placeholder-gray-600 focus:outline-none focus:border-[#10b981]"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-gray-300 font-medium mb-1">
              Password <span className="text-rose-400">*</span>
            </label>
            <div className="relative">
              <Lock className="w-3.5 h-3.5 absolute left-3 top-2.5 text-gray-500" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 rounded bg-[#0b0f17] border border-[#1f2937] text-gray-100 placeholder-gray-600 focus:outline-none focus:border-[#10b981]"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full mt-2 py-2.5 rounded bg-[#10b981] text-gray-950 font-semibold flex items-center justify-center space-x-1.5 hover:bg-[#059669] transition-colors disabled:opacity-50"
          >
            <span>{isLoading ? "Authenticating..." : tab === "login" ? "Sign In to Console" : "Create Workspace"}</span>
            {!isLoading && <ArrowRight className="w-3.5 h-3.5" />}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-[#1f2937] text-center text-[10px] text-gray-500 font-mono">
          AIR-GAPPED TENANT ISOLATION • AES-256 SESSION TOKENS
        </div>
      </div>
    </div>
  );
}
