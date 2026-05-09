/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_COPILOTKIT_URL?: string;
  readonly VITE_AGENT_NAME?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
