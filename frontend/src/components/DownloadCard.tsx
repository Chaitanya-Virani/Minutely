"use client";

import { motion } from "framer-motion";
import { Download, FileText, RotateCcw } from "lucide-react";
import { useCallback } from "react";

interface DownloadCardProps {
  blob: Blob;
  filename: string;
  onReset: () => void;
}

function formatKB(bytes: number): string {
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export function DownloadCard({
  blob,
  filename,
  onReset,
}: DownloadCardProps): JSX.Element {
  const onDownload = useCallback(() => {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    // Defer revoke to give the browser time to start the download
    window.setTimeout(() => URL.revokeObjectURL(url), 500);
  }, [blob, filename]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="overflow-hidden rounded-2xl border border-teal-500/30 bg-gradient-to-br from-teal-500/10 via-zinc-900/60 to-indigo-500/10 p-6 backdrop-blur"
    >
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-teal-500/15 text-teal-300">
            <FileText className="h-6 w-6" />
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-teal-300">
              Report ready
            </span>
            <p className="break-all text-base font-medium text-zinc-100">
              {filename}
            </p>
            <p className="text-xs text-zinc-400">
              {formatKB(blob.size)} · application/pdf
            </p>
          </div>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <motion.button
            type="button"
            onClick={onDownload}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-teal-500 px-4 py-2.5 text-sm font-semibold text-zinc-950 shadow-lg shadow-teal-500/20 transition-shadow hover:shadow-teal-500/30 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-300 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950"
          >
            <Download className="h-4 w-4" />
            Download PDF
          </motion.button>
          <motion.button
            type="button"
            onClick={onReset}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/80 px-4 py-2.5 text-sm font-medium text-zinc-300 transition-colors hover:border-zinc-700 hover:text-zinc-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-600"
          >
            <RotateCcw className="h-4 w-4" />
            Generate another
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}
