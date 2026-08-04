import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Generated admin page failed.", error, info);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return <main className="appforge-message-page"><h1>Page failed</h1><p>{this.state.error.message}</p></main>;
  }
}
