"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Project } from "@/types";
import { useAuth } from "@/context/auth-context";
import { CreateProjectModal } from "./create-project-modal";
import {
  Boxes,
  Plus,
  GitBranch,
  ExternalLink,
  Trash2,
  RefreshCw,
  Search,
  Server,
  Layers,
} from "lucide-react";

export function ProjectList() {
  const { activeOrg } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const fetchProjects = async () => {
    if (!activeOrg) return;
    setIsLoading(true);
    try {
      const data = await api.listProjects();
      setProjects(data);
    } catch (err) {
      console.error("Failed to load projects:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [activeOrg]);

  const handleDelete = async (id: string) => {
    try {
      await api.deleteProject(id);
      setProjects(projects.filter((p) => p.id !== id));
      setDeleteConfirmId(null);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete project");
    }
  };

  const filteredProjects = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.slug.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-4">
      {/* Top action bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter services or repositories..."
              className="pl-8 pr-3 py-1.5 text-xs rounded bg-[#111827] border border-[#1f2937] text-gray-200 placeholder-gray-500 focus:outline-none focus:border-[#10b981] w-64"
            />
          </div>
          <button
            onClick={fetchProjects}
            className="p-1.5 rounded hover:bg-[#111827] border border-[#1f2937] text-gray-400 hover:text-gray-200 transition-colors"
            title="Refresh list"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#10b981] text-gray-950 font-medium text-xs hover:bg-[#059669] transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Project</span>
        </button>
      </div>

      {/* Projects Table */}
      <div className="enterprise-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="table-header text-gray-400 font-mono uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-4">Service / Project</th>
                <th className="py-2.5 px-4">Repository</th>
                <th className="py-2.5 px-4">Environments</th>
                <th className="py-2.5 px-4">Branch</th>
                <th className="py-2.5 px-4">Registered</th>
                <th className="py-2.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1f2937] text-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-gray-500 font-mono">
                    Querying engineering catalog...
                  </td>
                </tr>
              ) : filteredProjects.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-500">
                    <Boxes className="w-8 h-8 mx-auto mb-2 text-gray-600" />
                    <p className="text-sm font-medium text-gray-400">No projects registered yet</p>
                    <p className="text-xs text-gray-600 mt-1">
                      Register a microservice or system repository to begin tracking dependencies.
                    </p>
                  </td>
                </tr>
              ) : (
                filteredProjects.map((project) => (
                  <tr key={project.id} className="hover:bg-[#151c2a] transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2.5">
                        <div className="w-7 h-7 rounded bg-[#1f2937] flex items-center justify-center text-gray-400 shrink-0">
                          <Server className="w-3.5 h-3.5" />
                        </div>
                        <div>
                          <div className="font-semibold text-gray-100 flex items-center space-x-2">
                            <span>{project.name}</span>
                            <span className="text-[10px] px-1 rounded bg-[#1f2937] text-gray-400 font-mono">
                              {project.slug}
                            </span>
                          </div>
                          {project.description && (
                            <p className="text-gray-400 text-[11px] truncate max-w-sm mt-0.5">
                              {project.description}
                            </p>
                          )}
                        </div>
                      </div>
                    </td>

                    <td className="py-3 px-4 font-mono text-[11px]">
                      {project.repository_url ? (
                        <a
                          href={project.repository_url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center space-x-1 text-[#06b6d4] hover:underline"
                        >
                          <span className="truncate max-w-[180px]">
                            {project.repository_url.replace("https://github.com/", "")}
                          </span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (
                        <span className="text-gray-600">Manual Ingestion</span>
                      )}
                    </td>

                    <td className="py-3 px-4">
                      <div className="flex flex-wrap gap-1">
                        {project.environments.map((env) => (
                          <span
                            key={env}
                            className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-[#1a2234] border border-[#1f2937] text-gray-300"
                          >
                            {env}
                          </span>
                        ))}
                      </div>
                    </td>

                    <td className="py-3 px-4 font-mono text-gray-400 flex items-center space-x-1 pt-4">
                      <GitBranch className="w-3 h-3 text-gray-500" />
                      <span>{project.default_branch}</span>
                    </td>

                    <td className="py-3 px-4 text-gray-400 text-[11px]">
                      {new Date(project.created_at).toLocaleDateString()}
                    </td>

                    <td className="py-3 px-4 text-right">
                      {deleteConfirmId === project.id ? (
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => handleDelete(project.id)}
                            className="text-xs px-2 py-1 rounded bg-rose-900/60 text-rose-200 border border-rose-700 hover:bg-rose-800"
                          >
                            Confirm Delete
                          </button>
                          <button
                            onClick={() => setDeleteConfirmId(null)}
                            className="text-xs px-2 py-1 rounded text-gray-400 hover:bg-[#1f2937]"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setDeleteConfirmId(project.id)}
                          className="p-1.5 rounded hover:bg-rose-950/40 text-gray-500 hover:text-rose-400 transition-colors"
                          title="Delete Project"
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
      </div>

      <CreateProjectModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={(newProj) => {
          setProjects([newProj, ...projects]);
        }}
      />
    </div>
  );
}
