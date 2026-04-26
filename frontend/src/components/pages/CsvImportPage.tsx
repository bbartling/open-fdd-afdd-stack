import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { UploadCloud } from "lucide-react";

import { ApiError } from "@/lib/api";
import { getDriverProfileStatus, uploadCsvFile } from "@/lib/crud-api";

export function CsvImportPage() {
  const { data: profile } = useQuery({
    queryKey: ["driver-profile"],
    queryFn: getDriverProfileStatus,
  });

  const [siteId, setSiteId] = useState("csv-upload");
  const [createPoints, setCreatePoints] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<unknown>(null);
  const [errorText, setErrorText] = useState("");

  const csvEnabled = profile?.drivers?.csv ?? false;
  const statusText = useMemo(() => {
    if (!profile) return "Checking driver profile...";
    return csvEnabled
      ? "CSV scraper is enabled in bootstrap profile."
      : "CSV scraper is disabled in bootstrap profile. Upload API still works when API is running.";
  }, [profile, csvEnabled]);

  const onDropFile = (f: File | null) => {
    setFile(f);
    setResult(null);
    setErrorText("");
  };

  const onSubmit = async () => {
    if (!file) return;
    setBusy(true);
    setResult(null);
    setErrorText("");
    try {
      const body = new FormData();
      body.append("file", file);
      body.append("site_id", siteId);
      body.append("create_points", String(createPoints));
      body.append("source_name", file.name.replace(/\.csv$/i, ""));
      const resp = await uploadCsvFile(body);
      setResult(resp);
    } catch (e) {
      if (e instanceof ApiError && e.payload && typeof e.payload === "object") {
        const payload = e.payload as { error?: { message?: string; details?: unknown } };
        setErrorText(payload.error?.message ?? e.message);
        setResult(payload.error?.details ?? e.payload);
      } else {
        setErrorText(e instanceof Error ? e.message : "Upload failed");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">CSV Import</h1>
      <p className="text-sm text-muted-foreground">
        Upload CSV with drag-and-drop. Backend validates timestamp and metric columns and returns structured errors when data is malformed.
      </p>

      <div className="rounded-xl border border-border/60 bg-card p-4">
        <p className="text-sm font-medium text-foreground">Driver profile status</p>
        <p className="mt-1 text-sm text-muted-foreground">{statusText}</p>
      </div>

      <div className="rounded-xl border border-border/60 bg-card p-4 space-y-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Site ID</label>
          <input
            value={siteId}
            onChange={(e) => setSiteId(e.target.value)}
            className="h-9 w-full rounded-lg border border-border/60 bg-background px-3 text-sm"
            placeholder="csv-upload"
          />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={createPoints}
            onChange={(e) => setCreatePoints(e.target.checked)}
          />
          Auto-create missing points
        </label>

        <div
          className="rounded-xl border-2 border-dashed border-border p-8 text-center"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            onDropFile(e.dataTransfer.files?.[0] ?? null);
          }}
        >
          <UploadCloud className="mx-auto h-8 w-8 text-muted-foreground" />
          <p className="mt-2 text-sm text-muted-foreground">Drag and drop a CSV file here</p>
          <p className="mt-1 text-xs text-muted-foreground">or</p>
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => onDropFile(e.target.files?.[0] ?? null)}
            className="mt-2 text-sm"
          />
          {file ? <p className="mt-2 text-sm font-medium">{file.name}</p> : null}
        </div>

        <button
          type="button"
          disabled={!file || busy || !siteId.trim()}
          onClick={onSubmit}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-60"
        >
          {busy ? "Uploading..." : "Validate + Import CSV"}
        </button>
      </div>

      {errorText ? (
        <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
          {errorText}
        </div>
      ) : null}

      {result ? (
        <pre className="max-h-[360px] overflow-auto rounded-xl border border-border/60 bg-muted/40 p-3 text-xs">
          {JSON.stringify(result, null, 2)}
        </pre>
      ) : null}
    </div>
  );
}
