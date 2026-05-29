"use client";

import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { DownloadCard } from "@/components/DownloadCard";
import { GenerateButton } from "@/components/GenerateButton";
import {
  ProcessingSteps,
  type ProcessingStage,
} from "@/components/ProcessingSteps";
import { SettingsPanel } from "@/components/SettingsPanel";
import { UploadZone, type AccentName } from "@/components/UploadZone";
import { generateReport } from "@/lib/api";
import { fetchGenerationConfig, type ModelOption } from "@/lib/config";

const SYSTEM_PROMPT_STORAGE_KEY = "minutely.systemPrompt";

type Step = "idle" | "uploading" | "processing" | "done" | "error";

interface SlotConfig {
  key: "my_context" | "client_context" | "transcript";
  label: string;
  description: string;
  acceptExtensions: string[];
  accent: AccentName;
}

const SLOTS: SlotConfig[] = [
  {
    key: "my_context",
    label: "My Context",
    description: "Background about you, your goals, and what to listen for.",
    acceptExtensions: [".md"],
    accent: "indigo",
  },
  {
    key: "client_context",
    label: "Client Context",
    description: "Background on the client, their team, and prior history.",
    acceptExtensions: [".md"],
    accent: "teal",
  },
  {
    key: "transcript",
    label: "Meeting Transcript",
    description: "Raw transcript export from your call.",
    acceptExtensions: [".csv", ".txt", ".pdf", ".docx", ".md"],
    accent: "amber",
  },
];

interface FileSlots {
  my_context: File | null;
  client_context: File | null;
  transcript: File | null;
}

const EMPTY_SLOTS: FileSlots = {
  my_context: null,
  client_context: null,
  transcript: null,
};

export function ThreeDocUploader(): JSX.Element {
  const [slots, setSlots] = useState<FileSlots>(EMPTY_SLOTS);
  const [step, setStep] = useState<Step>("idle");
  const [stage, setStage] = useState<ProcessingStage>("parsing");
  const [result, setResult] = useState<{ blob: Blob; filename: string } | null>(
    null,
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [models, setModels] = useState<ModelOption[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [systemPrompt, setSystemPrompt] = useState<string>("");
  const [defaultSystemPrompt, setDefaultSystemPrompt] = useState<string>("");
  const [settingsError, setSettingsError] = useState<string | null>(null);

  const stageTimers = useRef<number[]>([]);

  const clearStageTimers = useCallback(() => {
    for (const id of stageTimers.current) {
      window.clearTimeout(id);
    }
    stageTimers.current = [];
  }, []);

  useEffect(() => {
    return () => {
      clearStageTimers();
    };
  }, [clearStageTimers]);

  // Load model list + default system prompt once on mount, then apply any
  // locally-persisted custom prompt. localStorage is read ONLY here (never
  // during render) to stay SSR-hydration safe.
  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const config = await fetchGenerationConfig();
        if (cancelled) return;

        setModels(config.models);
        setSelectedModel(config.default_model);
        setDefaultSystemPrompt(config.default_system_prompt);

        let stored: string | null = null;
        try {
          stored = window.localStorage.getItem(SYSTEM_PROMPT_STORAGE_KEY);
        } catch {
          stored = null;
        }
        if (stored !== null && stored.trim().length > 0) {
          setSystemPrompt(stored);
        } else {
          setSystemPrompt(config.default_system_prompt);
        }
      } catch (err: unknown) {
        if (cancelled) return;
        const message =
          err instanceof Error
            ? err.message
            : "Could not load generation settings.";
        setSettingsError(message);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const allFilled = useMemo<boolean>(
    () =>
      slots.my_context !== null &&
      slots.client_context !== null &&
      slots.transcript !== null,
    [slots],
  );

  const isBusy = step === "uploading" || step === "processing";

  const isCustomized = useMemo<boolean>(
    () =>
      systemPrompt.trim() !== defaultSystemPrompt.trim() &&
      systemPrompt.trim().length > 0,
    [systemPrompt, defaultSystemPrompt],
  );

  const onResetSystemPrompt = useCallback(() => {
    setSystemPrompt(defaultSystemPrompt);
    try {
      window.localStorage.removeItem(SYSTEM_PROMPT_STORAGE_KEY);
    } catch {
      /* storage unavailable — non-fatal */
    }
  }, [defaultSystemPrompt]);

  const onSlotChange = useCallback(
    (key: SlotConfig["key"]) => (file: File | null) => {
      setSlots((prev) => ({ ...prev, [key]: file }));
    },
    [],
  );

  const reset = useCallback(() => {
    clearStageTimers();
    setSlots(EMPTY_SLOTS);
    setStep("idle");
    setStage("parsing");
    setResult(null);
    setErrorMessage(null);
  }, [clearStageTimers]);

  const onGenerate = useCallback(async () => {
    if (
      !slots.my_context ||
      !slots.client_context ||
      !slots.transcript
    ) {
      return;
    }

    setErrorMessage(null);
    setResult(null);
    setStep("uploading");
    setStage("parsing");

    // Visually advance through the steps while the single backend call runs.
    clearStageTimers();
    stageTimers.current.push(
      window.setTimeout(() => {
        setStep("processing");
        setStage("claude");
      }, 1200),
    );
    stageTimers.current.push(
      window.setTimeout(() => {
        setStage("pdf");
      }, 12000),
    );

    // Persist the prompt: keep custom prompts for next visit, drop defaults.
    try {
      if (isCustomized) {
        window.localStorage.setItem(SYSTEM_PROMPT_STORAGE_KEY, systemPrompt);
      } else {
        window.localStorage.removeItem(SYSTEM_PROMPT_STORAGE_KEY);
      }
    } catch {
      /* storage unavailable — non-fatal */
    }

    try {
      const report = await generateReport({
        my_context: slots.my_context,
        client_context: slots.client_context,
        transcript: slots.transcript,
        model: selectedModel,
        systemPrompt,
      });
      clearStageTimers();
      setResult(report);
      setStep("done");
    } catch (err: unknown) {
      clearStageTimers();
      const message =
        err instanceof Error ? err.message : "Something went wrong.";
      setErrorMessage(message);
      setStep("error");
    }
  }, [clearStageTimers, slots, selectedModel, systemPrompt, isCustomized]);

  return (
    <section className="flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <SettingsPanel
          models={models}
          selectedModel={selectedModel}
          onModelChange={setSelectedModel}
          systemPrompt={systemPrompt}
          onSystemPromptChange={setSystemPrompt}
          onResetSystemPrompt={onResetSystemPrompt}
          isCustomized={isCustomized}
          disabled={isBusy}
        />
        {settingsError ? (
          <p className="flex items-start gap-2 px-1 text-xs text-amber-300/80">
            <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span>
              {settingsError} You can still generate a report — the server will
              apply its defaults.
            </span>
          </p>
        ) : null}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3 md:gap-5">
        {SLOTS.map((slot) => (
          <UploadZone
            key={slot.key}
            label={slot.label}
            description={slot.description}
            acceptExtensions={slot.acceptExtensions}
            file={slots[slot.key]}
            onFile={onSlotChange(slot.key)}
            accent={slot.accent}
            disabled={isBusy}
          />
        ))}
      </div>

      <div className="flex flex-col gap-4">
        <GenerateButton
          disabled={!allFilled || step === "done"}
          loading={isBusy}
          onClick={onGenerate}
        />

        <AnimatePresence>
          {errorMessage ? (
            <motion.div
              key="error"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              className="flex items-start gap-3 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-200"
              role="alert"
            >
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <div className="flex flex-col gap-2">
                <p className="font-medium">Report generation failed</p>
                <p className="text-xs leading-relaxed text-rose-200/80">
                  {errorMessage}
                </p>
                <button
                  type="button"
                  onClick={() => setErrorMessage(null)}
                  className="self-start text-xs font-medium underline-offset-2 hover:underline"
                >
                  Dismiss
                </button>
              </div>
            </motion.div>
          ) : null}
        </AnimatePresence>

        <ProcessingSteps visible={isBusy} activeStage={stage} />

        <AnimatePresence>
          {step === "done" && result ? (
            <DownloadCard
              blob={result.blob}
              filename={result.filename}
              onReset={reset}
            />
          ) : null}
        </AnimatePresence>
      </div>
    </section>
  );
}
