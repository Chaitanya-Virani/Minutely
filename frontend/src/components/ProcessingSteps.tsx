"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Check } from "lucide-react";

import { cn } from "@/lib/cn";

export type ProcessingStage = "parsing" | "claude" | "pdf";

interface ProcessingStepsProps {
  visible: boolean;
  activeStage: ProcessingStage;
}

interface StepDef {
  id: ProcessingStage;
  label: string;
  detail: string;
}

const STEPS: StepDef[] = [
  {
    id: "parsing",
    label: "Parsing documents",
    detail: "Extracting text from your three uploads.",
  },
  {
    id: "claude",
    label: "Calling Claude",
    detail: "Single pass with the 1M-token context window.",
  },
  {
    id: "pdf",
    label: "Building PDF",
    detail: "Composing the report layout and tables.",
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.05 },
  },
  exit: { opacity: 0, transition: { duration: 0.2 } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: "easeOut" } },
  exit: { opacity: 0, y: -4, transition: { duration: 0.15 } },
};

function stageIndex(stage: ProcessingStage): number {
  return STEPS.findIndex((step) => step.id === stage);
}

export function ProcessingSteps({
  visible,
  activeStage,
}: ProcessingStepsProps): JSX.Element {
  const activeIdx = stageIndex(activeStage);

  return (
    <AnimatePresence mode="wait">
      {visible ? (
        <motion.div
          key="processing"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 backdrop-blur"
        >
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-400">
              Processing
            </h3>
            <span className="text-xs text-zinc-500">
              This usually takes 20–40 seconds.
            </span>
          </div>
          <ol className="relative space-y-4 pl-6">
            <span
              aria-hidden
              className="absolute left-[10px] top-2 bottom-2 w-px bg-zinc-800"
            />
            {STEPS.map((step, idx) => {
              const isDone = idx < activeIdx;
              const isActive = idx === activeIdx;
              return (
                <motion.li
                  key={step.id}
                  variants={itemVariants}
                  className="relative"
                >
                  <span
                    className={cn(
                      "absolute -left-6 top-0.5 flex h-5 w-5 items-center justify-center rounded-full border transition-colors",
                      isDone
                        ? "border-teal-500/60 bg-teal-500/15 text-teal-300"
                        : isActive
                          ? "border-indigo-500/60 bg-indigo-500/15"
                          : "border-zinc-800 bg-zinc-900",
                    )}
                  >
                    {isDone ? (
                      <Check className="h-3 w-3" />
                    ) : isActive ? (
                      <motion.span
                        className="h-2 w-2 rounded-full bg-indigo-400"
                        animate={{ scale: [1, 1.35, 1], opacity: [0.7, 1, 0.7] }}
                        transition={{
                          duration: 1.4,
                          repeat: Infinity,
                          ease: "easeInOut",
                        }}
                      />
                    ) : (
                      <span className="h-2 w-2 rounded-full bg-zinc-700" />
                    )}
                  </span>
                  <div className="flex flex-col gap-0.5">
                    <p
                      className={cn(
                        "text-sm font-medium transition-colors",
                        isDone
                          ? "text-zinc-300"
                          : isActive
                            ? "text-zinc-50"
                            : "text-zinc-500",
                      )}
                    >
                      {step.label}
                    </p>
                    <p className="text-xs text-zinc-500">{step.detail}</p>
                  </div>
                </motion.li>
              );
            })}
          </ol>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
