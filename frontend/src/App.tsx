import {
  useEffect,
  useRef,
  useState,
} from "react";
import {
  ShieldCheck,
  WifiOff,
} from "lucide-react";

import { ChatMessage } from "./components/ChatMessage";
import { Composer } from "./components/Composer";
import { Welcome } from "./components/Welcome";
import {
  checkHealth,
  streamChat,
} from "./services/api";

import type {
  ApiMessage,
  ChatMessage as ChatMessageType,
} from "./types/chat";

import "./index.css";

function createId() {
  return crypto.randomUUID();
}

function App() {
  const [messages, setMessages] =
    useState<ChatMessageType[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [backendOnline, setBackendOnline] =
    useState<boolean | null>(null);

  const messagesRef = useRef<ChatMessageType[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  function updateMessages(next: ChatMessageType[]) {
    messagesRef.current = next;
    setMessages(next);
  }

  function updateAssistant(
    assistantId: string,
    updater: (message: ChatMessageType) => ChatMessageType,
  ) {
    const next = messagesRef.current.map((message) =>
      message.id === assistantId
        ? updater(message)
        : message,
    );

    updateMessages(next);
  }

  useEffect(() => {
    let active = true;

    async function verifyBackend() {
      const online = await checkHealth();

      if (active) {
        setBackendOnline(online);
      }
    }

    void verifyBackend();

    const interval = window.setInterval(
      verifyBackend,
      30_000,
    );

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    if (messages.length === 0) {
      return;
    }

    bottomRef.current?.scrollIntoView({
      behavior: isStreaming ? "auto" : "smooth",
      block: "end",
    });
  }, [messages, isStreaming]);

  async function sendMessage(content: string) {
    if (isStreaming || backendOnline === false) {
      return;
    }

    const userMessage: ChatMessageType = {
      id: createId(),
      role: "user",
      content,
    };

    const assistantId = createId();

    const assistantMessage: ChatMessageType = {
      id: assistantId,
      role: "assistant",
      content: "",
      isStreaming: true,
      metadata: {},
    };

    const nextMessages = [
      ...messagesRef.current,
      userMessage,
      assistantMessage,
    ];

    updateMessages(nextMessages);
    setIsStreaming(true);

    const history: ApiMessage[] = nextMessages
      .filter(
        (message) =>
          message.id !== assistantId &&
          message.content.trim().length > 0,
      )
      .map((message) => ({
        role: message.role,
        content: message.content,
      }));

    try {
      await streamChat(history, {
        onMetadata(metadata) {
          updateAssistant(
            assistantId,
            (message) => ({
              ...message,
              metadata: {
                ...message.metadata,
                ...metadata,
              },
            }),
          );
        },

        onContent(text) {
          updateAssistant(
            assistantId,
            (message) => ({
              ...message,
              content: message.content + text,
            }),
          );
        },

        onDone(metadata) {
          updateAssistant(
            assistantId,
            (message) => ({
              ...message,
              isStreaming: false,
              metadata: {
                ...message.metadata,
                ...metadata,
              },
            }),
          );
        },

        onError(errorMessage) {
          updateAssistant(
            assistantId,
            (message) => ({
              ...message,
              content:
                message.content ||
                errorMessage,
              isStreaming: false,
            }),
          );
        },
      });

      setBackendOnline(true);
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Não foi possível conectar ao assistente.";

      setBackendOnline(false);

      updateAssistant(
        assistantId,
        (message) => ({
          ...message,
          content:
            `Não foi possível concluir a solicitação. ${errorMessage}`,
          isStreaming: false,
        }),
      );
    } finally {
      updateAssistant(
        assistantId,
        (message) => ({
          ...message,
          isStreaming: false,
        }),
      );

      setIsStreaming(false);
    }
  }

  function newConversation() {
    if (isStreaming) {
      return;
    }

    updateMessages([]);
  }

  const composerDisabled =
    isStreaming || backendOnline === false;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-symbol">P</div>

          <div>
            <strong>Panvel</strong>
            <span>AI Assistant</span>
          </div>
        </div>

        <div className="header-actions">
          <div
            className={`status ${
              backendOnline === false
                ? "status-offline"
                : ""
            }`}
          >
            {backendOnline === false ? (
              <WifiOff size={14} />
            ) : (
              <span className="status-dot" />
            )}

            {backendOnline === null
              ? "Verificando serviço..."
              : backendOnline
                ? "Assistente online"
                : "Assistente indisponível"}
          </div>

          {messages.length > 0 && (
            <button
              className="new-chat"
              onClick={newConversation}
              disabled={isStreaming}
            >
              Nova conversa
            </button>
          )}
        </div>
      </header>

      <main className="chat-container">
        {messages.length === 0 ? (
          <Welcome onSuggestion={sendMessage} />
        ) : (
          <section className="conversation">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
              />
            ))}

            <div
              ref={bottomRef}
              className="scroll-anchor"
              aria-hidden="true"
            />
          </section>
        )}
      </main>

      <footer className="composer-area">
        <div className="composer-wrapper">
          {backendOnline === false && (
            <div className="service-warning">
              <WifiOff size={15} />
              O backend está indisponível. Verifique o serviço
              para continuar.
            </div>
          )}

          <Composer
            disabled={composerDisabled}
            onSend={sendMessage}
          />

          <div className="disclaimer">
            <ShieldCheck size={13} />
            <span>
              Respostas sobre medicamentos são baseadas nas
              bulas disponíveis e não substituem orientação
              profissional.
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;