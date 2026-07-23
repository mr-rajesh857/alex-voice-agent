"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function HomeDashboard() {
  const { user, token, isLoading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !token) {
      router.push("/login");
    }
  }, [isLoading, token, router]);

  if (isLoading || !token) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 p-4">
        <div className="flex items-center space-x-3 text-slate-400">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          <span className="text-sm font-medium">Authenticating session...</span>
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col bg-slate-950 text-slate-100">
      {/* Top Navbar */}
      <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 shadow-md shadow-indigo-500/20">
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-none">Alex Voice AI</h1>
              <span className="text-xs text-emerald-400 flex items-center gap-1.5 mt-1 font-medium">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                JWT Authenticated
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-sm font-semibold text-white">{user?.name}</span>
              <span className="text-xs text-slate-400">{user?.email}</span>
            </div>
            <button
              onClick={logout}
              className="rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-xs font-semibold text-slate-300 transition-colors hover:border-red-500/50 hover:bg-red-500/10 hover:text-red-400"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Dashboard Hero */}
      <div className="flex-1 mx-auto w-full max-w-7xl px-6 py-12">
        <div className="rounded-3xl border border-slate-800 bg-gradient-to-b from-slate-900/80 to-slate-950/80 p-8 md:p-12 shadow-2xl backdrop-blur-xl">
          <div className="max-w-3xl">
            <span className="inline-flex items-center rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-400 mb-6">
              Authenticated Session
            </span>
            <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white leading-tight">
              Hello, {user?.name}! Your Alex Voice Agent is ready.
            </h2>
            <p className="mt-4 text-base text-slate-400 leading-relaxed">
              You are securely logged in with a JWT access token. Next, we will connect the LangGraph real-time orchestrator, STT/TTS audio pipeline, and FastMCP tools.
            </p>
          </div>

          {/* User Info & Token Details Card */}
          <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-6">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">User ID</div>
              <div className="text-sm font-mono text-indigo-300 truncate">{user?.id}</div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-6">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Account Email</div>
              <div className="text-sm font-medium text-slate-200 truncate">{user?.email}</div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-6">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">JWT Authorization</div>
              <div className="text-sm font-mono text-emerald-400 truncate">Bearer Token Active</div>
            </div>
          </div>

          {/* Voice Interface Preview Card */}
          <div className="mt-8 flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 bg-slate-950/40 p-12 text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 shadow-xl mb-4">
              <svg className="h-10 w-10 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-white">Voice Pipeline & LangGraph Engine</h3>
            <p className="mt-2 text-sm text-slate-400 max-w-md">
              Authentication setup is complete! We will now proceed with LangGraph state orchestration and FastMCP integrations.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
