import { useCallback, useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  fetchFortune100Companies,
  fetchJobs,
  fetchStats,
  triggerCareersScrape,
  triggerScrape,
} from './api'
import type { Fortune100Company, Job, Stats } from './types'

const FORTUNE100_ALL = '__all__'

const SOURCE_LABELS: Record<string, string> = {
  linkedin: 'LinkedIn',
  remotive: 'Remotive',
  remoteok: 'RemoteOK',
  arbeitnow: 'Arbeitnow',
  jobicy: 'Jobicy',
  weworkremotely: 'We Work Remotely',
  weworkremotely_dev: 'WWR Dev',
  himalayas: 'Himalayas',
  jobicy_rss: 'Jobicy RSS',
  careers: 'Fortune 100 Careers',
}

function formatSource(source: string) {
  return SOURCE_LABELS[source] ?? source
}

function formatDate(iso: string | null) {
  if (!iso) return 'Never'
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-panel)] p-5 shadow-sm">
      <p className="text-sm font-medium text-[var(--color-ink-muted)]">{label}</p>
      <p className="mt-2 font-display text-4xl text-[var(--color-ink)]" style={{ fontFamily: 'var(--font-display)' }}>
        {value}
      </p>
      {sub && <p className="mt-1 text-xs text-[var(--color-ink-muted)]">{sub}</p>}
    </div>
  )
}

function JobRow({ job }: { job: Job }) {
  const skills = job.skills ? job.skills.split(', ').slice(0, 4) : []
  return (
    <a
      href={job.url}
      target="_blank"
      rel="noreferrer"
      className="group block rounded-xl border border-[var(--color-border)] bg-[var(--color-panel)] p-4 transition hover:border-[var(--color-accent)] hover:shadow-md"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-[var(--color-ink)] group-hover:text-[var(--color-accent)]">
            {job.title}
          </h3>
          <p className="mt-1 text-sm text-[var(--color-ink-muted)]">
            {job.company} · {job.location || 'Location n/a'}
          </p>
        </div>
        <span className="rounded-full bg-[var(--color-accent-light)] px-3 py-1 text-xs font-medium text-[var(--color-accent)]">
          {formatSource(job.source)}
        </span>
      </div>
      {skills.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {skills.map((s) => (
            <span key={s} className="rounded-md bg-[var(--color-surface)] px-2 py-0.5 text-xs text-[var(--color-ink-muted)]">
              {s}
            </span>
          ))}
        </div>
      )}
      {job.search_label && (
        <p className="mt-2 text-xs text-[var(--color-ink-muted)]">Track: {job.search_label}</p>
      )}
    </a>
  )
}

export default function App() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [totalJobs, setTotalJobs] = useState(0)
  const [query, setQuery] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [fortune100Filter, setFortune100Filter] = useState('')
  const [fortune100Companies, setFortune100Companies] = useState<Fortune100Company[]>([])
  const [loading, setLoading] = useState(true)
  const [scraping, setScraping] = useState(false)
  const [scrapeMsg, setScrapeMsg] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const jobParams: Parameters<typeof fetchJobs>[0] = {
        q: query || undefined,
        source: sourceFilter || undefined,
        limit: 30,
      }
      if (fortune100Filter === FORTUNE100_ALL) {
        jobParams.fortune100 = true
      } else if (fortune100Filter) {
        jobParams.fortune100_company = fortune100Filter
      }
      const [statsData, jobsData, companiesData] = await Promise.all([
        fetchStats(),
        fetchJobs(jobParams),
        fetchFortune100Companies(),
      ])
      setStats(statsData)
      setJobs(jobsData.jobs)
      setTotalJobs(jobsData.total)
      setFortune100Companies(companiesData)
    } catch (err) {
      console.error(err)
      setScrapeMsg('Could not reach API. Start backend on port 8000.')
    } finally {
      setLoading(false)
    }
  }, [query, sourceFilter, fortune100Filter])

  useEffect(() => {
    load()
  }, [load])

  async function handleScrape(careersOnly = false) {
    setScraping(true)
    setScrapeMsg(
      careersOnly
        ? 'Syncing Fortune 100 career pages (~1 min)…'
        : 'Collecting jobs from 9 sources (Fortune 100 runs first)… this may take several minutes.',
    )
    try {
      const result = careersOnly ? await triggerCareersScrape() : await triggerScrape()
      setScrapeMsg(
        `Done — ${result.jobs_added} new, ${result.jobs_updated} updated in ${result.duration_seconds.toFixed(0)}s` +
          (result.errors.length ? ` (${result.errors.length} warnings)` : ''),
      )
      await load()
    } catch {
      setScrapeMsg('Scrape failed. Check backend logs.')
    } finally {
      setScraping(false)
    }
  }

  const chartData =
    stats?.by_source.map((s) => ({
      name: formatSource(s.source),
      count: s.count,
    })) ?? []

  return (
    <div className="min-h-screen">
      <header className="border-b border-[var(--color-border)] bg-[var(--color-panel)]">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-[var(--color-accent)]">
              Tekwissen · Workforce Intelligence
            </p>
            <h1
              className="text-3xl text-[var(--color-ink)] md:text-4xl"
              style={{ fontFamily: 'var(--font-display)' }}
            >
              Job Market Dashboard
            </h1>
            <p className="mt-1 max-w-xl text-sm text-[var(--color-ink-muted)]">
              Live hiring signals from LinkedIn, Remotive, RemoteOK, RSS feeds & more — for staffing and sales outreach.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => handleScrape(false)}
              disabled={scraping}
              className="rounded-xl bg-[var(--color-accent)] px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-60"
            >
              {scraping ? 'Syncing…' : 'Sync All Sources'}
            </button>
            <button
              type="button"
              onClick={() => handleScrape(true)}
              disabled={scraping}
              className="rounded-xl border border-[var(--color-accent)] bg-[var(--color-panel)] px-5 py-3 text-sm font-semibold text-[var(--color-accent)] transition hover:bg-[var(--color-accent-light)] disabled:opacity-60"
            >
              Fortune 100 Only
            </button>
          </div>
        </div>
        {scrapeMsg && (
          <div className="border-t border-[var(--color-border)] bg-[var(--color-accent-light)] px-6 py-2 text-sm text-[var(--color-accent)]">
            {scrapeMsg}
          </div>
        )}
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        {loading && !stats ? (
          <p className="text-center text-[var(--color-ink-muted)]">Loading market data…</p>
        ) : (
          <>
            <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="Total listings" value={stats?.total_jobs ?? 0} />
              <StatCard label="Unique companies" value={stats?.total_companies ?? 0} />
              <StatCard label="Data sources" value={stats?.total_sources ?? 0} />
              <StatCard label="Last sync" value={formatDate(stats?.last_scrape ?? null)} sub="All sources" />
            </section>

            <section className="mt-8 grid gap-6 lg:grid-cols-5">
              <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-panel)] p-5 lg:col-span-3">
                <h2 className="text-lg font-semibold">Jobs by source</h2>
                <div className="mt-4 h-64">
                  {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 40 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#eef1f6" />
                        <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-25} textAnchor="end" height={60} />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Bar dataKey="count" fill="#0d7c8c" radius={[6, 6, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="py-16 text-center text-sm text-[var(--color-ink-muted)]">
                      No data yet — click Sync Market Data
                    </p>
                  )}
                </div>
              </div>

              <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-panel)] p-5 lg:col-span-2">
                <h2 className="text-lg font-semibold">Top skills in demand</h2>
                <ul className="mt-4 space-y-2">
                  {(stats?.top_skills ?? []).slice(0, 10).map((s, i) => (
                    <li key={s.skill} className="flex items-center justify-between text-sm">
                      <span className="text-[var(--color-ink-muted)]">
                        {i + 1}. {s.skill}
                      </span>
                      <span className="font-semibold text-[var(--color-ink)]">{s.count}</span>
                    </li>
                  ))}
                  {!stats?.top_skills?.length && (
                    <li className="text-sm text-[var(--color-ink-muted)]">Run a sync to populate</li>
                  )}
                </ul>
              </div>
            </section>

            <section className="mt-8 grid gap-6 lg:grid-cols-2">
              <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-panel)] p-5">
                <h2 className="text-lg font-semibold">Top hiring companies</h2>
                <p className="mt-1 text-xs text-[var(--color-ink-muted)]">Sales lead signals for staffing outreach</p>
                <ul className="mt-4 space-y-3">
                  {(stats?.top_companies ?? []).map((c, i) => (
                    <li key={c.company} className="flex items-center justify-between border-b border-[var(--color-border)] pb-2 last:border-0">
                      <span className="font-medium">
                        {i + 1}. {c.company}
                      </span>
                      <span className="rounded-full bg-[var(--color-surface)] px-2 py-0.5 text-xs font-semibold">
                        {c.count} roles
                      </span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-panel)] p-5">
                <h2 className="text-lg font-semibold">Why this matters for Tekwissen</h2>
                <ul className="mt-4 space-y-3 text-sm text-[var(--color-ink-muted)]">
                  <li>
                    <strong className="text-[var(--color-ink)]">Recruiters</strong> — see which skills and locations are heating up before sourcing candidates.
                  </li>
                  <li>
                    <strong className="text-[var(--color-ink)]">Sales / BD</strong> — companies with many open roles are warm leads for staffing and RPO.
                  </li>
                  <li>
                    <strong className="text-[var(--color-ink)]">Account teams</strong> — rate and demand context for client conversations on SAP, DevOps, Java, ServiceNow.
                  </li>
                </ul>
              </div>
            </section>

            <section className="mt-8">
              <div className="mb-4 flex flex-wrap items-end justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold">Job listings</h2>
                  <p className="text-sm text-[var(--color-ink-muted)]">{totalJobs} total · showing latest 30</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <input
                    type="search"
                    placeholder="Search title, company, skill…"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm outline-none focus:border-[var(--color-accent)]"
                  />
                  <select
                    value={sourceFilter}
                    onChange={(e) => setSourceFilter(e.target.value)}
                    className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm"
                    aria-label="Filter by data source"
                  >
                    <option value="">All sources</option>
                    {stats?.by_source.map((s) => (
                      <option key={s.source} value={s.source}>
                        {formatSource(s.source)}
                      </option>
                    ))}
                  </select>
                  <select
                    value={fortune100Filter}
                    onChange={(e) => setFortune100Filter(e.target.value)}
                    className="max-w-[220px] rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm"
                    aria-label="Filter by Fortune 100 company"
                  >
                    <option value="">All companies</option>
                    <option value={FORTUNE100_ALL}>Fortune 100 (all)</option>
                    {fortune100Companies.map((c) => (
                      <option key={c.slug} value={c.name}>
                        #{c.rank} {c.name}
                        {c.job_count > 0 ? ` (${c.job_count})` : ''}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="space-y-3">
                {jobs.map((job) => (
                  <JobRow key={job.id} job={job} />
                ))}
                {!jobs.length && (
                  <p className="rounded-xl border border-dashed border-[var(--color-border)] py-12 text-center text-sm text-[var(--color-ink-muted)]">
                    {fortune100Filter ? (
                      <>
                        No Fortune 100 career listings yet. Click <strong>Fortune 100 Only</strong> (~1 min)
                        — pulls from Amazon, Microsoft, CVS, Bank of America, and 14 more Workday career APIs.
                      </>
                    ) : (
                      <>
                        No jobs yet. Click <strong>Sync All Sources</strong> to pull live listings.
                      </>
                    )}
                  </p>
                )}
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  )
}
