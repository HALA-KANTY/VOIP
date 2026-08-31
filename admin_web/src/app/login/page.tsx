"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Input, Field } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [erreur, setErreur] = useState<string | null>(null);
  const [chargement, setChargement] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setErreur(null);
    setChargement(true);
    try {
      await login(username, password);
      router.push("/");
    } catch {
      setErreur("Identifiants invalides");
    } finally {
      setChargement(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-page px-4">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm rounded-xl border border-border bg-surface p-8"
      >
        <div className="mb-6 flex flex-col items-center gap-2">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-base font-bold text-white">
            K
          </span>
          <h1 className="text-lg font-semibold">KANTYVOIP</h1>
          <p className="text-sm text-ink-muted">Connexion administrateur</p>
        </div>

        <Field label="Nom d'utilisateur">
          <Input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
        </Field>
        <Field label="Mot de passe">
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </Field>

        {erreur && <p className="mb-3 text-sm text-critical">{erreur}</p>}

        <Button type="submit" className="mt-2 w-full" disabled={chargement}>
          {chargement ? "Connexion..." : "Se connecter"}
        </Button>
      </form>
    </div>
  );
}
