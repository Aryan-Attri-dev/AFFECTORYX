"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import { Header } from "@/components/navigation/header";
import { Sidebar } from "@/components/navigation/sidebar";
import { ProjectList } from "@/components/projects/project-list";
import { Boxes } from "lucide-react";

export default function ProjectsPage() {
  const router = useRouter();
  const { user, activeOrg, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [user, isLoading, router]);

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-[#0b0f17] flex items-center justify-center font-mono text-xs text-gray-500">
        Loading engineering session...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0b0f17] flex flex-col">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">
          <div className="pb-4 border-b border-[#1f2937]">
            <div className="flex items-center space-x-2">
              <Boxes className="w-5 h-5 text-[#10b981]" />
              <h1 className="text-xl font-bold text-gray-100 tracking-tight">
                Projects & Microservice Systems
              </h1>
              <span className="text-[10px] px-2 py-0.5 rounded bg-[#1a2234] border border-[#1f2937] text-gray-400 font-mono">
                {activeOrg?.name}
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-1">
              Registered engineering services, code repositories, branch configurations, and runtime target environments.
            </p>
          </div>

          <ProjectList />
        </main>
      </div>
    </div>
  );
}
