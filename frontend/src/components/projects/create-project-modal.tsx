"use client";

import React, { useState } from "react";
import { api } from "@/lib/api";
import { Project } from "@/types";
import { X, GitBranch, FolderGit2, AlertCircle } from "lucide-react";

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (project: Project) => void;
}

export function CreateProjectModal({ isOpen, onClose, onSuccess }: CreateProjectModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [repositoryUrl, setRepositoryUrl] = useState("");
  const [defaultBranch, setDefaultBranch] = useState("main");
  const [environments, setEnvironments] = useState("production, staging");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Project name is required");
      return;
    }

    setError(null);
    setIsSubmitting(true);
    try {
      const envArray = environments
        .split(",")
        .map((env) => env.trim())
        .filter((env) => env.length > 0);

      const project = await api.createProject({
        name: name.trim(),
        description: description.trim() || undefined,
        repository_url: repositoryUrl.trim() || undefined,
        default_branch: defaultBranch.trim() || "main",
        environments: envArray.length > 0 ? envArray : ["production", "staging"],
      });

      onSuccess(project);
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-[#111827] border border-[#1f2937] rounded-lg max-w-lg w-full overflow-hidden shadow-2xl">
        <div className="px-5 py-4 border-b border-[#1f2937] flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FolderGit2 className="w-4 h-4 text-[#10b981]" />
            <h3 className="text-sm font-semibold text-gray-100">Create New Engineering Project</h3>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-200 p-1 rounded hover:bg-[#1f2937]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <div className="p-3 rounded bg-rose-950/40 border border-rose-800 text-xs text-rose-300 flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              Project / Service Name <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. core-billing-engine"
              className="w-full px-3 py-2 text-xs rounded bg-[#0b0f17] border border-[#1f2937] text-gray-100 placeholder-gray-500 focus:outline-none focus:border-[#10b981]"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Service purpose, architecture scope, domain boundary"
              rows={2}
              className="w-full px-3 py-2 text-xs rounded bg-[#0b0f17] border border-[#1f2937] text-gray-100 placeholder-gray-500 focus:outline-none focus:border-[#10b981]"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              Repository URL (Git/GitHub)
            </label>
            <input
              type="url"
              value={repositoryUrl}
              onChange={(e) => setRepositoryUrl(e.target.value)}
              placeholder="https://github.com/organization/repo"
              className="w-full px-3 py-2 text-xs rounded bg-[#0b0f17] border border-[#1f2937] text-gray-100 placeholder-gray-500 focus:outline-none focus:border-[#10b981]"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">
                Default Branch
              </label>
              <div className="relative">
                <GitBranch className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-gray-500" />
                <input
                  type="text"
                  value={defaultBranch}
                  onChange={(e) => setDefaultBranch(e.target.value)}
                  className="w-full pl-8 pr-3 py-2 text-xs rounded bg-[#0b0f17] border border-[#1f2937] text-gray-100 focus:outline-none focus:border-[#10b981]"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-300 mb-1">
                Environments (Comma-separated)
              </label>
              <input
                type="text"
                value={environments}
                onChange={(e) => setEnvironments(e.target.value)}
                placeholder="production, staging, qa"
                className="w-full px-3 py-2 text-xs rounded bg-[#0b0f17] border border-[#1f2937] text-gray-100 focus:outline-none focus:border-[#10b981]"
              />
            </div>
          </div>

          <div className="pt-3 border-t border-[#1f2937] flex items-center justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-xs text-gray-400 hover:text-gray-200 hover:bg-[#1f2937] rounded transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-1.5 text-xs font-medium bg-[#10b981] text-gray-950 rounded hover:bg-[#059669] transition-colors disabled:opacity-50"
            >
              {isSubmitting ? "Creating..." : "Create Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
