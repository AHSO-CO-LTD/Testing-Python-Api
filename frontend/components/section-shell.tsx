import type { ReactNode } from 'react';

type SectionShellProps = {
  title: string;
  action?: ReactNode;
  children: ReactNode;
  tone?: 'default' | 'subtle' | 'warning';
};

const toneClassMap = {
  default: 'border-[color:var(--border-strong)] bg-[color:var(--surface-strong)]',
  subtle: 'border-[color:var(--border-soft)] bg-[color:var(--surface-soft)]',
  warning: 'border-[color:var(--warning-border)] bg-[color:var(--warning-surface)]',
};

export function SectionShell({
  title,
  action,
  children,
  tone = 'default',
}: SectionShellProps) {
  return (
    <section
      className={`rounded-2xl border p-5 ${toneClassMap[tone]}`}
    >
      <div className="mb-4 flex flex-col gap-3 border-b border-[color:var(--border-soft)] pb-4 md:flex-row md:items-start md:justify-between">
        <div className="space-y-1">
          <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-[color:var(--muted-strong)]">
            {title}
          </h2>
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
      {children}
    </section>
  );
}
