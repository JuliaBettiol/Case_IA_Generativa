import { ArrowUp, LoaderCircle } from "lucide-react";
import {
  type FormEvent,
  type KeyboardEvent,
  useState,
} from "react";

interface Props {
  disabled: boolean;
  onSend: (message: string) => void;
}

export function Composer({ disabled, onSend }: Props) {
  const [value, setValue] = useState("");

  function submit(event?: FormEvent) {
    event?.preventDefault();

    const message = value.trim();

    if (!message || disabled) {
      return;
    }

    setValue("");
    onSend(message);
  }

  function handleKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>,
  ) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <form className="composer" onSubmit={submit}>
      <textarea
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Pergunte sobre medicamentos ou filiais..."
        rows={1}
        disabled={disabled}
      />

      <button
        type="submit"
        disabled={disabled || !value.trim()}
        aria-label="Enviar mensagem"
      >
        {disabled ? (
          <LoaderCircle className="spin" size={20} />
        ) : (
          <ArrowUp size={20} />
        )}
      </button>
    </form>
  );
}
