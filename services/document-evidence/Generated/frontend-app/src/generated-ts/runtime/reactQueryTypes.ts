import type {
  QueryClient,
  UseMutationOptions,
  UseMutationResult,
  UseQueryOptions,
  UseQueryResult,
} from "@tanstack/react-query";
import type { AvailabilityState } from "./availabilityTypes";
import type { ActionBinding } from "./actionRuntime";
import type { MutationBinding } from "./mutationRuntime";
import type { OperationLifecycle } from "./operationLifecycleTypes";
import type { QueryKey } from "./queryKeyRuntime";
import type { QueryBinding } from "./queryRuntime";
import type { TransportResponseMetadata } from "./responseMetadata";

export type GeneratedQueryOptions<TOutput, TError = unknown> =
  Omit<UseQueryOptions<TOutput, TError, TOutput, QueryKey>, "queryKey" | "queryFn">;

export type GeneratedEndpointInput<TInput> =
  | TInput
  | {
      readonly args?: unknown;
      readonly request?: unknown;
      readonly body?: unknown;
      readonly [key: string]: unknown;
    };

export type GeneratedQueryHookResult<TInput, TOutput, TError = unknown> = UseQueryResult<TOutput, TError> & {
  readonly binding: QueryBinding<TInput, TOutput>;
  readonly availability: AvailabilityState;
  readonly isVisible: boolean;
  readonly isEnabled: boolean;
  readonly disabledReason: string | null;
  readonly query: UseQueryResult<TOutput, TError>;
  readonly execute: (input: GeneratedEndpointInput<TInput>) => Promise<TOutput>;
  readonly lifecycle: OperationLifecycle<TOutput, TError>;
};

export interface GeneratedStreamOptions<TItem, TError = unknown> {
  readonly enabled?: boolean;
  readonly autoStart?: boolean;
  readonly onItem?: (item: TItem) => void;
  readonly onError?: (error: TError) => void;
  readonly onComplete?: (items: readonly TItem[]) => void;
}

export interface GeneratedStreamHookResult<TInput, TItem, TError = unknown> {
  readonly binding: QueryBinding<TInput, AsyncIterable<TItem>>;
  readonly availability: AvailabilityState;
  readonly isVisible: boolean;
  readonly isEnabled: boolean;
  readonly disabledReason: string | null;
  readonly items: readonly TItem[];
  readonly latestItem: TItem | null;
  readonly isStreaming: boolean;
  readonly error: TError | null;
  readonly start: (input?: GeneratedEndpointInput<TInput>) => Promise<readonly TItem[]>;
  readonly cancel: () => void;
  readonly clear: () => void;
}

export type GeneratedMutationOptions<TInput, TOutput, TError = unknown, TContext = unknown> =
  Omit<UseMutationOptions<TOutput, TError, GeneratedEndpointInput<TInput>, TContext>, "mutationFn"> & {
    readonly invalidateOnSuccess?: boolean;
    readonly onResponse?: (metadata: TransportResponseMetadata) => void;
  };

export type GeneratedMutationHookResult<TInput, TOutput, TError = unknown, TContext = unknown> =
  UseMutationResult<TOutput, TError, GeneratedEndpointInput<TInput>, TContext> & {
    readonly binding: MutationBinding<TInput, TOutput>;
    readonly availability: AvailabilityState;
    readonly isVisible: boolean;
    readonly isEnabled: boolean;
    readonly disabledReason: string | null;
    readonly mutation: UseMutationResult<TOutput, TError, GeneratedEndpointInput<TInput>, TContext>;
    readonly execute: (input: GeneratedEndpointInput<TInput>) => Promise<TOutput>;
    readonly lifecycle: OperationLifecycle<TOutput, TError>;
    readonly lastResponse: TransportResponseMetadata | null;
    readonly warnings: readonly string[];
  };

export type GeneratedActionOptions<TInput, TOutput, TError = unknown, TContext = unknown> =
  GeneratedMutationOptions<TInput, TOutput, TError, TContext>;

export type GeneratedActionHookResult<TInput, TOutput, TError = unknown, TContext = unknown> =
  UseMutationResult<TOutput, TError, GeneratedEndpointInput<TInput>, TContext> & {
    readonly binding: ActionBinding<TInput, TOutput>;
    readonly availability: AvailabilityState;
    readonly isVisible: boolean;
    readonly isEnabled: boolean;
    readonly disabledReason: string | null;
    readonly action: UseMutationResult<TOutput, TError, GeneratedEndpointInput<TInput>, TContext>;
    readonly execute: (input: GeneratedEndpointInput<TInput>) => Promise<TOutput>;
    readonly lifecycle: OperationLifecycle<TOutput, TError>;
    readonly redirect: (input?: GeneratedEndpointInput<TInput>) => void;
    readonly lastResponse: TransportResponseMetadata | null;
    readonly warnings: readonly string[];
  };

export type GeneratedQueryClient = QueryClient;
