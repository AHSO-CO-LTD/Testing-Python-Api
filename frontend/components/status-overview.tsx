type StatusOverviewProps = {
  apiConnected: boolean;
  isCheckingApi: boolean;
  wsConnected: boolean;
  modelReady: boolean;
  configSynced: boolean;
  labels: {
    api: string;
    config: string;
    model: string;
    socket: string;
    checking: string;
    online: string;
    offline: string;
    synced: string;
    pending: string;
    loaded: string;
    required: string;
    ready: string;
    waiting: string;
  };
};

type StatusItem = {
  label: string;
  value: string;
  state: 'healthy' | 'pending' | 'idle';
};

function StatusBadge({ label, value, state }: StatusItem) {
  const stateClassMap = {
    healthy: 'bg-[color:var(--success-surface)] text-[color:var(--success-text)]',
    pending: 'bg-[color:var(--warning-surface)] text-[color:var(--warning-text)]',
    idle: 'bg-[color:var(--surface-muted)] text-[color:var(--muted-strong)]',
  };

  return (
    <div className="rounded-2xl border border-[color:var(--border-soft)] bg-[color:var(--surface-soft)] p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--muted)]">
          {label}
        </span>
        <span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${stateClassMap[state]}`}>
          {value}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-[color:var(--surface-muted)]">
        <div
          className={`h-full rounded-full transition-all ${
            state === 'healthy'
              ? 'w-full bg-[color:var(--success-text)]'
              : state === 'pending'
                ? 'w-2/3 bg-[color:var(--warning-text)]'
                : 'w-1/3 bg-[color:var(--muted)]'
          }`}
        />
      </div>
    </div>
  );
}

export function StatusOverview({
  apiConnected,
  isCheckingApi,
  wsConnected,
  modelReady,
  configSynced,
  labels,
}: StatusOverviewProps) {
  const items: StatusItem[] = [
    {
      label: labels.api,
      value: isCheckingApi ? labels.checking : apiConnected ? labels.online : labels.offline,
      state: isCheckingApi ? 'pending' : apiConnected ? 'healthy' : 'idle',
    },
    {
      label: labels.config,
      value: configSynced ? labels.synced : labels.pending,
      state: configSynced ? 'healthy' : 'pending',
    },
    {
      label: labels.model,
      value: modelReady ? labels.loaded : labels.required,
      state: modelReady ? 'healthy' : 'idle',
    },
    {
      label: labels.socket,
      value: wsConnected ? labels.ready : labels.waiting,
      state: wsConnected ? 'healthy' : apiConnected ? 'pending' : 'idle',
    },
  ];

  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <StatusBadge key={item.label} {...item} />
      ))}
    </div>
  );
}
