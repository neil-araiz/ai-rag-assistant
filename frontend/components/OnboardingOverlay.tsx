"use client";

import { useState, useEffect } from "react";
import { X } from "lucide-react";

interface OnboardingOverlayProps {
  step: number;
  onNext: () => void;
  onSkip: () => void;
  onFinish: () => void;
}

export default function OnboardingOverlay({
  step,
  onNext,
  onSkip,
  onFinish,
}: OnboardingOverlayProps) {
  const [coords, setCoords] = useState({
    top: 0,
    left: 0,
    width: 0,
    height: 0,
  });

  const steps = [
    {
      id: "step-dropzone",
      title: "Upload Area",
      text: "Drag and drop your PDF documents here to start.",
    },
    {
      id: "step-try-sample",
      title: "Sample Document",
      text: "Don't have a PDF? Try it out with our sample file!",
    },
    {
      id: "step-view-sample",
      title: "Preview",
      text: "You can view the sample file natively in your browser first.",
    },
    {
      id: "step-upload-btn",
      title: "Process Document",
      text: "After selecting a file, click here to process it for RAG.",
    },
    {
      id: "step-chat",
      title: "Chat Interface",
      text: "Ask questions about your uploaded documents here.",
    },
    {
      id: "step-help",
      title: "How it works",
      text: "Click here anytime to learn more about the RAG system.",
    },
  ];

  useEffect(() => {
    const updateCoords = () => {
      const el = document.getElementById(steps[step].id);
      if (el) {
        const rect = el.getBoundingClientRect();
        setCoords({
          top: rect.top,
          left: rect.left,
          width: rect.width,
          height: rect.height,
        });
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    };

    updateCoords();
    window.addEventListener("resize", updateCoords);
    return () => window.removeEventListener("resize", updateCoords);
  }, [step]);

  const currentStep = steps[step];

  return (
    <div className="fixed inset-0 z-50 pointer-events-none ring-slate-900/50 dark:ring-slate-900/80">
      <svg
        className="absolute inset-0 w-full h-full pointer-events-auto"
        onClick={onSkip}
      >
        <defs>
          <mask id="spotlight-mask">
            <rect x="0" y="0" width="100%" height="100%" fill="white" />
            <rect
              x={coords.left - 8}
              y={coords.top - 8}
              width={coords.width + 16}
              height={coords.height + 16}
              rx="12"
              fill="black"
              className="transition-all duration-300 ease-in-out"
            />
          </mask>
        </defs>
        <rect
          x="0"
          y="0"
          width="100%"
          height="100%"
          fill="rgba(0,0,0,0.6)"
          mask="url(#spotlight-mask)"
        />
      </svg>

      <div
        className="absolute z-[60] pointer-events-auto transition-all duration-300 ease-in-out bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 max-w-sm w-[calc(100vw-48px)]"
        style={{
          top:
            coords.top + coords.height + 24 > window.innerHeight - 200
              ? coords.top - 200
              : coords.top + coords.height + 24,
          left: Math.min(
            Math.max(24, coords.left + coords.width / 2 - 175),
            window.innerWidth - 375,
          ),
        }}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold text-orange-600 dark:text-orange-400 tracking-wider">
              Step {step + 1} of {steps.length}
            </span>
            <button
              onClick={onSkip}
              className="text-slate-400 hover:text-slate-600 p-1"
            >
              <X size={16} />
            </button>
          </div>
          <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100">
            {currentStep.title}
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
            {currentStep.text}
          </p>
          <div className="flex items-center justify-between pt-2">
            <button
              onClick={onSkip}
              className="text-xs font-bold text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
            >
              Skip Tour
            </button>
            <button
              onClick={step === steps.length - 1 ? onFinish : onNext}
              className="px-6 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-bold text-sm transition-all shadow-lg shadow-orange-600/20"
            >
              {step === steps.length - 1 ? "Get Started" : "Next Step"}
            </button>
          </div>
        </div>
      </div>

      <div
        className="absolute border-2 border-orange-500 rounded-xl transition-all duration-300 ease-in-out pointer-events-none shadow-[0_0_20px_rgba(249,115,22,0.4)]"
        style={{
          top: coords.top - 8,
          left: coords.left - 8,
          width: coords.width + 16,
          height: coords.height + 16,
        }}
      />
    </div>
  );
}
