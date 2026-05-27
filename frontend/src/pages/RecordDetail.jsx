import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAuditLog, fetchRecord, reviewRecord } from "../api.js";
import { Button, EmptyState, ScopeBadge, StatusBadge, formatDate } from "../components.jsx";

function actionForStatus(status) {
  if (status === "APPROVED") return "APPROVE";
  if (status === "REJECTED") return "REJECT";
  return "FLAG";
}

export function RecordDetail() {
  const { id } = useParams();
  const [notes, setNotes] = useState("");
  const queryClient = useQueryClient();
  const recordQuery = useQuery({
    queryKey: ["record", id],
    queryFn: () => fetchRecord(id),
  });
  const auditQuery = useQuery({
    queryKey: ["audit-log", id],
    queryFn: () => fetchAuditLog(id),
  });
  const mutation = useMutation({
    mutationFn: (payload) => reviewRecord(id, payload),
    onSuccess: (record) => {
      setNotes(record.edit_notes ?? "");
      queryClient.invalidateQueries({ queryKey: ["record", id] });
      queryClient.invalidateQueries({ queryKey: ["records"] });
      queryClient.invalidateQueries({ queryKey: ["audit-log", id] });
    },
  });

  const record = recordQuery.data;

  useEffect(() => {
    if (record) {
      setNotes(record.edit_notes ?? "");
    }
  }, [record]);

  if (recordQuery.isLoading) return <EmptyState>Loading record...</EmptyState>;
  if (recordQuery.isError) return <EmptyState>Record not found.</EmptyState>;

  function saveNotes() {
    mutation.mutate({
      action: actionForStatus(record.status),
      reviewer: "Analyst",
      flag_reason: record.flag_reason,
      edit_notes: notes,
    });
  }

  return (
    <div className="space-y-5">
      <Link className="text-sm font-medium text-zinc-600 hover:text-zinc-950" to="/review">
        {"<-"} Back to review
      </Link>

      <section className="rounded-md border border-zinc-200 bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold">{record.activity_type}</h1>
            <p className="mt-1 text-sm text-zinc-500">{record.source_row_id}</p>
          </div>
          <div className="flex gap-2">
            <ScopeBadge value={record.scope} />
            <StatusBadge value={record.status} />
          </div>
        </div>
        <dl className="mt-5 grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <Info label="Date" value={formatDate(record.activity_date)} />
          <Info label="Value" value={`${record.raw_value} ${record.raw_unit}`} />
          <Info label="CO2e kg" value={record.co2e_kg ?? "-"} />
          <Info label="Reviewed by" value={record.reviewed_by || "-"} />
        </dl>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1fr_340px]">
        <div className="rounded-md border border-zinc-200 bg-white p-5">
          <h2 className="text-base font-semibold">Raw Payload</h2>
          <pre className="mt-4 max-h-[520px] overflow-auto rounded-md bg-zinc-950 p-4 text-xs leading-5 text-zinc-50">
            {JSON.stringify(record.raw_payload, null, 2)}
          </pre>
        </div>
        <aside className="rounded-md border border-zinc-200 bg-white p-5">
          <h2 className="text-base font-semibold">Edit Notes</h2>
          <textarea
            className="mt-4 min-h-40 w-full rounded-md border border-zinc-300 px-3 py-2 text-sm"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
          />
          <Button className="mt-3 w-full" disabled={mutation.isPending} onClick={saveNotes}>
            Save notes
          </Button>
        </aside>
      </section>

      <section className="rounded-md border border-zinc-200 bg-white p-5">
        <h2 className="text-base font-semibold">Audit Log</h2>
        <div className="mt-4 space-y-3">
          {(auditQuery.data ?? []).length === 0 ? (
            <p className="text-sm text-zinc-500">No audit events yet.</p>
          ) : (
            auditQuery.data.map((entry) => (
              <div key={entry.id} className="border-l-2 border-zinc-300 pl-4 text-sm">
                <div className="font-medium">{entry.action} by {entry.actor}</div>
                <div className="mt-1 text-zinc-500">{new Date(entry.timestamp).toLocaleString()}</div>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}

function Info({ label, value }) {
  return (
    <div>
      <dt className="text-zinc-500">{label}</dt>
      <dd className="mt-1 font-medium">{value}</dd>
    </div>
  );
}
