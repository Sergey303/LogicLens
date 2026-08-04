import type { RealtimeCommandDescriptor } from "./realtimeTypes";

export interface CommandExecutionHandle<TAck> {
  readonly promise: Promise<TAck>;
  readonly cancel: () => void;
  readonly affectedEndpointKeys: readonly string[];
}

export interface CommandAckMap { readonly [commandKey: string]: unknown; }
export interface CommandErrorMap { readonly [commandKey: string]: unknown; }

export interface RealtimeCommandRuntimeOptions {
  readonly correlationPrefix?: string;
  readonly timeoutMs?: number;
  readonly getCommandDescriptor?: (commandKey: string) => RealtimeCommandDescriptor | undefined;
  readonly resolveAffectedEndpointKeys?: (commandKey: string) => readonly string[];
  readonly onAffectedEndpointKeys?: (commandKey: string, endpointKeys: readonly string[]) => void | Promise<void>;
}

export interface RealtimeCommandRuntime<
  TCommandPayloadByKey extends object,
  TCommandAckByKey extends object,
  TCommandErrorByKey extends object,
> {
  readonly executeCommand: <K extends Extract<keyof TCommandPayloadByKey & keyof TCommandAckByKey, string>>(
    commandKey: K,
    payload: TCommandPayloadByKey[K],
  ) => CommandExecutionHandle<TCommandAckByKey[K]>;
  readonly registerAckHandler: <K extends Extract<keyof TCommandAckByKey, string>>(
    commandKey: K,
    handler: (ack: TCommandAckByKey[K]) => void,
  ) => () => void;
  readonly registerErrorHandler: <K extends Extract<keyof TCommandErrorByKey, string>>(
    commandKey: K,
    handler: (error: TCommandErrorByKey[K]) => void,
  ) => () => void;
  readonly sendRaw: (envelope: unknown) => void;
  readonly resolveAck: (envelope: { correlationId?: string; commandKey?: string; payload?: unknown; error?: unknown }) => void;
}

export function createRealtimeCommandRuntime<
  TCommandPayloadByKey extends object,
  TCommandAckByKey extends object,
  TCommandErrorByKey extends object,
>(
  sendRaw: (envelope: unknown) => void,
  options?: string | RealtimeCommandRuntimeOptions,
): RealtimeCommandRuntime<TCommandPayloadByKey, TCommandAckByKey, TCommandErrorByKey> {
  const runtimeOptions = typeof options === "string" ? { correlationPrefix: options } : options;
  const timeoutMs = runtimeOptions?.timeoutMs ?? 30000;
  let correlationCounter = 0;
  const pendingAcks = new Map<string, PendingAck>();
  const ackHandlers = new Map<string, Set<(value: unknown) => void>>();
  const errorHandlers = new Map<string, Set<(value: unknown) => void>>();

  function executeCommand<K extends Extract<keyof TCommandPayloadByKey & keyof TCommandAckByKey, string>>(
    commandKey: K,
    payload: TCommandPayloadByKey[K],
  ): CommandExecutionHandle<TCommandAckByKey[K]> {
    const descriptor = runtimeOptions?.getCommandDescriptor?.(commandKey);
    const affectedEndpointKeys = resolveAffectedEndpointKeys(commandKey, descriptor);
    const correlationId = `${runtimeOptions?.correlationPrefix ?? "cmd"}_${++correlationCounter}_${Date.now()}`;
    let cancelled = false;
    const promise = new Promise<TCommandAckByKey[K]>((resolve, reject) => {
      pendingAcks.set(correlationId, { commandKey, affectedEndpointKeys, resolve: resolve as (value: unknown) => void, reject });
      sendRaw({ realtimeKey: commandKey, wireName: descriptor?.wireName ?? commandKey, correlationId, payload });
      setTimeout(() => {
        const pending = pendingAcks.get(correlationId);
        if (pending) {
          pendingAcks.delete(correlationId);
          if (!cancelled) { pending.reject(new Error(`Command ${commandKey} timed out`)); }
        }
      }, timeoutMs);
    });
    return {
      promise,
      cancel: () => rejectPending(correlationId, new Error("Command cancelled"), () => { cancelled = true; }),
      affectedEndpointKeys,
    };
  }

  function rejectPending(correlationId: string, error: unknown, beforeReject?: () => void): void {
    beforeReject?.();
    const pending = pendingAcks.get(correlationId);
    if (pending) { pendingAcks.delete(correlationId); pending.reject(error); }
  }

  function registerAckHandler<K extends Extract<keyof TCommandAckByKey, string>>(
    commandKey: K,
    handler: (ack: TCommandAckByKey[K]) => void,
  ): () => void {
    return registerHandler(ackHandlers, commandKey, handler as (value: unknown) => void);
  }

  function registerErrorHandler<K extends Extract<keyof TCommandErrorByKey, string>>(
    commandKey: K,
    handler: (error: TCommandErrorByKey[K]) => void,
  ): () => void {
    return registerHandler(errorHandlers, commandKey, handler as (value: unknown) => void);
  }

  function resolveAck(envelope: { correlationId?: string; commandKey?: string; payload?: unknown; error?: unknown }): void {
    const commandKey = envelope.commandKey;
    if (envelope.error) {
      notify(errorHandlers, commandKey, envelope.error);
      if (envelope.correlationId) { rejectPending(envelope.correlationId, envelope.error); }
      return;
    }
    if (!envelope.correlationId) { return; }
    const pending = pendingAcks.get(envelope.correlationId);
    if (pending) {
      const resolvedCommandKey = commandKey ?? pending.commandKey;
      pendingAcks.delete(envelope.correlationId);
      pending.resolve(envelope.payload);
      notify(ackHandlers, resolvedCommandKey, envelope.payload);
      notifyAffectedEndpointKeys(resolvedCommandKey, pending.affectedEndpointKeys);
    }
  }

  function resolveAffectedEndpointKeys(
    commandKey: string,
    descriptor: RealtimeCommandDescriptor | undefined,
  ): readonly string[] {
    return runtimeOptions?.resolveAffectedEndpointKeys?.(commandKey) ?? descriptor?.relatedEndpointKeys ?? [];
  }

  function notifyAffectedEndpointKeys(commandKey: string, endpointKeys: readonly string[]): void {
    if (endpointKeys.length > 0) { void runtimeOptions?.onAffectedEndpointKeys?.(commandKey, endpointKeys); }
  }

  return { executeCommand, registerAckHandler, registerErrorHandler, sendRaw, resolveAck };
}

interface PendingAck {
  readonly commandKey: string;
  readonly affectedEndpointKeys: readonly string[];
  readonly resolve: (value: unknown) => void;
  readonly reject: (reason: unknown) => void;
}

function registerHandler(map: Map<string, Set<(value: unknown) => void>>, key: string, handler: (value: unknown) => void): () => void {
  if (!map.has(key)) { map.set(key, new Set()); }
  map.get(key)!.add(handler);
  return () => { map.get(key)?.delete(handler); };
}

function notify(map: Map<string, Set<(value: unknown) => void>>, key: string | undefined, value: unknown): void {
  for (const handler of map.get(key ?? "") ?? []) { handler(value); }
}
