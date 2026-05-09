import ReactMarkdown from "react-markdown";
import type { MarkdownSpec } from "./types";

export function MarkdownRenderer({ spec }: { spec: MarkdownSpec }) {
  return (
    <div className="a2ui-card">
      <ReactMarkdown>{spec.content}</ReactMarkdown>
    </div>
  );
}
