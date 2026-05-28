"use client";

import { motion } from "framer-motion";
import { Loader2, Sparkles } from "lucide-react";

import { cn } from "@/lib/cn";

interface GenerateButtonProps {
  disabled: boolean;
  loading: boolean;
  onClick: () => void;
}

export function GenerateButton({
  disabled,
  loading,
  onClick,
}: GenerateButtonProps): JSX.Element {
  const isDisabled = disabled || loading;

  return (
    <motion.button
      type="button"
      onClick={onClick}
      disabled={isDisabled}
      whileHover={isDisabled ? undefined : { scale: 1.015 }}
      whileTap={isDisabled ? undefined : { scale: 0.985 }}
      transition={{ type: "spring", stiffness: 400, damping: 22 }}
      className={cn(
        "group relative inline-flex w-full items-center justify-center gap-2 overflow-hidden rounded-2xl px-6 py-4 text-base font-semibold transition-all duration-200",
        "bg-gradient-to-r from-indigo-500 via-indigo-500 to-teal-500 text-white shadow-lg shadow-indigo-500/20",
        "hover:shadow-xl hover:shadow-indigo-500/30",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950",
        isDisabled &&
          "cursor-not-allowed bg-zinc-800 from-zinc-800 via-zinc-800 to-zinc-800 text-zinc-500 shadow-none hover:shadow-none",
      )}
    >
      <span className="pointer-events-none absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform duration-700 ease-out group-hover:translate-x-full" />
      {loading ? (
        <>
          <Loader2 className="h-5 w-5 animate-spin" />
          Generating report…
        </>
      ) : (
        <>
          <Sparkles className="h-5 w-5" />
          Generate Report
        </>
      )}
    </motion.button>
  );
}
