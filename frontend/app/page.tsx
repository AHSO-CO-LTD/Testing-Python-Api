import { OCRPanel } from '@/components/ocr-panel';

export default function Home() {
  return (
    <main className="min-h-screen bg-[color:var(--background)] px-4 py-6 md:px-6 md:py-8">
      <div className="mx-auto max-w-7xl">
        <OCRPanel />
      </div>
    </main>
  );
}
