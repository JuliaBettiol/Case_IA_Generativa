import type {
  ApiMessage,
  ExecutionMetadata,
  StreamEventName,
} from "../types/chat";

const API_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface StreamCallbacks {
  onMetadata: (metadata: ExecutionMetadata) => void;
  onContent: (text: string) => void;
  onDone: (metadata: ExecutionMetadata) => void;
  onError: (message: string) => void;
}

interface ParsedEvent {
  event: StreamEventName;
  data: string;
}

function parseEvent(block: string): ParsedEvent | null {
  let event: StreamEventName | null = null;
  const dataLines: string[] = [];

  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim() as StreamEventName;
    }

    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  if (!event || dataLines.length === 0) {
    return null;
  }

  return {
    event,
    data: dataLines.join("\n"),
  };
}

function handleEvent(
  block: string,
  callbacks: StreamCallbacks,
) {
  const parsed = parseEvent(block);

  if (!parsed) {
    return;
  }

  const data = JSON.parse(parsed.data);

  if (parsed.event === "metadata") {
    callbacks.onMetadata(data);
    return;
  }

  if (parsed.event === "content") {
    callbacks.onContent(data.text ?? "");
    return;
  }

  if (parsed.event === "done") {
    callbacks.onDone(data);
    return;
  }

  if (parsed.event === "error") {
    callbacks.onError(
      data.message ?? "Erro ao processar a mensagem.",
    );
  }
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/health`, {
      method: "GET",
    });

    return response.ok;
  } catch {
    return false;
  }
}

export async function streamChat(
  messages: ApiMessage[],
  callbacks: StreamCallbacks,
): Promise<void> {
  const response = await fetch(`${API_URL}/api/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ messages }),
  });

  if (!response.ok) {
    throw new Error(
      `Não foi possível processar a solicitação (${response.status}).`,
    );
  }

  if (!response.body) {
    throw new Error(
      "O navegador não disponibilizou o streaming da resposta.",
    );
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();

    if (done) {
      buffer += decoder.decode();

      const finalBlock = buffer.trim();

      if (finalBlock) {
        handleEvent(finalBlock, callbacks);
      }

      break;
    }

    buffer += decoder.decode(value, { stream: true });
    buffer = buffer.replace(/\r\n/g, "\n");

    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";

    for (const block of blocks) {
      handleEvent(block, callbacks);
    }
  }
}