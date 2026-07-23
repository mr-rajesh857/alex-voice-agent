"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant" | "system";
  text: string;
  timestamp: string;
  confirmation?: {
    toolName: string;
    summary: string;
    details: Record<string, any>;
    status?: "pending" | "approved" | "rejected";
  };
}

export default function ChatDashboardPage() {
  const { user, token, isLoading, logout } = useAuth();
  const router = useRouter();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isLoading && !token) {
      router.push("/login");
    }
  }, [isLoading, token, router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

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

  const handleSendMessage = (textToSend?: string) => {
    const query = textToSend || inputText;
    if (!query.trim()) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputText("");
    setIsTyping(true);

    // Simulated Assistant & LangGraph flow preview
    setTimeout(() => {
      setIsTyping(false);
      
      const lower = query.toLowerCase();
      let reply: ChatMessage;

      if (lower.includes("meeting") || lower.includes("schedule") || lower.includes("calendar")) {
        reply = {
          id: (Date.now() + 1).toString(),
          sender: "assistant",
          text: "I have prepared the calendar event based on your request. Please confirm before I fix this in your calendar:",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          confirmation: {
            toolName: "calendar-mcp.create_event",
            summary: "Schedule Sync Meeting with Team tomorrow at 3:00 PM",
            details: { title: "Team Sync", start: "Tomorrow, 3:00 PM", duration: "30 mins" },
            status: "pending",
          },
        };
      } else if (lower.includes("reminder")) {
        reply = {
          id: (Date.now() + 1).toString(),
          sender: "assistant",
          text: "I've extracted your reminder details: **Reminder**: Review project proposal today at 6:00 PM. Shall I save this?",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          confirmation: {
            toolName: "reminders-mcp.set_reminder",
            summary: "Set reminder: 'Review project proposal' today at 6:00 PM",
            details: { text: "Review project proposal", time: "Today, 6:00 PM" },
            status: "pending",
          },
        };
      } else {
        reply = {
          id: (Date.now() + 1).toString(),
          sender: "assistant",
          text: `Hello ${user?.name || "there"}! I'm Alex, your AI assistant. I can manage your calendar, set reminders, resolve contacts, search the web, and send messages. How can I help you today?`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
      }

      setMessages((prev) => [...prev, reply]);
    }, 1200);
  };

  const handleConfirmationAction = (msgId: string, action: "approved" | "rejected") => {
    setMessages((prev) =>
      prev.map((msg) => {
        if (msg.id === msgId && msg.confirmation) {
          return {
            ...msg,
            confirmation: {
              ...msg.confirmation,
              status: action,
            },
          };
        }
        return msg;
      })
    );

    const resultMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: "assistant",
      text: action === "approved" 
        ? "✅ Action executed successfully! The tool audit log has been updated." 
        : "❌ Action cancelled by user. No changes were made.",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, resultMsg]);
  };

  const promptSuggestions = [
    "📅 Schedule a meeting with Alex tomorrow at 3 PM",
    "⏰ Set a reminder to submit code review by 5 PM",
    "🔍 Search web for latest LangGraph updates",
    "✉️ Draft an update email to the product team",
  ];

  return (
    <div className="flex h-screen w-full overflow-hidden bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? "w-64" : "w-16"} flex flex-col border-r border-slate-800/80 bg-slate-900/60 backdrop-blur-xl transition-all duration-300`}>
        {/* Sidebar Header */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-slate-800/80">
          {sidebarOpen ? (
            <div className="flex items-center space-x-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 shadow-md shadow-indigo-500/20">
                <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <span className="font-bold text-white tracking-wide">Alex AI</span>
            </div>
          ) : (
            <div className="mx-auto flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 text-white">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={sidebarOpen ? "M11 19l-7-7 7-7m8 14l-7-7 7-7" : "M13 5l7 7-7 7M5 5l7 7-7 7"} />
            </svg>
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={() => setMessages([])}
            className={`flex w-full items-center justify-center space-x-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 ${sidebarOpen ? "px-4" : "px-2"} py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 hover:from-indigo-600 hover:to-purple-700 transition-all`}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {sidebarOpen && <span>New Chat</span>}
          </button>
        </div>

        {/* Tools Status */}
        {sidebarOpen && (
          <div className="flex-1 overflow-y-auto px-3 py-2 space-y-4">
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 px-2">Connected MCP Tools</span>
              <div className="mt-2 space-y-1 text-xs">
                {[
                  { name: "calendar-mcp", color: "bg-emerald-400" },
                  { name: "contacts-mcp", color: "bg-emerald-400" },
                  { name: "reminders-mcp", color: "bg-emerald-400" },
                  { name: "search-rag-mcp", color: "bg-emerald-400" },
                  { name: "email-messaging-mcp", color: "bg-emerald-400" },
                ].map((tool) => (
                  <div key={tool.name} className="flex items-center justify-between rounded-lg px-2.5 py-1.5 text-slate-300 hover:bg-slate-800/60">
                    <span className="truncate">{tool.name}</span>
                    <span className={`h-2 w-2 rounded-full ${tool.color}`} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* User Profile Footer */}
        <div className="mt-auto border-t border-slate-800/80 p-3">
          {sidebarOpen ? (
            <div className="flex items-center justify-between">
              <div className="flex flex-col truncate">
                <span className="text-xs font-semibold text-white truncate">{user?.name}</span>
                <span className="text-[11px] text-slate-400 truncate">{user?.email}</span>
              </div>
              <button
                onClick={logout}
                title="Sign Out"
                className="rounded-lg p-1.5 text-slate-400 hover:bg-red-500/20 hover:text-red-400 transition-colors"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          ) : (
            <button
              onClick={logout}
              title="Sign Out"
              className="mx-auto flex h-9 w-9 items-center justify-center rounded-xl text-slate-400 hover:bg-red-500/20 hover:text-red-400"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          )}
        </div>
      </aside>

      {/* Main Chat Content */}
      <main className="flex flex-1 flex-col overflow-hidden bg-slate-950">
        {/* Top Header */}
        <header className="flex h-16 items-center justify-between border-b border-slate-800/80 bg-slate-950/80 px-6 backdrop-blur-xl">
          <div className="flex items-center space-x-3">
            <h2 className="text-base font-bold text-white">Alex Chat Assistant</h2>
            <span className="flex items-center space-x-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              LangGraph Ready
            </span>
          </div>
        </header>

        {/* Scrollable Message List */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="my-auto flex flex-col items-center justify-center pt-16 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-500 p-0.5 shadow-xl shadow-indigo-500/25 mb-6">
                <div className="flex h-full w-full items-center justify-center rounded-[14px] bg-slate-950">
                  <svg className="h-8 w-8 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
              </div>
              <h3 className="text-2xl font-bold text-white">How can I help you today, {user?.name}?</h3>
              <p className="mt-2 text-sm text-slate-400 max-w-md">
                I can schedule events, set reminders, search the web, manage contacts, and execute multi-tool workflows.
              </p>

              {/* Prompt Suggestions */}
              <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
                {promptSuggestions.map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(suggestion.replace(/^[^\s]+\s/, ""))}
                    className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/60 p-4 text-left text-xs text-slate-300 transition-all hover:border-indigo-500/50 hover:bg-slate-900 hover:text-white"
                  >
                    <span>{suggestion}</span>
                    <svg className="h-4 w-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex w-full ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                <div className={`flex max-w-2xl items-start space-x-3 ${msg.sender === "user" ? "flex-row-reverse space-x-reverse" : "flex-row"}`}>
                  {/* Avatar */}
                  <div className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl text-xs font-bold ${
                    msg.sender === "user"
                      ? "bg-gradient-to-tr from-purple-500 to-indigo-500 text-white"
                      : "bg-slate-800 text-indigo-400 border border-slate-700"
                  }`}>
                    {msg.sender === "user" ? user?.name?.[0]?.toUpperCase() || "U" : "A"}
                  </div>

                  {/* Bubble Content */}
                  <div className="space-y-3">
                    <div className={`rounded-2xl px-5 py-3.5 text-sm leading-relaxed ${
                      msg.sender === "user"
                        ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
                        : "bg-slate-900 border border-slate-800 text-slate-200"
                    }`}>
                      <p>{msg.text}</p>
                    </div>

                    {/* Interactive Confirmation Card (if any) */}
                    {msg.confirmation && (
                      <div className="rounded-2xl border border-indigo-500/40 bg-slate-900/90 p-4 shadow-xl backdrop-blur-xl space-y-3">
                        <div className="flex items-center justify-between text-xs font-semibold text-indigo-400">
                          <span className="uppercase tracking-wider">Security Confirmation Required</span>
                          <span className="rounded-md bg-indigo-500/10 px-2 py-0.5 border border-indigo-500/20">{msg.confirmation.toolName}</span>
                        </div>
                        <p className="text-sm font-medium text-white">{msg.confirmation.summary}</p>
                        
                        {msg.confirmation.status === "pending" ? (
                          <div className="flex items-center space-x-3 pt-1">
                            <button
                              onClick={() => handleConfirmationAction(msg.id, "approved")}
                              className="rounded-xl bg-emerald-500 px-4 py-2 text-xs font-bold text-slate-950 hover:bg-emerald-400 transition-colors shadow-lg shadow-emerald-500/20"
                            >
                              ✅ Confirm Action
                            </button>
                            <button
                              onClick={() => handleConfirmationAction(msg.id, "rejected")}
                              className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-red-500/20 hover:text-red-400 transition-colors"
                            >
                              ❌ Cancel
                            </button>
                          </div>
                        ) : (
                          <div className={`text-xs font-semibold ${msg.confirmation.status === "approved" ? "text-emerald-400" : "text-red-400"}`}>
                            {msg.confirmation.status === "approved" ? "Approved & Executed" : "Cancelled by User"}
                          </div>
                        )}
                      </div>
                    )}

                    <span className="block text-[10px] text-slate-500 px-1">{msg.timestamp}</span>
                  </div>
                </div>
              </div>
            ))
          )}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex items-center space-x-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-800 text-indigo-400 border border-slate-700 font-bold text-xs">
                A
              </div>
              <div className="flex items-center space-x-1.5 rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-slate-400">
                <span className="h-2 w-2 animate-bounce rounded-full bg-indigo-400 [animation-delay:-0.3s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-indigo-400 [animation-delay:-0.15s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-indigo-400" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <footer className="p-4 border-t border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="mx-auto max-w-4xl flex items-center space-x-3"
          >
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Ask Alex to schedule meetings, set reminders, search..."
              className="flex-1 rounded-xl border border-slate-800 bg-slate-900/80 px-4 py-3.5 text-sm text-white placeholder-slate-500 transition-all focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
            <button
              type="submit"
              disabled={!inputText.trim()}
              className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/25 transition-all hover:from-indigo-600 hover:to-purple-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9-2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </form>
        </footer>
      </main>
    </div>
  );
}
