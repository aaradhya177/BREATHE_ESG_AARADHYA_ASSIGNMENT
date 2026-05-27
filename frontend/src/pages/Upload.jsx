import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadIngestion } from "../api.js";
import { Button, StatusBadge } from "../components.jsx";

const uploadTypes = [
  { key: "sap", label: "SAP Fuel", accept: ".csv", hint: "CSV" },
  { key: "utility", label: "Utility Electricity", accept: ".csv", hint: "CSV" },
  { key: "travel", label: "Corporate Travel", accept: ".json", hint: "JSON" },
];

export function Upload() {
  const [active, setActive] = useState("sap");
  const [files, setFiles] = useState({});
  const [uploadedBy, setUploadedBy] = useState("analyst");
  const [lastBatch, setLastBatch] = useState(null);
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: ({ kind, file }) => uploadIngestion(kind, file, uploadedBy),
    onSuccess: (data) => {
      setLastBatch(data);
      queryClient.invalidateQueries({ queryKey: ["batches"] });
    },
  });
  const current = uploadTypes.find((item) => item.key === active);

  function submit(event) {
    event.preventDefault();
    if (!files[active]) return;
    mutation.mutate({ kind: active, file: files[active] });
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Upload Data</h1>
        <p className="mt-1 text-sm text-zinc-600">Choose a source type and upload the export file for Acme Corp.</p>
      </div>

      <div className="rounded-md border border-zinc-200 bg-white">
        <div className="flex flex-wrap border-b border-zinc-200">
          {uploadTypes.map((item) => (
            <button
              key={item.key}
              className={`px-4 py-3 text-sm font-medium ${active === item.key ? "border-b-2 border-zinc-900 text-zinc-950" : "text-zinc-500 hover:text-zinc-950"}`}
              onClick={() => setActive(item.key)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </div>

        <form className="grid gap-5 p-5 md:grid-cols-[1fr_220px]" onSubmit={submit}>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-zinc-700">{current.label} file</label>
              <input
                className="mt-2 block w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm file:mr-4 file:rounded-md file:border-0 file:bg-zinc-100 file:px-3 file:py-2 file:text-sm file:font-medium hover:file:bg-zinc-200"
                type="file"
                accept={current.accept}
                onChange={(event) => setFiles((value) => ({ ...value, [active]: event.target.files?.[0] }))}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-zinc-700">Uploaded by</label>
              <input
                className="mt-2 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
                value={uploadedBy}
                onChange={(event) => setUploadedBy(event.target.value)}
              />
            </div>
          </div>
          <div className="flex flex-col justify-end gap-3">
            <Button disabled={!files[active] || mutation.isPending} type="submit">
              {mutation.isPending ? "Uploading" : `Submit ${current.hint}`}
            </Button>
            {mutation.isError ? <p className="text-sm text-red-600">{mutation.error?.response?.data?.detail ?? "Upload failed"}</p> : null}
          </div>
        </form>
      </div>

      {lastBatch ? (
        <section className="rounded-md border border-zinc-200 bg-white p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-base font-semibold">Last Batch</h2>
            <StatusBadge value={lastBatch.status} />
          </div>
          <p className="mt-4 text-lg font-medium">
            {lastBatch.row_count} rows ingested, {lastBatch.flagged_count} flagged, {lastBatch.error_count} errors
          </p>
          <p className="mt-1 text-sm text-zinc-500">Batch #{lastBatch.batch_id}</p>
        </section>
      ) : null}
    </div>
  );
}
