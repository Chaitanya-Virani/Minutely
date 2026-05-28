"use client";

import { motion } from "framer-motion";
import { File as FileIcon, UploadCloud, X } from "lucide-react";
import { useCallback, useId, useRef, useState } from "react";
import type { ChangeEvent, DragEvent, MouseEvent } from "react";

import { cn } from "@/lib/cn";

export type AccentName = "indigo" | "teal" | "amber";

interface UploadZoneProps {
  label: string;
  description: string;
  acceptExtensions: string[];
  file: File | null;
  onFile: (file: File | null) => void;
  accent: AccentName;
  disabled?: boolean;
}

const accentClasses: Record<
  AccentName,
  {
    ring: string;
    border: string;
    iconBg: string;
    iconText: string;
    dot: string;
    gradient: string;
  }
> = {
  indigo: {
    ring: "ring-indigo-500/60",
    border: "hover:border-indigo-500/60",
    iconBg: "bg-indigo-500/10",
    iconText: "text-indigo-300",
    dot: "bg-indigo-400",
    gradient: "from-indigo-500/20 via-transparent to-transparent",
  },
  teal: {
    ring: "ring-teal-500/60",
    border: "hover:border-teal-500/60",
    iconBg: "bg-teal-500/10",
    iconText: "text-teal-300",
    dot: "bg-teal-400",
    gradient: "from-teal-500/20 via-transparent to-transparent",
  },
  amber: {
    ring: "ring-amber-500/60",
    border: "hover:border-amber-500/60",
    iconBg: "bg-amber-500/10",
    iconText: "text-amber-300",
    dot: "bg-amber-400",
    gradient: "from-amber-500/20 via-transparent to-transparent",
  },
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function isAccepted(file: File, acceptExtensions: string[]): boolean {
  const lower = file.name.toLowerCase();
  return acceptExtensions.some((ext) => lower.endsWith(ext.toLowerCase()));
}

export function UploadZone({
  label,
  description,
  acceptExtensions,
  file,
  onFile,
  accent,
  disabled = false,
}: UploadZoneProps): JSX.Element {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const inputId = useId();
  const palette = accentClasses[accent];

  const acceptAttr = acceptExtensions.join(",");

  const handleFiles = useCallback(
    (incoming: FileList | null) => {
      if (!incoming || incoming.length === 0) {
        return;
      }
      const next = incoming[0];
      if (!isAccepted(next, acceptExtensions)) {
        setError(`Expected ${acceptExtensions.join(" / ")}`);
        return;
      }
      setError(null);
      onFile(next);
    },
    [acceptExtensions, onFile],
  );

  const onDragOver = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      if (disabled) return;
      event.preventDefault();
      setIsDragOver(true);
    },
    [disabled],
  );

  const onDragLeave = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
  }, []);

  const onDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setIsDragOver(false);
      if (disabled) return;
      handleFiles(event.dataTransfer.files);
    },
    [disabled, handleFiles],
  );

  const onChange = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      handleFiles(event.target.files);
      // Reset so re-selecting the same file still fires change
      event.target.value = "";
    },
    [handleFiles],
  );

  const onClear = useCallback(
    (event: MouseEvent<HTMLButtonElement>) => {
      event.stopPropagation();
      onFile(null);
      setError(null);
    },
    [onFile],
  );

  const onClickZone = useCallback(() => {
    if (disabled) return;
    inputRef.current?.click();
  }, [disabled]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="flex w-full flex-col"
    >
      <label
        htmlFor={inputId}
        className="mb-2 flex items-center gap-2 text-sm font-medium text-zinc-300"
      >
        <span className={cn("h-1.5 w-1.5 rounded-full", palette.dot)} />
        {label}
      </label>

      <div
        role="button"
        tabIndex={0}
        aria-disabled={disabled}
        onClick={onClickZone}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onClickZone();
          }
        }}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={cn(
          "group relative flex min-h-[180px] cursor-pointer flex-col items-center justify-center gap-3 overflow-hidden rounded-2xl border border-dashed border-zinc-800 bg-zinc-900/40 p-6 text-center transition-all duration-200",
          "focus:outline-none focus-visible:ring-2",
          palette.border,
          palette.ring,
          isDragOver && cn("border-solid ring-2", palette.ring),
          disabled && "cursor-not-allowed opacity-60",
          file && "border-solid border-zinc-700/80",
        )}
      >
        <div
          className={cn(
            "pointer-events-none absolute inset-0 bg-gradient-to-br opacity-0 transition-opacity duration-300 group-hover:opacity-100",
            palette.gradient,
            isDragOver && "opacity-100",
          )}
        />

        <input
          ref={inputRef}
          id={inputId}
          type="file"
          accept={acceptAttr}
          className="hidden"
          onChange={onChange}
          disabled={disabled}
        />

        {file ? (
          <div className="relative z-10 flex w-full flex-col items-center gap-2">
            <div
              className={cn(
                "flex h-11 w-11 items-center justify-center rounded-xl",
                palette.iconBg,
              )}
            >
              <FileIcon className={cn("h-5 w-5", palette.iconText)} />
            </div>
            <p className="line-clamp-1 max-w-full break-all text-sm font-medium text-zinc-100">
              {file.name}
            </p>
            <p className="text-xs text-zinc-500">{formatBytes(file.size)}</p>
            <button
              type="button"
              onClick={onClear}
              className="mt-1 inline-flex items-center gap-1 rounded-md border border-zinc-800 bg-zinc-900/80 px-2 py-1 text-xs text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-200"
              aria-label="Remove file"
              disabled={disabled}
            >
              <X className="h-3 w-3" />
              Clear
            </button>
          </div>
        ) : (
          <div className="relative z-10 flex flex-col items-center gap-2">
            <div
              className={cn(
                "flex h-11 w-11 items-center justify-center rounded-xl",
                palette.iconBg,
              )}
            >
              <UploadCloud className={cn("h-5 w-5", palette.iconText)} />
            </div>
            <p className="text-sm font-medium text-zinc-200">
              Drop file or click to browse
            </p>
            <p className="text-xs text-zinc-500">{description}</p>
            <p className="text-[10px] uppercase tracking-wider text-zinc-600">
              {acceptExtensions.join(" · ")}
            </p>
          </div>
        )}
      </div>

      {error ? (
        <p className="mt-2 text-xs text-rose-400">{error}</p>
      ) : null}
    </motion.div>
  );
}
