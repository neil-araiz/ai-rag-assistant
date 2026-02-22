"use client";

import { useState, useRef, useEffect } from "react";
import {
  uploadDocument,
  chatWithDocument,
  deleteDocument,
} from "@/lib/document";
import {
  Send,
  FileText,
  HelpCircle,
  X,
  Bot,
  User,
  FileUp,
  MonitorCog,
  Sun,
  Moon,
} from "lucide-react";
import clsx from "clsx";
import toast from "react-hot-toast";
import InfoModal from "@/components/InfoModal";
import OnboardingOverlay from "@/components/OnboardingOverlay";

export default function Home() {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<
    { role: string; content: string; citations?: any[] }[]
  >([]);
  const [files, setFiles] = useState<File[]>([]);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [documentId, setDocumentId] = useState<number | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [isInfoOpen, setIsInfoOpen] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [onboardingStep, setOnboardingStep] = useState(0);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setIsDarkMode(false);
    document.documentElement.classList.remove("dark");

    const hasSeenOnboarding = localStorage.getItem("hasSeenOnboarding-v1");
    if (!hasSeenOnboarding) {
      setShowOnboarding(true);
    }
  }, []);

  const toggleDarkMode = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    if (newMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (chatHistory.length > 0) {
      scrollToBottom();
    }
  }, [chatHistory]);

  const handleSendMessage = async () => {
    if (!message.trim() || !documentId) return;

    const currentMsg = message;
    const userMsg = { role: "user", content: currentMsg };
    setChatHistory((prev) => [...prev, userMsg]);
    setMessage("");
    setIsLoading(true);

    try {
      const response = await chatWithDocument(currentMsg, documentId);
      const botMsg = {
        role: "assistant",
        content: response.answer,
        citations: response.citations,
      };
      setChatHistory((prev) => [...prev, botMsg]);
    } catch (error) {
      toast.error("Failed to connect to AI server.");
    } finally {
      setIsLoading(false);
    }
  };

  const onFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (files.length > 0) {
      toast.error(
        "Upload one file only. Please remove the current file first.",
      );
      return;
    }
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setPendingFile(selectedFile);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    if (files.length > 0) {
      toast.error(
        "Upload one file only. Please remove the current file first.",
      );
      return;
    }

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && droppedFile.type === "application/pdf") {
      setPendingFile(droppedFile);
    } else if (droppedFile) {
      toast.error("Please upload a PDF file.");
    }
  };

  const handleFileUpload = async () => {
    if (!pendingFile) return;

    const selectedFile = pendingFile;
    setPendingFile(null);

    const uploadPromise = async () => {
      const response = await uploadDocument(selectedFile);
      setDocumentId(response.document_id);

      setFiles((prev) => [...prev, selectedFile]);

      const greetingMsg = {
        role: "assistant",
        content: `Hello! Your document is ready. You can now ask me questions about the contents of "${selectedFile.name}"`,
      };
      setChatHistory((prev) => [...prev, greetingMsg]);

      return response;
    };

    toast.promise(uploadPromise(), {
      loading: `Processing "${selectedFile.name}"...`,
      success: "Document ready!",
      error: "Failed to process the document.",
    });
  };

  const removeFile = async (index: number) => {
    if (documentId) {
      const deletePromise = deleteDocument(documentId);

      toast.promise(deletePromise, {
        loading: "Removing document...",
        success: "Document removed successfully.",
        error: "Failed to remove document.",
      });

      try {
        await deletePromise;
        setFiles((prev) => prev.filter((_, i) => i !== index));
        setDocumentId(null);
        setChatHistory([]);
      } catch (error) {
        console.error("Deletion error:", error);
      }
    } else {
      setFiles((prev) => prev.filter((_, i) => i !== index));
      setDocumentId(null);
      setChatHistory([]);
    }
  };

  const handleLoadSample = async () => {
    if (files.length > 0) {
      toast.error(
        "Upload one file only. Please remove the current file first.",
      );
      return;
    }

    const sampleProcess = async () => {
      const response = await fetch("/sample.pdf");
      if (!response.ok) throw new Error("Sample file not found");
      const blob = await response.blob();

      const sampleFile = new File([blob], "sample.pdf", {
        type: "application/pdf",
      });

      const uploadResponse = await uploadDocument(sampleFile);
      setDocumentId(uploadResponse.document_id);
      setFiles([sampleFile]);

      const greetingMsg = {
        role: "assistant",
        content: `Hello! I've loaded the sample document for you. You can now ask me questions about "sample.pdf"`,
      };
      setChatHistory((prev) => [...prev, greetingMsg]);

      return uploadResponse;
    };

    toast.promise(sampleProcess(), {
      loading: "Loading sample document...",
      success: "Sample document ready!",
      error: "Failed to load sample document. Ensure /public/sample.pdf exists.",
    });
  };

  return (
    <div className="min-h-screen flex flex-col font-sans transition-colors duration-300">
      <header className="px-6 py-4 flex items-center justify-between bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 transition-colors">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-orange-500 rounded-lg flex items-center justify-center text-white shadow-lg shadow-orange-500/20">
            <MonitorCog size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              AI RAG Assistant
            </h1>
          </div>
        </div>
        <div className="flex items-center gap-4 text-slate-500">
          <button
            onClick={toggleDarkMode}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-all text-slate-500 dark:text-slate-400"
            title={isDarkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          <button 
            id="step-help"
            onClick={() => setIsInfoOpen(true)}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors text-slate-500 dark:text-slate-400"
            title="System Information"
          >
            <HelpCircle size={20} />
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-4 md:px-0 relative bg-background pb-32 transition-colors">
        <div className="hidden lg:block absolute right-8 top-8 w-48 bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm z-10 animate-fade-in transition-colors">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 bg-green-500 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              System Ready
            </span>
          </div>
          <div className="space-y-2">
            <div>
              <p className="text-[10px] text-slate-400 font-medium">
                AI Model:
              </p>
              <p className="text-xs font-bold text-orange-600 dark:text-orange-400">
                Gemini 2.5 Flash (RAG)
              </p>
            </div>
            <div>
              <p className="text-[10px] text-slate-400 font-medium">
                Document Library:
              </p>
              <p className="text-xs font-bold">
                {documentId ? "1 document loaded" : "No documents loaded"}
              </p>
            </div>
          </div>
        </div>

        <div className="max-w-4xl mx-auto py-12 space-y-12">
          <section className="space-y-6">
            <div
              id="step-dropzone"
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={clsx(
                "dropzone-dashed rounded-2xl p-12 flex flex-col items-center justify-center text-center space-y-6 transition-all duration-200",
                isDragging
                  ? "bg-orange-50/50 dark:bg-orange-950/20 border-orange-400 scale-[1.01] shadow-xl"
                  : "border-slate-200 dark:border-slate-800",
              )}
            >
              <div
                className={clsx(
                  "w-12 h-12 rounded-full flex items-center justify-center transition-colors",
                  isDragging
                    ? "bg-orange-600 text-white"
                    : "bg-orange-50 dark:bg-orange-950/30 text-orange-600",
                )}
              >
                <FileUp size={24} />
              </div>
              <div className="space-y-1">
                <h2 className="text-lg font-bold text-foreground">
                  Document Library
                </h2>
                <p className="text-sm text-slate-500">
                  Drag and drop your PDF here to start chatting.
                </p>
                {pendingFile && (
                  <div className="flex items-center gap-2 mt-2 animate-fade-in justify-center">
                    <p className="text-xs font-semibold text-orange-600 dark:text-orange-400">
                      File selected: {pendingFile.name}
                    </p>
                    <button
                      onClick={() => setPendingFile(null)}
                      className="text-orange-600 dark:text-orange-400 hover:text-orange-800 dark:hover:text-orange-200"
                      title="Remove selection"
                    >
                      <X size={14} />
                    </button>
                  </div>
                )}
                {!pendingFile && files.length === 0 && (
                  <div className="flex flex-col items-center gap-2 mt-4">
                    <button
                      id="step-try-sample"
                      onClick={handleLoadSample}
                      className="text-xs font-bold cursor-pointer text-orange-600 dark:text-orange-400 hover:underline transition-all"
                    >
                      Try with a sample document
                    </button>
                    <a
                      id="step-view-sample"
                      href="/sample.pdf"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 flex items-center gap-1"
                    >
                      <FileText size={11} />
                      View Sample PDF
                    </a>
                  </div>
                )}
              </div>
              <div className="flex gap-3">
                <button
                  id="step-upload-btn"
                  onClick={handleFileUpload}
                  disabled={!pendingFile}
                  className="px-6 py-2.5 bg-orange-600 hover:bg-orange-700 disabled:bg-slate-300 dark:disabled:bg-slate-800 text-white rounded-lg font-bold text-sm transition-all shadow-md shadow-orange-600/20 disabled:shadow-none"
                >
                  Upload Document
                </button>
                <label className="cursor-pointer px-6 py-2.5 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 rounded-lg font-bold text-sm transition-all text-slate-700 dark:text-slate-300">
                  <input
                    type="file"
                    className="hidden"
                    ref={fileInputRef}
                    onChange={onFileSelect}
                    accept=".pdf"
                  />
                  Browse Files
                </label>
              </div>
            </div>

            {files.length > 0 && (
              <div className="flex flex-wrap gap-2 justify-center">
                {files.map((f, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 px-3 py-1.5 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-full text-xs font-medium text-orange-700 dark:text-orange-400 animate-fade-in"
                  >
                    <FileText size={14} />
                    {f.name}
                    <button
                      onClick={() => removeFile(i)}
                      className="hover:text-orange-900 dark:hover:text-orange-200 cursor-pointer"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>

          <div className="space-y-8">
            {chatHistory.map((msg, idx) => (
              <div
                key={idx}
                className={clsx(
                  "flex gap-4 mx-auto animate-fade-in",
                  msg.role === "user" ? "flex-row-reverse" : "flex-row",
                )}
              >
                <div
                  className={clsx(
                    "w-10 h-10 rounded-full flex items-center justify-center text-white flex-shrink-0 shadow-md",
                    msg.role === "user" ? "bg-slate-400" : "bg-orange-500",
                  )}
                >
                  {msg.role === "user" ? <User size={20} /> : <Bot size={20} />}
                </div>
                <div
                  className={clsx(
                    "flex-1 space-y-2",
                    msg.role === "user" ? "text-right" : "text-left",
                  )}
                >
                  <div
                    className={clsx(
                      "p-4 rounded-2xl shadow-sm inline-block text-left max-w-[90%]",
                      msg.role === "user"
                        ? "bg-orange-600 text-white rounded-tr-none"
                        : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 rounded-tl-none",
                    )}
                  >
                    <p className="text-sm leading-relaxed">{msg.content}</p>

                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-4 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800 flex items-start gap-3">
                        <FileText
                          size={16}
                          className="text-orange-500 mt-0.5"
                        />
                        <div>
                          <p className="text-[10px] font-bold text-slate-500 uppercase">
                            Source Found
                          </p>
                          <p className="text-[11px] font-medium text-slate-700 dark:text-slate-300 italic line-clamp-2">
                            "{msg.citations[0].snippet}"
                          </p>
                          <p className="text-[9px] text-slate-400 mt-1">
                            Page {msg.citations[0].page_number}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">
                    {msg.role === "user" ? "You" : "AI Assistant"} • Just Now
                  </p>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-4 mx-auto animate-pulse flex-row">
                <div className="w-10 h-10 bg-orange-500 rounded-full flex items-center justify-center text-white flex-shrink-0">
                  <Bot size={20} />
                </div>
                <div className="flex-1 space-y-2">
                  <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4 rounded-2xl rounded-tl-none h-12 w-24 flex items-center justify-center gap-1.5">
                    <div className="w-1.5 h-1.5 bg-slate-400 rounded-full typing-dot"></div>
                    <div className="w-1.5 h-1.5 bg-slate-400 rounded-full typing-dot"></div>
                    <div className="w-1.5 h-1.5 bg-slate-400 rounded-full typing-dot"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
        </div>
      </main>

      <div className="fixed bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-background via-background/80 to-transparent transition-colors">
        <div className="max-w-4xl mx-auto">
          <div className="relative group" id="step-chat">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              placeholder="Ask a question about your documents..."
              className="w-full pl-6 pr-16 py-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl focus:outline-none focus:ring-2 focus:ring-orange-500/30 transition-all text-sm"
              disabled={!documentId}
            />
            <button
              onClick={handleSendMessage}
              disabled={isLoading || !message.trim() || !documentId}
              className="absolute right-2.5 top-2.5 p-2 px-4 bg-orange-600 text-white rounded-xl hover:bg-orange-700 disabled:opacity-50 disabled:bg-slate-300 dark:disabled:bg-slate-800 transition-all shadow-lg shadow-orange-600/20 flex items-center gap-2"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>

      <InfoModal isOpen={isInfoOpen} onClose={() => setIsInfoOpen(false)} />

      {showOnboarding && (
        <OnboardingOverlay 
          step={onboardingStep} 
          onNext={() => setOnboardingStep(prev => prev + 1)}
          onSkip={() => {
            setShowOnboarding(false);
            localStorage.setItem("hasSeenOnboarding-v1", "true");
          }}
          onFinish={() => {
            setShowOnboarding(false);
            localStorage.setItem("hasSeenOnboarding-v1", "true");
          }}
        />
      )}
    </div>
  );
}
