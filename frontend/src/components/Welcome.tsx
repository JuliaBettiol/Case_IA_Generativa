import {
  Building2,
  FileText,
  MessagesSquare,
  Sparkles,
} from "lucide-react";

interface Props {
  onSuggestion: (question: string) => void;
}

const suggestions = [
  {
    icon: FileText,
    label: "Consultar uma bula",
    question: "Quais são os efeitos adversos do Rohydorm?",
  },
  {
    icon: Building2,
    label: "Encontrar filiais",
    question:
      "Quais filiais de Londrina possuem estacionamento e Panvel Clinic?",
  },
  {
    icon: MessagesSquare,
    label: "Explorar a conversa",
    question:
      "Quais filiais de Londrina possuem estacionamento?",
  },
];

export function Welcome({ onSuggestion }: Props) {
  return (
    <section className="welcome">
      <div className="welcome-mark">
        <Sparkles size={25} />
      </div>

      <h1>Como posso ajudar?</h1>

      <p>
        Consulte informações sobre medicamentos nas bulas disponíveis
        ou encontre filiais Panvel de forma rápida e simples.
      </p>

      <div className="suggestions">
        {suggestions.map(({ icon: Icon, label, question }) => (
          <button
            key={question}
            className="suggestion"
            onClick={() => onSuggestion(question)}
          >
            <Icon size={19} />
            <span>
              <strong>{label}</strong>
              <small>{question}</small>
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
