let forbidden = false;

const listeners = new Set<() => void>();

export function markForbidden(): void {
  if (forbidden) {
    return;
  }

  forbidden = true;
  notify();
}

export function clearForbidden(): void {
  if (!forbidden) {
    return;
  }

  forbidden = false;
  notify();
}

export function getForbidden(): boolean {
  return forbidden;
}

export function subscribeForbidden(listener: () => void): () => void {
  listeners.add(listener);

  return () => {
    listeners.delete(listener);
  };
}

function notify(): void {
  for (const listener of listeners) {
    listener();
  }
}
