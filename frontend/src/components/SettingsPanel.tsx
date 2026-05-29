"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, RotateCcw, Sliders } from "lucide-react";
import { useCallback, useId, useState } from "react";

import { cn } from "@/lib/cn";
import type { ModelOption } from "@/lib/config";

interface SettingsPanelProps {
  models: ModelOption[];
  selectedModel: string;
  onModelChange: (id: string) => void;
  systemPrompt: string;
  onSystemPromptChange: (text: string) => void;
  onResetSystemPrompt: () => void;
  isCustomized: boolean;
  disabled?: boolean;
}

export function SettingsPanel({
  models,
  selectedModel,
  onModelChange,
  systemPrompt,
  onSystemPromptChange,
  onResetSystemPrompt,
  isCustomized,
  disabled = false,
}: SettingsPanelProps): JSX.Element {
  const [open, setOpen] = useState<boolean>(false);
  const modelId = useId();
  const promptId = useId();
  const bodyId = useId();

  const toggle = useCallback(() => {
    setOpen((prev) => !prev);
  }, []);

  const selected = models.find((m) => m.id === selectedModel);

  return (
    <div className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/40">
      <button
        type="button"
        onClick={toggle}
        aria-expanded={open}
        aria-controls={bodyId}
        className="flex w-full items-center justify-between gap-3 px-5 py-4 text-left transition-colors hover:bg-zinc-900/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950"
      >
        <span className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-300">
            <Sliders className="h-4 w-4" />
          </span>
          <span className="flex flex-col gap-0.5">
            <span className="text-sm font-medium text-zinc-200">
              Model &amp; system prompt
            </span>
            <span className="text-xs text-zinc-500">
              {selected ? selected.label : "Configure how Claude writes the report"}
              {isCustomized ? " · custom prompt" : ""}
            </span>
          </span>
        </span>
        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 text-zinc-500 transition-transform duration-300",
            open && "rotate-180",
          )}
        />
      </button>

      <AnimatePresence initial={false}>
        {open ? (
          <motion.div
            key="settings-body"
            id={bodyId}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="flex flex-col gap-6 border-t border-zinc-800 px-5 py-5">
              {/* Model selector */}
              <div className="flex flex-col gap-2">
                <label
                  htmlFor={modelId}
                  className="text-sm font-medium text-zinc-300"
                >
                  Model
                </label>
                <div className="relative">
                  <select
                    id={modelId}
                    value={selectedModel}
                    onChange={(event) => onModelChange(event.target.value)}
                    disabled={disabled || models.length === 0}
                    className={cn(
                      "w-full appearance-none rounded-xl border border-zinc-800 bg-zinc-900/80 px-4 py-3 pr-10 text-sm text-zinc-100 transition-colors",
                      "hover:border-zinc-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950",
                      "disabled:cursor-not-allowed disabled:opacity-60",
                    )}
                  >
                    {models.length === 0 ? (
                      <option value="">Loading models…</option>
                    ) : (
                      models.map((model) => (
                        <option key={model.id} value={model.id}>
                          {model.label}
                        </option>
                      ))
                    )}
                  </select>
                  <ChevronDown
                    aria-hidden
                    className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500"
                  />
                </div>
                {selected ? (
                  <p className="text-xs leading-relaxed text-zinc-500">
                    {selected.description}
                  </p>
                ) : null}
              </div>

              {/* System prompt */}
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between gap-3">
                  <label
                    htmlFor={promptId}
                    className="text-sm font-medium text-zinc-300"
                  >
                    System prompt
                  </label>
                  <button
                    type="button"
                    onClick={onResetSystemPrompt}
                    disabled={!isCustomized || disabled}
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-md border border-zinc-800 bg-zinc-900/80 px-2.5 py-1 text-xs font-medium text-zinc-400 transition-colors",
                      "hover:border-zinc-700 hover:text-zinc-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-600",
                      "disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-zinc-800 disabled:hover:text-zinc-400",
                    )}
                  >
                    <RotateCcw className="h-3 w-3" />
                    Reset to default
                  </button>
                </div>
                <textarea
                  id={promptId}
                  value={systemPrompt}
                  onChange={(event) => onSystemPromptChange(event.target.value)}
                  disabled={disabled}
                  rows={8}
                  spellCheck={false}
                  placeholder="Instructions that steer how Claude writes the report…"
                  className={cn(
                    "w-full resize-y rounded-xl border border-zinc-800 bg-zinc-900/80 px-4 py-3 font-mono text-xs leading-relaxed text-zinc-100 placeholder:text-zinc-600 transition-colors",
                    "hover:border-zinc-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950",
                    "disabled:cursor-not-allowed disabled:opacity-60",
                  )}
                />
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs text-zinc-500">
                    {isCustomized
                      ? "Customized — saved locally for next time."
                      : "Using the server default."}
                  </span>
                  <span className="text-xs tabular-nums text-zinc-600">
                    {systemPrompt.length.toLocaleString()} chars
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
