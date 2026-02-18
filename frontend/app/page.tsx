"use client";

import { useState } from "react";
import api from "@/lib/api";
import { Upload, Send, FileText } from "lucide-react";
import clsx from "clsx";

export default function Home() {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<{ role: string; content: string }[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    const userMsg = { role: "user", content: message };
    setChatHistory((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await api.post("/chat", { message });
      const botMsg = { role: "assistant", content: response.data.response };
      setChatHistory((prev) => [...prev, botMsg]);
    } catch (error) {
      console.error("Chat error:", error);
      setChatHistory((prev) => [
        ...prev,
        { role: "assistant", content: "Error connecting to backend." },
      ]);
    } finally {
      setIsLoading(false);
      setMessage("");
    }
  };

  const handleFileUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setUploadStatus("Uploading...");

    try {
      const response = await api.post("/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setUploadStatus(`Uploaded: ${response.data.filename}`);
    } catch (error) {
      console.error("Upload error:", error);
      setUploadStatus("Upload failed.");
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-8 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <div className="w-full max-w-2xl space-y-8">
        <h1 className="text-3xl font-bold text-center">AI RAG Assistant</h1>

        {/* Upload Section */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Upload size={20} /> Upload Document
          </h2>
          <div className="flex gap-4 items-center">
            <input
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-full file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100 dark:file:bg-gray-700 dark:file:text-gray-300"
            />
            <button
              onClick={handleFileUpload}
              disabled={!file}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Upload
            </button>
          </div>
          {uploadStatus && (
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{uploadStatus}</p>
          )}
        </div>

        {/* Chat Section */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md h-[500px] flex flex-col">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <FileText size={20} /> Chat
          </h2>
          
          <div className="flex-1 overflow-y-auto mb-4 space-y-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
            {chatHistory.length === 0 ? (
              <p className="text-center text-gray-500 italic">Start a conversation...</p>
            ) : (
              chatHistory.map((msg, idx) => (
                <div
                  key={idx}
                  className={clsx(
                    "p-3 rounded-lg max-w-[80%]",
                    msg.role === "user"
                      ? "ml-auto bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100"
                      : "bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  )}
                >
                  <p className="text-sm font-semibold mb-1 capitalize">{msg.role}</p>
                  <p>{msg.content}</p>
                </div>
              ))
            )}
            {isLoading && (
               <div className="bg-gray-100 dark:bg-gray-700 p-3 rounded-lg max-w-[80%] animate-pulse">
                 Thinking...
               </div>
            )}
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              placeholder="Ask something about your documents..."
              className="flex-1 p-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-transparent focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSendMessage}
              disabled={isLoading || !message.trim()}
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
