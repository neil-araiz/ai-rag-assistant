"use client";

import Modal from "./Modal";
import {  
  Cpu, 
  ShieldCheck, 
  Zap, 
  Database,
  Search,
} from "lucide-react";

interface InfoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function InfoModal({ isOpen, onClose }: InfoModalProps) {
  const steps = [
    {
      icon: <Database className="text-orange-500" size={24} />,
      title: "Document Loading",
      description: "When you upload a PDF, we don't just 'read' it. We extract every sentence and clean it up for the AI to process without distractions."
    },
    {
      icon: <Cpu className="text-orange-500" size={24} />,
      title: "Knowledge Mapping",
      description: "Our system creates a 'semantic map' (embeddings) of your document. This allows the AI to understand the meaning of the content, not just match keywords."
    },
    {
      icon: <Search className="text-orange-500" size={24} />,
      title: "Smart Retrieval",
      description: "When you ask a question, our RAG engine instantly scans your entire library to find the exact paragraphs relevant to your specific query."
    },
    {
      icon: <ShieldCheck className="text-orange-500" size={24} />,
      title: "Grounded Answers",
      description: "The AI is strictly 'grounded' in your data. It uses the retrieved chunks to formulate an answer, ensuring it stay truthful to your document's content."
    }
  ];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="How the Assistant Works">
      <div className="space-y-8">
        <div>
          <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed mb-6">
            This assistant uses <strong>RAG (Retrieval-Augmented Generation)</strong> technology. 
            Instead of relying on general knowledge, it builds its own internal brain from the specific 
            documents you provide. Here is the life cycle of your information:
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {steps.map((step, idx) => (
            <div key={idx} className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 transition-all hover:shadow-md">
              <div className="w-10 h-10 mb-4 bg-white dark:bg-slate-900 rounded-xl flex items-center justify-center shadow-sm">
                {step.icon}
              </div>
              <h4 className="font-bold text-slate-900 dark:text-white mb-2 text-sm uppercase tracking-tight">
                {step.title}
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>

        <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-xl border border-orange-100 dark:border-orange-800/50 flex items-start gap-4">
          <Zap className="text-orange-600 shrink-0" size={20} />
          <p className="text-xs text-orange-800 dark:text-orange-300 leading-relaxed font-medium">
            <strong>Pro Tip:</strong> Large or complex PDFs are indexed in chunks. If you don't get 
            a perfect answer, try asking specifically about a section or page number!
          </p>
        </div>
      </div>
    </Modal>
  );
}
