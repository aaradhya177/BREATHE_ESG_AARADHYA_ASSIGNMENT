import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchBatches, fetchRecords, reviewRecord } from "../api.js";
import { Button, EmptyState, ScopeBadge, StatusBadge, formatDate, formatNumber } from "../components.jsx";

const filters = [
  { label: "All", value: "" },
  { label: "Pending", value: "PENDING_REVIEW" },
  { label: "Flagged", value: "FLAGGED" },
  { label: "Approved", value: "APPROVED" },
  { label: "Rejected", value: "REJECTED" },
];

export function Review() {
  const [selectedBatchId, setSelectedBatchId] = useState(null);
  const [statusFilter, setStatusFilter] = useState("");
  const queryClient = useQueryClient();

  const batchesQuery = useQuery({ queryKey: ["batches"], queryFn: fetchBatches });
  const batches = batchesQuery.data ?? [];

  useEffect(() => {
    if (!selectedBatchId && batches.length > 0) {
      setSelectedBatchId(batches[0].id);
    }
  }, [batches, selectedBatchId]);

  const recordsQuery = useQuery({
    queryKey: ["records", selectedBatchId, statusFilter],
    queryFn: () => fetchRecords({ batchId: selectedBatchId, status: statusFilter }),
    enabled: Boolean(selectedBatchId),
  });
  const allRecordsQuery = useQuery({
    queryKey: ["records", selectedBatchId, "summary"],
    queryFn: () => fetchRecords({ batchId: selectedBatchId }),
    enabled: Boolean(selectedBatchId),
  });

  const records = recordsQuery.data?.results ?? [];
  const allRecords = allRecordsQuery.data?.results ?? [];
  const summary = useMemo(() => {
    return allRecords.reduce(
      (acc, record) => {
        if (record.status === "PENDING_REVIEW") acc.pending += 1;
        if (record.status === "FLAGGED") acc.flagged += 1;
        if (record.status === "APPROVED") acc.approved += 1;
        return acc;
      },
      { pending: 0, flagged: 0, approved: 0 },
    );
  }, [allRecords]);

  const reviewMutation = useMutation({
    mutationFn: ({ recordId, payload }) => reviewRecord(recordId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["records"] });
      queryClient.invalidateQueries({ queryKey: ["audit-log"] });
    },
  });

  function runAction(record, action) {
    const payload = { action, reviewer: "Analyst" };
    if (action === "FLAG") {
      payload.flag_reason = window.prompt("Flag reason", record.flag_reason || "needs_review") || "needs_review";
    }
    reviewMutation.mutate({ recordId: record.id, payload });
  }

  function bulkApprove() {
    allRecords
      .filter((record) => record.status === "PENDING_REVIEW")
      .forEach((record) => {
        reviewMutation.mutate({
          recordId: record.id,
          payload: { action: "APPROVE", reviewer: "Analyst" },
        });
      });
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[300px_1fr]">
      <aside className="rounded-md border border-zinc-200 bg-white">
        <div className="border-b border-zinc-200 p-4">
          <h1 className="text-lg font-semibold">Recent Batches</h1>
        </div>
        <div className="max-h-[calc(100vh-180px)] overflow-auto p-2">
          {batches.length === 0 ? (
            <div className="p-4 text-sm text-zinc-500">No batches yet.</div>
          ) : (
            batches.map((batch) => (
              <button
                key={batch.id}
                className={`mb-2 w-full rounded-md border p-3 text-left text-sm ${selectedBatchId === batch.id ? "border-zinc-900 bg-zinc-50" : "border-zinc-200 bg-white hover:bg-zinc-50"}`}
                onClick={() => setSelectedBatchId(batch.id)}
                type="button"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="font-medium">Batch #{batch.id}</span>
                  <StatusBadge value={batch.status} />
                </div>
                <div className="mt-2 text-xs text-zinc-500">{batch.source_type}</div>
                <div className="mt-1 text-xs text-zinc-500">{formatDate(batch.uploaded_at)}</div>
              </button>
            ))
          )}
        </div>
      </aside>

      <section className="space-y-4">
        <div className="rounded-md border border-zinc-200 bg-white p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Emission Records</h2>
              <p className="mt-1 text-sm text-zinc-600">
                {summary.pending} pending, {summary.flagged} flagged, {summary.approved} approved
              </p>
            </div>
            <Button disabled={!summary.pending || reviewMutation.isPending} onClick={bulkApprove}>
              Bulk approve pending
            </Button>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {filters.map((filter) => (
              <button
                key={filter.label}
                className={`rounded-md px-3 py-2 text-sm font-medium ${statusFilter === filter.value ? "bg-zinc-900 text-white" : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"}`}
                onClick={() => setStatusFilter(filter.value)}
                type="button"
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-hidden rounded-md border border-zinc-200 bg-white">
          {records.length === 0 ? (
            <div className="p-4">
              <EmptyState>{recordsQuery.isLoading ? "Loading records..." : "No records match this filter."}</EmptyState>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-zinc-200 text-sm">
                <thead className="bg-zinc-50 text-left text-xs font-semibold uppercase text-zinc-500">
                  <tr>
                    <th className="px-3 py-3">Date</th>
                    <th className="px-3 py-3">Source</th>
                    <th className="px-3 py-3">Scope</th>
                    <th className="px-3 py-3">Activity</th>
                    <th className="px-3 py-3">Value</th>
                    <th className="px-3 py-3">CO2e kg</th>
                    <th className="px-3 py-3">Status</th>
                    <th className="px-3 py-3">Flag reason</th>
                    <th className="px-3 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100">
                  {records.map((record) => (
                    <tr key={record.id} className="align-top hover:bg-zinc-50">
                      <td className="whitespace-nowrap px-3 py-3">{formatDate(record.activity_date)}</td>
                      <td className="px-3 py-3">
                        <Link className="font-medium text-zinc-900 underline-offset-2 hover:underline" to={`/record/${record.id}`}>
                          {record.source_type}
                        </Link>
                        <div className="mt-1 text-xs text-zinc-500">{record.source_row_id}</div>
                      </td>
                      <td className="px-3 py-3"><ScopeBadge value={record.scope} /></td>
                      <td className="px-3 py-3">{record.activity_type}</td>
                      <td className="whitespace-nowrap px-3 py-3">{formatNumber(record.raw_value)} {record.raw_unit}</td>
                      <td className="whitespace-nowrap px-3 py-3">{formatNumber(record.co2e_kg)}</td>
                      <td className="px-3 py-3"><StatusBadge value={record.status} /></td>
                      <td className="max-w-xs px-3 py-3 text-zinc-600">{record.flag_reason || "-"}</td>
                      <td className="px-3 py-3">
                        {record.status === "PENDING_REVIEW" ? (
                          <div className="flex gap-2">
                            <Button className="h-8 w-8 px-0" title="Approve" variant="approve" onClick={() => runAction(record, "APPROVE")}>✓</Button>
                            <Button className="h-8 w-8 px-0" title="Reject" variant="reject" onClick={() => runAction(record, "REJECT")}>✗</Button>
                            <Button className="h-8 w-8 px-0" title="Flag" variant="flag" onClick={() => runAction(record, "FLAG")}>⚑</Button>
                          </div>
                        ) : (
                          <span className="text-xs text-zinc-400">Done</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
