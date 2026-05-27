import { Link } from "react-router-dom";

export function Home() {
  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <section className="rounded-md border border-zinc-200 bg-white p-6">
        <p className="text-sm font-medium text-zinc-500">Client</p>
        <h1 className="mt-2 text-3xl font-semibold">Acme Corp</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-600">
          Ingest activity data from SAP, utility bills, and travel exports, then review flagged records before approval.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/upload" className="inline-flex rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700">
            Go to Upload
          </Link>
          <Link to="/review" className="inline-flex rounded-md bg-white px-4 py-2 text-sm font-medium text-zinc-800 ring-1 ring-inset ring-zinc-300 hover:bg-zinc-50">
            Go to Review
          </Link>
        </div>
      </section>
      <aside className="rounded-md border border-zinc-200 bg-white p-5">
        <h2 className="text-sm font-semibold">Prototype Client</h2>
        <dl className="mt-4 space-y-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-zinc-500">Slug</dt>
            <dd className="font-medium">acme-corp</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-zinc-500">API</dt>
            <dd className="font-medium">Django REST</dd>
          </div>
        </dl>
      </aside>
    </div>
  );
}
