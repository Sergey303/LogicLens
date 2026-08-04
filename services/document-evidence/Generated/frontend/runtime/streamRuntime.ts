export interface StreamOperationHandle<TChunk, TFinal> {
  stream: AsyncIterable<TChunk>;
  final: Promise<TFinal>;
  cancel: () => void;
}

export async function* readNdjsonStream<TItem>(stream: ReadableStream<Uint8Array>): AsyncIterable<TItem> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      yield* drainCompleteLines<TItem>(() => buffer, (next) => { buffer = next; });
    }

    buffer += decoder.decode();
    const tail = buffer.trim();
    if (tail.length > 0) {
      yield JSON.parse(tail) as TItem;
    }
  } finally {
    reader.releaseLock();
  }
}

function* drainCompleteLines<TItem>(
  readBuffer: () => string,
  writeBuffer: (value: string) => void,
): Iterable<TItem> {
  let buffer = readBuffer();
  let newlineIndex = buffer.indexOf("\n");
  while (newlineIndex >= 0) {
    const line = buffer.slice(0, newlineIndex).trim();
    buffer = buffer.slice(newlineIndex + 1);
    if (line.length > 0) {
      yield JSON.parse(line) as TItem;
    }
    newlineIndex = buffer.indexOf("\n");
  }

  writeBuffer(buffer);
}
