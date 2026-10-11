import { Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { ChatMessage as Message } from "../types/chat";
import { ExecutionDetails } from "./ExecutionDetails";
import { SourceCard } from "./SourceCard";

interface Props {
  message: Message;
}

function removeSourcesSection(content: string): string {
  const lines = content.split("\n");

  const sourceIndex = lines.findIndex((line) => {
    const normalized = line
      .trim()
      .replace(/^#{1,6}\s*/, "")
      .replace(/\*\*/g, "")
      .toLowerCase();

    return (
      normalized === "fonte:" ||
      normalized === "fonte" ||
      normalized === "fontes:" ||
      normalized === "fontes"
    );
  });

  if (sourceIndex === -1) {
    return content;
  }

  return lines
    .slice(0, sourceIndex)
    .join("\n")
    .trimEnd();
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";

  const displayedContent =
    !isUser &&
    !message.isStreaming &&
    message.metadata?.sources?.length
      ? removeSourcesSection(message.content)
      : message.content;

  return (
    <article
      className={`message ${isUser ? "user-message" : "ai-message"}`}
    >
      <div className="avatar">
        {isUser ? <User size={18} /> : <Bot size={19} />}
      </div>

      <div className="message-body">
        <div className="message-author">
          {isUser ? "Você" : "Panvel AI"}
        </div>

        <div className="message-content">
          {isUser ? (
            displayedContent
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {displayedContent}
            </ReactMarkdown>
          )}

          {message.isStreaming && (
            <span className="streaming-cursor" />
          )}
        </div>

        {!isUser &&
          message.metadata?.sources &&
          message.metadata.sources.length > 0 && (
            <div className="sources">
              {message.metadata.sources.map((source) => (
                <SourceCard
                  source={source}
                  key={source}
                />
              ))}
            </div>
          )}

        {!isUser && !message.isStreaming && (
          <ExecutionDetails
            metadata={message.metadata}
          />
        )}
      </div>
    </article>
  );
}