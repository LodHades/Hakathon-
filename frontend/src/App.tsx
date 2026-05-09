import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { RegisterA2UIActions } from "./components/a2ui/RegisterActions";

const RUNTIME_URL =
  import.meta.env.VITE_COPILOTKIT_URL ?? "http://localhost:8000/copilotkit";
const AGENT_NAME = import.meta.env.VITE_AGENT_NAME ?? "data_supervisor";

export default function App() {
  return (
    <CopilotKit runtimeUrl={RUNTIME_URL} agent={AGENT_NAME}>
      <RegisterA2UIActions />
      <div className="app-shell">
        <header>
          <h1>Data Analyst</h1>
          <span className="subtitle">
            Pregúntame sobre tus datos: SQL · CSV · JSON · PDF
          </span>
        </header>
        <main>
          <CopilotChat
            className="copilot-chat"
            labels={{
              title: "Asistente",
              initial:
                "Hola. Dame un tema o pregunta de datos y construyo el dashboard.",
            }}
          />
        </main>
      </div>
    </CopilotKit>
  );
}
