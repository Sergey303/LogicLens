import { useState, type FormEvent } from "react";
import { Button } from "primereact/button";
import { InputText } from "primereact/inputtext";
import { Message } from "primereact/message";
import { Password } from "primereact/password";
import { useAuth } from "./AuthProvider";

export function LoginPage() {
  const auth = useAuth();
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const canSubmit = login.trim().length > 0 && password.length > 0;

  async function submit(event: FormEvent) {
    event.preventDefault();

    if (!canSubmit) {
      return;
    }

    setError(null);

    try {
      await auth.login(login.trim(), password);
    }
    catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Sign in failed.",
      );
    }
  }

  return (
    <main className="appforge-login-page">
      <form
        className="appforge-login-card"
        onSubmit={(event) => void submit(event)}
      >
        <header>
          <h1>AppForge Admin</h1>
          <p>Sign in with the account configured for this deployment.</p>
        </header>

        <label htmlFor="appforge-login">
          Email or login
        </label>

        <InputText
          id="appforge-login"
          autoComplete="username"
          value={login}
          onChange={(event) => setLogin(event.target.value)}
        />

        <label htmlFor="appforge-password">
          Password
        </label>

        <Password
          inputId="appforge-password"
          autoComplete="current-password"
          feedback={false}
          toggleMask
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />

        {error ? (
          <Message severity="error" text={error} />
        ) : null}

        <Button
          type="submit"
          label="Sign in"
          loading={auth.loading}
          disabled={!canSubmit}
        />
      </form>
    </main>
  );
}
