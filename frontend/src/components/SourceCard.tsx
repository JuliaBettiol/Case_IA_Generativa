import { FileText } from "lucide-react";

interface SourceCardProps {
  source: string;
}

export function SourceCard({ source }: SourceCardProps) {
  const readableName = source
    .replace(".pdf", "")
    .replace(/^\d+_/, "")
    .replaceAll("_", " ");

  return (
    <div className="source-card">
      <div className="source-icon">
        <FileText size={17} />
      </div>

      <div>
        <span className="source-label">Fonte da resposta</span>
        <strong>{readableName}</strong>
      </div>
    </div>
  );
}
