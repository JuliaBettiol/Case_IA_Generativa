import {
  Activity,
  ChevronDown,
  Database,
  Wrench,
} from "lucide-react";

import type { ExecutionMetadata } from "../types/chat";

interface Props {
  metadata?: ExecutionMetadata;
}

export function ExecutionDetails({ metadata }: Props) {
  if (!metadata) {
    return null;
  }

  const hasTools =
    (metadata.tool_calls?.length ?? 0) > 0;

  const retrievedCount =
    metadata.retrieved_documents?.length ?? 0;

  const queryLabel =
    retrievedCount > 0
      ? "Consulta utilizada no RAG"
      : "Consulta analisada";

  return (
    <details className="execution-details">
      <summary>
        <span>
          <Activity size={16} />
          Detalhes da execução
        </span>
        <ChevronDown size={16} />
      </summary>

      <div className="execution-content">
        {metadata.route && (
          <div className="execution-row">
            <span>Rota</span>
            <strong>
              {metadata.route === "bulas"
                ? "RAG · Bulas"
                : "Tools · Filiais"}
            </strong>
          </div>
        )}

        {metadata.search_query && (
          <div className="execution-block">
            <span>
              <Database size={15} />
              {queryLabel}
            </span>
            <code>{metadata.search_query}</code>
          </div>
        )}

        {hasTools &&
          metadata.tool_calls?.map((tool, index) => (
            <div
              className="execution-block"
              key={`${tool.name}-${index}`}
            >
              <span>
                <Wrench size={15} />
                {tool.name}
              </span>

              <pre>
                {JSON.stringify(tool.arguments, null, 2)}
              </pre>
            </div>
          ))}

        {retrievedCount > 0 && (
          <div className="execution-row">
            <span>Chunks recuperados</span>
            <strong>{retrievedCount}</strong>
          </div>
        )}

        {metadata.usage && (
          <>
            <div className="execution-row">
              <span>Tokens de entrada</span>
              <strong>
                {metadata.usage.prompt_tokens}
              </strong>
            </div>

            <div className="execution-row">
              <span>Tokens de saída</span>
              <strong>
                {metadata.usage.completion_tokens}
              </strong>
            </div>

            <div className="execution-row">
              <span>Total de tokens</span>
              <strong>
                {metadata.usage.total_tokens}
              </strong>
            </div>
          </>
        )}

        {metadata.latency_ms !== undefined && (
          <div className="execution-row">
            <span>Latência</span>
            <strong>
              {(metadata.latency_ms / 1000).toFixed(2)} s
            </strong>
          </div>
        )}

        {metadata.trace_id && (
          <div className="execution-block trace">
            <span>Trace ID</span>
            <code>{metadata.trace_id}</code>
          </div>
        )}
      </div>
    </details>
  );
}