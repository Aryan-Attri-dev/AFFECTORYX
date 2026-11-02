"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { User, Organization } from "@/types";
import { api } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  activeOrg: Organization | null;
  organizations: Organization[];
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string, orgName?: string) => Promise<void>;
  logout: () => void;
  switchOrganization: (orgId: string) => Promise<void>;
  refreshOrganizations: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [activeOrg, setActiveOrg] = useState<Organization | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const initAuth = async () => {
    const token = api.getToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      const currentUser = await api.getCurrentUser();
      setUser(currentUser);

      const orgs = await api.listOrganizations();
      setOrganizations(orgs);

      const savedOrgId = api.getOrganizationId();
      let matchedOrg = orgs.find((o) => o.id === savedOrgId);
      if (!matchedOrg && orgs.length > 0) {
        matchedOrg = orgs[0];
        api.setOrganizationId(matchedOrg.id);
      }
      setActiveOrg(matchedOrg || null);
    } catch (err) {
      console.error("Auth session expired or invalid:", err);
      api.setToken(null);
      api.setOrganizationId(null);
      setUser(null);
      setActiveOrg(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await api.login({ email, password });
      setUser(res.user);

      const orgs = await api.listOrganizations();
      setOrganizations(orgs);

      let matchedOrg = orgs.find((o) => o.id === res.active_organization_id);
      if (!matchedOrg && orgs.length > 0) {
        matchedOrg = orgs[0];
      }
      setActiveOrg(matchedOrg || null);
      if (matchedOrg) {
        api.setOrganizationId(matchedOrg.id);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (fullName: string, email: string, password: string, orgName?: string) => {
    setIsLoading(true);
    try {
      const res = await api.register({ full_name: fullName, email, password, organization_name: orgName });
      setUser(res.user);

      const orgs = await api.listOrganizations();
      setOrganizations(orgs);

      let matchedOrg = orgs.find((o) => o.id === res.active_organization_id);
      if (!matchedOrg && orgs.length > 0) {
        matchedOrg = orgs[0];
      }
      setActiveOrg(matchedOrg || null);
      if (matchedOrg) {
        api.setOrganizationId(matchedOrg.id);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    api.setToken(null);
    api.setOrganizationId(null);
    setUser(null);
    setActiveOrg(null);
    setOrganizations([]);
  };

  const switchOrganization = async (orgId: string) => {
    const org = organizations.find((o) => o.id === orgId);
    if (org) {
      api.setOrganizationId(org.id);
      setActiveOrg(org);
    }
  };

  const refreshOrganizations = async () => {
    try {
      const orgs = await api.listOrganizations();
      setOrganizations(orgs);
      if (activeOrg) {
        const updated = orgs.find((o) => o.id === activeOrg.id);
        if (updated) setActiveOrg(updated);
      }
    } catch (e) {
      console.error("Failed to refresh organizations", e);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        activeOrg,
        organizations,
        isLoading,
        login,
        register,
        logout,
        switchOrganization,
        refreshOrganizations,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
