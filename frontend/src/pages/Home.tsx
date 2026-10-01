import { useQuery } from "@tanstack/react-query";

import api from "../lib/api";
import styles from "./Home.module.scss";

interface HealthResponse {
  status: string;
}

async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health/");
  return data;
}

export default function Home() {
  const { data, isLoading, isError, error } = useQuery<HealthResponse, Error>({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  return (
    <main className={styles.main}>
      <h1 className={styles.title}>ZeroBite</h1>

      {isLoading && <p className={styles.status}>Checking backend…</p>}

      {isError && (
        <p className={styles.status} role="alert">
          Backend: <span className={styles.error}>unreachable</span>
          <br />
          <span className={styles.hint}>{error?.message ?? "Unknown error"}</span>
        </p>
      )}

      {!isLoading && !isError && data && (
        <p className={styles.status}>
          Backend:{" "}
          <span className={data.status === "ok" ? styles.ok : styles.error}>
            {data.status}
          </span>
        </p>
      )}
    </main>
  );
}
