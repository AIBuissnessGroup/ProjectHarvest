"use client"

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import {
  ArrowUpRight,
  Bot,
  Plus,
  Sparkles,
  LayoutGrid,
  Settings,
  User,
  X,
  MessageSquare,
  Clock,
  Menu,
  Trash2,
  Edit2,
  Check,
  Loader2
} from "lucide-react";
import { WorkspaceCanvas } from "@/components/workspace/WorkspaceCanvas";
import { chatAPI } from "@/lib/api-client";
import type { ChatMessage as APIChatMessage } from "@/lib/api-client";
import ReactMarkdown from 'react-markdown';

export default function ProjectHarvest() {
  const [activePage, setActivePage] = useState("main");
  const [pages, setPages] = useState([
    { id: "main", name: "Main Dashboard" },
  ]);

  // Store visualizations per page
  const [pageVisualizations, setPageVisualizations] = useState<Record<string, Array<any>>>({
    "main": [] // Main page starts empty
  });

  const [activeChat, setActiveChat] = useState("");
  const [showChatSidebar, setShowChatSidebar] = useState(false);
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editingChatName, setEditingChatName] = useState("");
  const [chats, setChats] = useState([
    { id: "chat-1", name: "New Chat", timestamp: "Just now", preview: "Start a new conversation..." },
  ]);

  // Chat input and loading state
  const [chatInput, setChatInput] = useState("");
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  // Resizable sidebar state
  const [sidebarWidth, setSidebarWidth] = useState(384); // 384px = w-96
  const [isResizing, setIsResizing] = useState(false);

  // Store messages per chat
  const [chatMessages, setChatMessages] = useState<Record<string, Array<{ type: 'ai' | 'user', content: string }>>>({
    "chat-1": [
      { type: 'ai', content: "👋 **Welcome!** I'm your AI Analytics Assistant.\n\nI can analyze Fortnite Creative maps, predict future performance, detect anomalies, and much more.\n\nNot sure where to start? Just ask me what I'm capable of!" }
    ]
  });

  // Automatically set first chat as active when component mounts
  useEffect(() => {
    if (activeChat === "" && chats.length > 0) {
      setActiveChat(chats[0].id);
    }
  }, [activeChat, chats]);

  const [editingPageId, setEditingPageId] = useState<string | null>(null);
  const [editingPageName, setEditingPageName] = useState("");

  const addNewPage = () => {
    const newPageId = `page-${Date.now()}`;
    const newPage = {
      id: newPageId,
      name: `Page ${pages.length + 1}`
    };
    setPages([...pages, newPage]);
    // Initialize empty visualizations for new page
    setPageVisualizations({
      ...pageVisualizations,
      [newPageId]: []
    });
    setActivePage(newPageId);
  };

  const removePage = (pageId: string) => {
    if (pages.length > 1) {
      setPages(pages.filter(p => p.id !== pageId));
      // Remove visualizations for this page
      const newPageVisualizations = { ...pageVisualizations };
      delete newPageVisualizations[pageId];
      setPageVisualizations(newPageVisualizations);

      if (activePage === pageId) {
        setActivePage(pages[0].id);
      }
    }
  };

  const addNewChat = () => {
    const newChatId = `chat-${Date.now()}`;
    const newChat = {
      id: newChatId,
      name: "New Chat",
      timestamp: "Just now",
      preview: "Start a new conversation..."
    };
    setChats([newChat, ...chats]);
    setChatMessages({
      ...chatMessages,
      [newChatId]: [
        { type: 'ai', content: "👋 **Welcome!** I'm your AI Analytics Assistant.\n\nI can analyze Fortnite Creative maps, predict future performance, detect anomalies, and much more.\n\nNot sure where to start? Just ask me what I'm capable of!" }
      ]
    });
    setActiveChat(newChatId);
    setShowChatSidebar(false);
  };

  // Handle sending messages to the AI
  const handleSendMessage = async () => {
    if (!chatInput.trim() || isSendingMessage) return;

    const userMessage = chatInput.trim();
    setChatInput("");
    setIsSendingMessage(true);

    // Add user message to chat
    const currentMessages = chatMessages[activeChat] || [];
    setChatMessages({
      ...chatMessages,
      [activeChat]: [...currentMessages, { type: 'user', content: userMessage }]
    });

    // Update chat preview
    setChats(chats.map(c =>
      c.id === activeChat
        ? { ...c, preview: userMessage.slice(0, 50) + (userMessage.length > 50 ? '...' : ''), timestamp: 'Just now' }
        : c
    ));

    try {
      // Convert chat messages to API format
      const conversationHistory: APIChatMessage[] = currentMessages.map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content
      }));

      // Call the backend API
      const response = await chatAPI.sendMessage(userMessage, conversationHistory);

      // Add AI response to chat
      setChatMessages(prev => ({
        ...prev,
        [activeChat]: [...(prev[activeChat] || []), { type: 'ai', content: response.response }]
      }));

      // Auto-scroll to bottom
      setTimeout(() => {
        if (chatScrollRef.current) {
          chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
        }
      }, 100);

    } catch (error) {
      console.error('Error sending message:', error);

      // Add error message to chat
      setChatMessages(prev => ({
        ...prev,
        [activeChat]: [...(prev[activeChat] || []), {
          type: 'ai',
          content: `⚠️ Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please make sure the backend server is running on http://localhost:8000`
        }]
      }));
    } finally {
      setIsSendingMessage(false);
    }
  };

  // Handle Enter key press
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Handle sidebar resize
  const startResizing = () => {
    setIsResizing(true);
  };

  const stopResizing = () => {
    setIsResizing(false);
  };

  const resize = (e: MouseEvent) => {
    if (isResizing) {
      const newWidth = e.clientX;
      if (newWidth >= 300 && newWidth <= 800) { // Min 300px, Max 800px
        setSidebarWidth(newWidth);
      }
    }
  };

  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', resize);
      window.addEventListener('mouseup', stopResizing);
      return () => {
        window.removeEventListener('mousemove', resize);
        window.removeEventListener('mouseup', stopResizing);
      };
    }
  }, [isResizing]);

  const deleteChat = (chatId: string) => {
    if (chats.length > 1) {
      setChats(chats.filter(c => c.id !== chatId));
      // Remove messages for this chat
      const newChatMessages = { ...chatMessages };
      delete newChatMessages[chatId];
      setChatMessages(newChatMessages);

      if (activeChat === chatId) {
        setActiveChat(chats[0].id);
      }
    }
  };

  const startEditingChat = (chatId: string, currentName: string) => {
    setEditingChatId(chatId);
    setEditingChatName(currentName);
  };

  const saveChat = (chatId: string) => {
    if (editingChatName.trim()) {
      setChats(chats.map(c => c.id === chatId ? { ...c, name: editingChatName.trim() } : c));
    }
    setEditingChatId(null);
    setEditingChatName("");
  };

  const startEditingPage = (pageId: string, currentName: string) => {
    setEditingPageId(pageId);
    setEditingPageName(currentName);
  };

  const savePage = (pageId: string) => {
    if (editingPageName.trim()) {
      setPages(pages.map(p => p.id === pageId ? { ...p, name: editingPageName.trim() } : p));
    }
    setEditingPageId(null);
    setEditingPageName("");
  };

  return (
    <div className={`min-h-screen bg-slate-950 text-white flex flex-col relative h-screen overflow-hidden ${isResizing ? 'select-none' : ''}`}>
      {/* Chat History Sidebar */}
      {showChatSidebar && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity"
            onClick={() => setShowChatSidebar(false)}
          />

          {/* Sidebar */}
          <div className="fixed left-0 top-0 bottom-0 w-80 bg-slate-900/95 backdrop-blur-xl border-r border-slate-800/50 z-50 shadow-2xl animate-in slide-in-from-left duration-300">
            <div className="flex flex-col h-full">
              {/* Sidebar Header */}
              <div className="p-4 border-b border-slate-800/50 flex items-center justify-between">
                <h2 className="font-bold text-lg flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-brand-400" />
                  Chat History
                </h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowChatSidebar(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>

              {/* New Chat Button */}
              <div className="p-4 border-b border-slate-800/50">
                <Button
                  onClick={addNewChat}
                  className="w-full bg-gradient-to-r from-brand-500 to-brand-600 hover:from-brand-600 hover:to-brand-700 shadow-lg shadow-brand-500/20"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Chat
                </Button>
              </div>

              {/* Chat List */}
              <ScrollArea className="flex-1">
                <div className="p-3 space-y-2">
                  {chats.map((chat) => (
                    <div
                      key={chat.id}
                      className={`group relative p-4 rounded-lg cursor-pointer transition-all ${activeChat === chat.id
                        ? 'bg-brand-500/10 border border-brand-500/30'
                        : 'hover:bg-slate-800/50 border border-transparent'
                        }`}
                      onClick={() => {
                        setActiveChat(chat.id);
                        setShowChatSidebar(false);
                      }}
                    >
                      <div className="flex items-start gap-3">
                        <MessageSquare className={`w-4 h-4 flex-shrink-0 mt-0.5 ${activeChat === chat.id ? 'text-brand-400' : 'text-slate-500'}`} />
                        <div className="flex-1 min-w-0">
                          {editingChatId === chat.id ? (
                            <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                              <Input
                                value={editingChatName}
                                onChange={(e) => setEditingChatName(e.target.value)}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') saveChat(chat.id);
                                  if (e.key === 'Escape') setEditingChatId(null);
                                }}
                                className="h-7 text-sm bg-slate-800 border-brand-500/50 text-white"
                                autoFocus
                              />
                              <button
                                onClick={() => saveChat(chat.id)}
                                className="p-1 hover:bg-brand-500/20 rounded"
                              >
                                <Check className="w-4 h-4 text-brand-400" />
                              </button>
                            </div>
                          ) : (
                            <p className={`text-sm font-medium truncate ${activeChat === chat.id ? 'text-brand-200' : 'text-slate-300'}`}>
                              {chat.name}
                            </p>
                          )}
                          <p className="text-xs text-slate-500 truncate mt-1">{chat.preview}</p>
                          <p className="text-xs text-slate-600 mt-2 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {chat.timestamp}
                          </p>
                        </div>
                      </div>
                      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 flex items-center gap-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            startEditingChat(chat.id, chat.name);
                          }}
                          className="p-1.5 hover:bg-brand-500/20 rounded transition-all"
                        >
                          <Edit2 className="w-4 h-4 text-brand-400" />
                        </button>
                        {chats.length > 1 && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteChat(chat.id);
                            }}
                            className="p-1.5 hover:bg-red-500/20 rounded transition-all"
                          >
                            <Trash2 className="w-4 h-4 text-red-400" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </div>
        </>
      )}

      {/* Header */}
      <header className="border-b border-slate-800/50 bg-slate-900/95 backdrop-blur-xl z-30 shadow-2xl">
        <div className="px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div className="w-14 h-14 relative flex items-center justify-center">
              <Image
                src="/harvest-logo.png"
                alt="Project Harvest Logo"
                width={56}
                height={56}
                className="object-contain rounded-lg"
                priority
              />
            </div>
            <div className="border-l border-slate-700 pl-3">
              <h1 className="font-bold text-lg tracking-tight">Project Harvest</h1>
              <p className="text-xs text-slate-400 font-light tracking-wide">Fortnite Activation Intelligence</p>
            </div>
          </Link>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white hover:bg-slate-800">
              <Settings className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white hover:bg-slate-800">
              <User className="w-4 h-4" />
            </Button>
            <div className="h-6 w-px bg-slate-700 mx-1" />
            <Button size="sm" className="bg-brand-600 hover:bg-brand-700 shadow-lg shadow-brand-500/20">
              <Sparkles className="w-4 h-4 mr-2" />
              Share
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - AI Chatbot (Cursor-like) */}
        <div
          className="bg-slate-900/50 border-r border-slate-800/50 flex flex-col backdrop-blur-sm relative"
          style={{ width: `${sidebarWidth}px`, minWidth: '300px', maxWidth: '800px' }}
        >
          {/* Chat Header */}
          <div className="p-4 border-b border-brand-900/30">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowChatSidebar(true)}
                  className="text-slate-400 hover:text-brand-300 hover:bg-brand-900/20 -ml-2"
                >
                  <Menu className="w-5 h-5" />
                </Button>
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-brand-400" />
                  <span className="font-semibold text-sm truncate max-w-[180px]">
                    {chats.find(c => c.id === activeChat)?.name || "New Chat"}
                  </span>
                </div>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={addNewChat}
                className="text-brand-400 hover:text-brand-300 hover:bg-brand-900/20"
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex items-center gap-3 pt-3 border-t border-slate-800/50">
              <div className="w-8 h-8 bg-gradient-to-br from-brand-500 to-brand-600 rounded-lg flex items-center justify-center shadow-lg shadow-brand-500/30">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-sm">AI Analytics Assistant</h3>
                <p className="text-xs text-brand-300/70">Powered by Google Gemini</p>
              </div>
            </div>
          </div>

          {/* Chat Messages */}
          <ScrollArea className="flex-1 p-6" ref={chatScrollRef}>
            <div className="space-y-5">
              {(chatMessages[activeChat] || []).map((message, index) => (
                message.type === 'ai' ? (
                  <div key={index} className="flex gap-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-brand-500 to-brand-600 rounded-lg flex items-center justify-center shadow-lg shadow-brand-500/30 flex-shrink-0">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="bg-slate-800/80 rounded-xl p-4 border border-brand-900/30 shadow-lg shadow-brand-900/20">
                        <div className="prose prose-invert prose-sm max-w-none">
                          <ReactMarkdown
                            components={{
                              p: ({ children }) => <p className="text-sm leading-relaxed text-slate-200 mb-3 last:mb-0">{children}</p>,
                              ul: ({ children }) => <ul className="text-sm text-slate-200 space-y-1 mb-3 list-disc list-inside">{children}</ul>,
                              ol: ({ children }) => <ol className="text-sm text-slate-200 space-y-1 mb-3 list-decimal list-inside">{children}</ol>,
                              li: ({ children }) => <li className="text-sm text-slate-200">{children}</li>,
                              strong: ({ children }) => <strong className="font-semibold text-brand-300">{children}</strong>,
                              em: ({ children }) => <em className="italic text-slate-300">{children}</em>,
                              code: ({ children }) => <code className="bg-slate-900/50 px-1.5 py-0.5 rounded text-xs text-brand-300 font-mono">{children}</code>,
                              h1: ({ children }) => <h1 className="text-lg font-bold text-white mb-2">{children}</h1>,
                              h2: ({ children }) => <h2 className="text-base font-bold text-white mb-2">{children}</h2>,
                              h3: ({ children }) => <h3 className="text-sm font-bold text-white mb-2">{children}</h3>,
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                        {message.content.includes("created") && (
                          <div className="bg-brand-500/10 border border-brand-500/30 rounded-lg p-3 mt-3">
                            <p className="text-xs text-brand-300 font-medium">✓ Visualization added to canvas</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div key={index} className="flex gap-3 justify-end">
                    <div className="flex-1">
                      <div className="bg-gradient-to-r from-brand-600 to-brand-500 rounded-xl p-4 ml-12 shadow-xl shadow-brand-600/30">
                        <p className="text-sm leading-relaxed text-white whitespace-pre-wrap">{message.content}</p>
                      </div>
                    </div>
                  </div>
                )
              ))}
            </div>
          </ScrollArea>

          {/* Example Prompts - Only show for new chats */}
          {(chatMessages[activeChat] || []).length <= 1 && (
            <div className="p-5 border-t border-brand-900/30">
              <p className="text-xs text-brand-300/60 mb-2.5 font-medium uppercase tracking-wide">Try these prompts</p>
              <div className="space-y-2">
                <button
                  onClick={() => setChatInput("Predict the future CCU for map 8530-0110-2817")}
                  className="w-full text-left p-2.5 bg-brand-950/30 hover:bg-brand-900/20 rounded-lg border border-brand-800/30 hover:border-brand-700/50 transition-all group"
                >
                  <p className="text-[13px] text-slate-300 group-hover:text-brand-200">Predict the future CCU for map 8530-0110-2817</p>
                </button>
                <button
                  onClick={() => setChatInput("Compare maps 8530-0110-2817 and 8942-4322-3496")}
                  className="w-full text-left p-2.5 bg-brand-950/30 hover:bg-brand-900/20 rounded-lg border border-brand-800/30 hover:border-brand-700/50 transition-all group"
                >
                  <p className="text-[13px] text-slate-300 group-hover:text-brand-200">Compare maps 8530-0110-2817 and 8942-4322-3496</p>
                </button>
                <button
                  onClick={() => setChatInput("Detect anomalies for map 8530-0110-2817")}
                  className="w-full text-left p-2.5 bg-brand-950/30 hover:bg-brand-900/20 rounded-lg border border-brand-800/30 hover:border-brand-700/50 transition-all group"
                >
                  <p className="text-[13px] text-slate-300 group-hover:text-brand-200">Detect anomalies for map 8530-0110-2817</p>
                </button>
              </div>
            </div>
          )}

          {/* Chat Input */}
          <div className="p-6 border-t border-brand-900/30 bg-slate-900/80">
            <div className="flex gap-3">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isSendingMessage}
                placeholder="Ask about a map, predict CCU, detect anomalies, or compare maps..."
                className="flex-1 bg-slate-800 border border-brand-800/40 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30 transition-all placeholder:text-slate-500 disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <Button
                size="sm"
                onClick={handleSendMessage}
                disabled={isSendingMessage || !chatInput.trim()}
                className="bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-700 hover:to-brand-600 shadow-lg shadow-brand-600/30 px-4 disabled:opacity-50"
              >
                {isSendingMessage ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4" />
                )}
              </Button>
            </div>
            <p className="text-xs text-brand-300/50 mt-2">Press Enter to send • Powered by Google Gemini</p>
          </div>

          {/* Resize Handle */}
          <div
            className={`absolute right-0 top-0 bottom-0 w-1.5 cursor-col-resize transition-all ${isResizing ? 'bg-brand-500' : 'bg-transparent hover:bg-brand-500/30'
              }`}
            onMouseDown={startResizing}
            style={{ zIndex: 50 }}
          >
            {/* Invisible wider hit area for easier grabbing */}
            <div className="absolute -left-2 -right-2 top-0 bottom-0" />
          </div>
        </div>

        {/* Main Workspace Canvas */}
        <div className="flex-1 flex flex-col min-h-0">
          {/* Page Tabs */}
          <div className="border-b border-brand-900/30 bg-slate-900/30 px-4 flex items-center justify-between">
            <div className="flex items-center gap-2 overflow-x-auto">
              {pages.map((page) => (
                <div
                  key={page.id}
                  className={`group flex items-center gap-2 px-4 py-3 text-sm font-medium cursor-pointer transition-all border-b-2 ${activePage === page.id
                    ? "border-brand-500 text-white bg-brand-950/20"
                    : "border-transparent text-slate-400 hover:text-brand-300 hover:bg-brand-950/10"
                    }`}
                  onClick={() => setActivePage(page.id)}
                >
                  <LayoutGrid className={`w-4 h-4 ${activePage === page.id ? "text-brand-400" : ""}`} />
                  {editingPageId === page.id ? (
                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      <Input
                        value={editingPageName}
                        onChange={(e) => setEditingPageName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') savePage(page.id);
                          if (e.key === 'Escape') setEditingPageId(null);
                        }}
                        className="h-7 w-32 text-sm bg-slate-800 border-brand-500/50 text-white"
                        autoFocus
                      />
                      <button
                        onClick={() => savePage(page.id)}
                        className="p-1 hover:bg-brand-500/20 rounded"
                      >
                        <Check className="w-3 h-3 text-brand-400" />
                      </button>
                    </div>
                  ) : (
                    <span>{page.name}</span>
                  )}
                  <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        startEditingPage(page.id, page.name);
                      }}
                      className="hover:text-brand-400 transition-all"
                    >
                      <Edit2 className="w-3 h-3" />
                    </button>
                    {pages.length > 1 && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removePage(page.id);
                        }}
                        className="hover:text-red-400 transition-opacity"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
              <Button
                size="sm"
                variant="ghost"
                onClick={addNewPage}
                className="flex-shrink-0 text-slate-400 hover:text-brand-300 hover:bg-brand-950/10"
              >
                <Plus className="w-4 h-4 mr-1" />
                New Page
              </Button>
            </div>
          </div>

          {/* Workspace Canvas */}
          <div className="flex-1 overflow-hidden">
            <WorkspaceCanvas key={activePage} pageId={activePage} />
          </div>
        </div>
      </div>
    </div>
  );
}