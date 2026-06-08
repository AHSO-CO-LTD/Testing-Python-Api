import type { InputHTMLAttributes } from 'react';

type FieldInputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
  tooltip?: string;
};

export function FieldInput({
  label,
  hint,
  tooltip,
  className = '',
  ...props
}: FieldInputProps) {
  return (
    <label className="block space-y-2">
      <span className="flex items-center gap-2 text-sm font-medium text-[color:var(--muted-strong)]">
        <span>{label}</span>
        {tooltip ? (
          <span
            className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-[color:var(--border-soft)] text-[10px] text-[color:var(--muted)]"
            title={tooltip}
          >
            ?
          </span>
        ) : null}
      </span>
      <input
        {...props}
        className={`w-full rounded-xl border border-[color:var(--border-soft)] bg-[color:var(--surface)] px-3 py-2.5 text-sm text-[color:var(--foreground)] outline-none transition focus:border-[color:var(--accent)] ${className}`}
      />
      {hint ? (
        <span className="block text-xs text-[color:var(--muted)]">{hint}</span>
      ) : null}
    </label>
  );
}
