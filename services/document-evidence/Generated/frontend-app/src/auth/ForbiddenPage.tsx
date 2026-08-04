import { Message } from "primereact/message";

export function ForbiddenPage() {
  return (
    <main className="appforge-message-page">
      <section className="appforge-message-card">
        <h1>Access denied</h1>

        <Message
          severity="warn"
          text="Your account does not have permission to use this operation or page."
        />

        <p>Choose another section or sign out.</p>
      </section>
    </main>
  );
}
