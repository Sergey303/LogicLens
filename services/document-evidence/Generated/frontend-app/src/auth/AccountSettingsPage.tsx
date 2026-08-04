import { useEffect, useState, type FormEvent } from "react";
import { Button } from "primereact/button";
import { Message } from "primereact/message";
import { Password } from "primereact/password";
import { getHttpClient } from "../generated-ts/runtime/httpClient";
import {
  changePasswordAuth,
  clearAuthSession,
} from "./authApi";
import { useAuth } from "./AuthProvider";

interface EmployeeVacationDto {
  id: string;
  startDate: string;
  endDate: string;
  calendarDays: number;
  workingDays: number;
  nonWorkingDays: number;
  holidayDays: number;
  shortenedWorkingDays: number;
}

interface ProductionCalendarSummaryDto {
  startDate: string;
  endDate: string;
  calendarDays: number;
  workingDays: number;
  nonWorkingDays: number;
  holidayDays: number;
  shortenedWorkingDays: number;
}

export function AccountSettingsPage({
  forceChangePassword = false,
}: {
  forceChangePassword?: boolean;
}) {
  const auth = useAuth();
  const user = auth.session?.user;

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [repeatPassword, setRepeatPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user) {
    return null;
  }

  const canSubmit =
    currentPassword.length > 0 &&
    newPassword.length >= 8 &&
    newPassword === repeatPassword;

  async function submit(event: FormEvent) {
    event.preventDefault();

    if (!canSubmit) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await changePasswordAuth(
        currentPassword,
        newPassword,
      );

      clearAuthSession();
    }
    catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Password was not changed.",
      );
    }
    finally {
      setLoading(false);
    }
  }

  return (
    <section className="appforge-account-page">
      <header>
        <h1>Account</h1>
        <p>Current account and password settings.</p>
      </header>

      {forceChangePassword ? (
        <Message
          severity="warn"
          text="You must change the temporary password before using the application."
        />
      ) : null}

      <div className="appforge-account-grid">
        <article className="appforge-account-card">
          <h2>Profile</h2>

          <dl className="appforge-profile-fields">
            <div>
              <dt>Email</dt>
              <dd>{user.email}</dd>
            </div>

            <div>
              <dt>User name</dt>
              <dd>{user.userName}</dd>
            </div>

            <div>
              <dt>Email confirmed</dt>
              <dd>{user.emailConfirmed ? "Yes" : "No"}</dd>
            </div>

            <div>
              <dt>Must change password</dt>
              <dd>{user.mustChangePassword ? "Yes" : "No"}</dd>
            </div>
          </dl>

          <h3>Roles</h3>
          <PillList values={user.roles} empty="No roles" />

          <h3>Permissions</h3>
          <PillList values={user.permissions} empty="No permissions" />
        </article>

        <form
          className="appforge-account-card"
          onSubmit={(event) => void submit(event)}
        >
          <h2>Change password</h2>

          <label htmlFor="appforge-current-password">
            Current password
          </label>

          <Password
            inputId="appforge-current-password"
            autoComplete="current-password"
            feedback={false}
            toggleMask
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
          />

          <label htmlFor="appforge-new-password">
            New password
          </label>

          <Password
            inputId="appforge-new-password"
            autoComplete="new-password"
            feedback={false}
            toggleMask
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
          />

          <label htmlFor="appforge-repeat-password">
            Repeat new password
          </label>

          <Password
            inputId="appforge-repeat-password"
            autoComplete="new-password"
            feedback={false}
            toggleMask
            value={repeatPassword}
            onChange={(event) => setRepeatPassword(event.target.value)}
          />

          {error ? (
            <Message severity="error" text={error} />
          ) : null}

          <Button
            type="submit"
            label="Change password"
            loading={loading}
            disabled={!canSubmit}
          />
        </form>
      </div>

      {!forceChangePassword ? <EmployeeVacationSection /> : null}
    </section>
  );
}

function EmployeeVacationSection() {
  const [supported, setSupported] = useState<boolean | null>(null);
  const [vacations, setVacations] = useState<EmployeeVacationDto[]>([]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [summary, setSummary] = useState<ProductionCalendarSummaryDto | null>(null);
  const [loadingCalendar, setLoadingCalendar] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadVacations();
  }, []);

  useEffect(() => {
    if (supported !== true || !isDateRangeReady(startDate, endDate)) {
      setSummary(null);
      setLoadingCalendar(false);
      return;
    }

    let cancelled = false;
    setLoadingCalendar(true);
    setError(null);

    void accountApi<ProductionCalendarSummaryDto>(
      "/api/account/vacations/calendar" +
        `?startDate=${encodeURIComponent(startDate)}` +
        `&endDate=${encodeURIComponent(endDate)}`,
    )
      .then((result) => {
        if (!cancelled) {
          setSummary(result);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setSummary(null);
          setError(readAccountError(caught, "Production calendar was not loaded."));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingCalendar(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [supported, startDate, endDate]);

  async function loadVacations() {
    try {
      const items = await accountApi<EmployeeVacationDto[]>("/api/account/vacations");
      setSupported(true);
      setVacations(items);
    }
    catch (caught) {
      if (caught instanceof AccountApiError && caught.status === 404) {
        setSupported(false);
        return;
      }

      setSupported(true);
      setError(readAccountError(caught, "Vacations were not loaded."));
    }
  }

  async function createVacation(event: FormEvent) {
    event.preventDefault();
    if (!isDateRangeReady(startDate, endDate) || saving) {
      return;
    }

    setSaving(true);
    setError(null);

    try {
      await accountApi<EmployeeVacationDto>(
        "/api/account/vacations",
        {
          method: "POST",
          body: {
            startDate,
            endDate,
          },
        },
      );
      setStartDate("");
      setEndDate("");
      setSummary(null);
      await loadVacations();
    }
    catch (caught) {
      setError(readAccountError(caught, "Vacation was not created."));
    }
    finally {
      setSaving(false);
    }
  }

  if (supported !== true) {
    return null;
  }

  return (
    <article className="appforge-account-card">
      <header>
        <h2>My vacations</h2>
        <p className="appforge-muted">
          Select the first and last vacation dates. Production calendar data is calculated by the server.
        </p>
      </header>

      <form className="appforge-generated-form" onSubmit={(event) => void createVacation(event)}>
        <label htmlFor="appforge-vacation-start">Start date</label>
        <input
          id="appforge-vacation-start"
          type="date"
          value={startDate}
          onChange={(event) => setStartDate(event.target.value)}
        />

        <label htmlFor="appforge-vacation-end">End date</label>
        <input
          id="appforge-vacation-end"
          type="date"
          value={endDate}
          min={startDate || undefined}
          onChange={(event) => setEndDate(event.target.value)}
        />

        {loadingCalendar ? <p className="appforge-muted">Loading production calendar...</p> : null}

        {summary ? (
          <dl className="appforge-profile-fields">
            <div><dt>Calendar days</dt><dd>{summary.calendarDays}</dd></div>
            <div><dt>Working days</dt><dd>{summary.workingDays}</dd></div>
            <div><dt>Non-working days</dt><dd>{summary.nonWorkingDays}</dd></div>
            <div><dt>Official holidays</dt><dd>{summary.holidayDays}</dd></div>
            <div><dt>Shortened working days</dt><dd>{summary.shortenedWorkingDays}</dd></div>
          </dl>
        ) : null}

        {error ? <Message severity="error" text={error} /> : null}

        <Button
          type="submit"
          label="Create vacation"
          loading={saving}
          disabled={!isDateRangeReady(startDate, endDate) || loadingCalendar}
        />
      </form>

      <h3>Created vacations</h3>

      {vacations.length === 0 ? (
        <p className="appforge-muted">No vacations created yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Start</th>
              <th>End</th>
              <th>Calendar days</th>
              <th>Working</th>
              <th>Non-working</th>
            </tr>
          </thead>
          <tbody>
            {vacations.map((vacation) => (
              <tr key={vacation.id}>
                <td>{vacation.startDate}</td>
                <td>{vacation.endDate}</td>
                <td>{vacation.calendarDays}</td>
                <td>{vacation.workingDays}</td>
                <td>{vacation.nonWorkingDays}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </article>
  );
}

function isDateRangeReady(startDate: string, endDate: string): boolean {
  return startDate.length > 0 && endDate.length > 0 && endDate >= startDate;
}

class AccountApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function accountApi<T>(
  path: string,
  options: {
    method?: "GET" | "POST";
    body?: unknown;
  } = {},
): Promise<T> {
  try {
    const result = await getHttpClient().call<T, "json">({
      method: options.method ?? "GET",
      url: path,
      headers: options.body === undefined
        ? undefined
        : {
            "Content-Type": "application/json",
          },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      responseMode: "json",
    });
    return result.data;
  }
  catch (caught) {
    const status = readHttpStatus(caught);
    if (status !== null) {
      throw new AccountApiError(
        status,
        caught instanceof Error ? caught.message : `HTTP ${status}`,
      );
    }
    throw caught;
  }
}

function readHttpStatus(caught: unknown): number | null {
  if (!(caught instanceof Error)) {
    return null;
  }
  const match = /^HTTP (\d{3})(?:\s|$)/.exec(caught.message);
  return match ? Number(match[1]) : null;
}

function readAccountError(caught: unknown, fallback: string): string {
  return caught instanceof Error ? caught.message : fallback;
}

function PillList({
  values,
  empty,
}: {
  values: string[];
  empty: string;
}) {
  if (values.length === 0) {
    return <p className="appforge-muted">{empty}</p>;
  }

  return (
    <ul className="appforge-pill-list">
      {values.map((value) => (
        <li className="appforge-pill" key={value}>
          {value}
        </li>
      ))}
    </ul>
  );
}
