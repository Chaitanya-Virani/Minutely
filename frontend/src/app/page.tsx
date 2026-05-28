import { ThreeDocUploader } from "@/components/ThreeDocUploader";

export default function HomePage(): JSX.Element {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 py-12 sm:px-6 lg:px-8 lg:py-20">
      <header className="mb-12 flex flex-col items-start gap-4 lg:mb-16">
        <span className="inline-flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900/60 px-3 py-1 text-xs font-medium uppercase tracking-wider text-zinc-400">
          <span className="h-1.5 w-1.5 rounded-full bg-teal-400" />
          Meeting Intelligence
        </span>
        <h1 className="bg-gradient-to-br from-zinc-50 via-zinc-100 to-zinc-400 bg-clip-text text-4xl font-semibold leading-tight tracking-tight text-transparent sm:text-5xl lg:text-6xl">
          Three documents in. <br className="hidden sm:block" />
          One sharp report out.
        </h1>
        <p className="max-w-2xl text-base leading-relaxed text-zinc-400 sm:text-lg">
          Drop in your own context, the client&apos;s context, and the raw meeting
          transcript. Minutely sends the lot to Claude in a single pass and gives you
          back a polished PDF you can actually use.
        </p>
      </header>

      <ThreeDocUploader />

      <footer className="mt-auto pt-16 text-xs text-zinc-600">
        Internal tool. Stateless pipeline. Documents are never persisted.
      </footer>
    </main>
  );
}
