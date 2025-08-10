PharmaSight – Performance Playbook
1) Multi‑tenant data model (simple + safe)
	•	Use one Postgres DB, shared schema with tenant_id uuid not null on every tenant-scoped table.
	•	Enforce Row‑Level Security (RLS) on all tenant tables.
	•	Set current_setting('app.tenant_id') in API middleware after auth; never trust client-sent tenant IDs.
	•	Keys & types:
	•	Primary keys: uuid (v4) or bigint sequences; foreign keys include tenant_id.
	•	Money: numeric(14,2); percentages: numeric(5,4); dates as date.

    RLS snippet
    ALTER TABLE daily_kpis ENABLE ROW LEVEL SECURITY;

    CREATE POLICY tenant_isolation ON daily_kpis
    USING (tenant_id = current_setting('app.tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);

2) Source-of-truth: daily facts
	•	Keep one row per day per tenant in daily_kpis (turnover, gp_value, gp_pct, purchases, basket_value, etc.).
	•	Index for common reads:
        CREATE INDEX kpi_tenant_date ON daily_kpis (tenant_id, kpi_date DESC);

3) Pre-aggregations for instant MTD/YTD
	•	Create rollup tables (or materialized views) for month and year:
	•	monthly_kpis(tenant_id, month_start date, turnover, gp_value, purchases, updated_at)
	•	yearly_kpis(tenant_id, year_start date,  turnover, gp_value, purchases, updated_at)
	•	Recompute only the affected month/year on ingest for that tenant (fast & simple).
	•	Add indexes:
        CREATE INDEX mkpi_tenant_month ON monthly_kpis (tenant_id, month_start);
        CREATE INDEX ykpi_tenant_year  ON yearly_kpis  (tenant_id, year_start);

        Monthly refresh (on ingest)
        -- :tenant_id, :as_of_date (the day you just ingested)
        UPDATE monthly_kpis mk
        SET turnover = s.turnover, gp_value = s.gp_value, purchases = s.purchases, updated_at = now()
        FROM (
        SELECT tenant_id, date_trunc('month', :as_of_date)::date AS month_start,
                SUM(turnover) AS turnover,
                SUM(gp_value) AS gp_value,
                SUM(purchases) AS purchases
        FROM daily_kpis
        WHERE tenant_id = :tenant_id
            AND kpi_date >= date_trunc('month', :as_of_date)
            AND kpi_date <  date_trunc('month', :as_of_date) + INTERVAL '1 month'
        GROUP BY 1,2
        ) s
        WHERE mk.tenant_id = s.tenant_id AND mk.month_start = s.month_start;

        INSERT INTO monthly_kpis (tenant_id, month_start, turnover, gp_value, purchases, updated_at)
        SELECT :tenant_id, date_trunc('month', :as_of_date)::date, 0,0,0, now()
        WHERE NOT EXISTS (
        SELECT 1 FROM monthly_kpis WHERE tenant_id=:tenant_id AND month_start=date_trunc('month', :as_of_date)::date
        );

        Reads
        -- MTD
        SELECT * FROM monthly_kpis
        WHERE tenant_id=$1 AND month_start=date_trunc('month',$2)::date;

        -- YTD
        SELECT * FROM yearly_kpis
        WHERE tenant_id=$1 AND year_start = date_trunc('year',$2)::date;

4) Hot-path queries & table design
	•	Composite indexes that mirror UI filters:
        CREATE INDEX sm_tenant_sku_date ON stock_movements (tenant_id, sku, movement_date DESC);
        CREATE INDEX products_tenant_sku  ON products (tenant_id, sku);
    •	For very large facts, monthly partitions by kpi_date. Keep current month “hot”.
	•	Avoid N+1 in API—batch by tenant & date ranges.

5) Background jobs (never compute on the device)
	•	On PDF ingest:
	1.	Upsert daily_kpis for that tenant/day.
	2.	Refresh that tenant’s monthly and yearly rollups.
	3.	Update any leaderboards (low GP, over‑stocked).
	•	Use a queue (RQ/Celery/Sidekiq/BullMQ).
	•	Keep jobs idempotent (safe to retry).

6) Caching strategy
	•	DB-side: pre-aggregations (above) are your primary cache.
	•	API-side: short‑TTL (30–60s) cache per tenant_id, as_of_date (Redis or in‑memory).
	•	HTTP caching for read endpoints: ETag + Cache-Control: max-age=60, stale-while-revalidate=120.
	•	Avoid caching anything tenant-crossing without care.

7) Data quality & guardrails
	•	Compute days of stock safely:
        floor avg_daily_sales to 0.1; cap to 365
        days_cover := LEAST(365, units / NULLIF(GREATEST(avg_daily_sales, 0.1),0));

8) API shape (simple & O(1) reads)
	•	One summary endpoint that returns Daily / MTD / YTD in a single call:
        GET /kpis/summary?as_of=2025-08-05
        → { daily:{...}, mtd:{...}, ytd:{...}, insights:[...] } 

	•	Endpoint for lists supports cursor pagination and limit=20 for low‑GP/over‑stocked lists.
	•	Enforce tenant scoping in server middleware; never pass tenant_id from client.

9) Mobile client performance (React Native/Expo)
	•	Lists:
	•	Use FlashList (or FlatList with getItemLayout, removeClippedSubviews, proper keyExtractor).
	•	Paginate (20–30 items); infinite scroll or “Show more”.
	•	Rendering:
	•	Memoize rows (React.memo), stable props, and useCallback handlers.
	•	Avoid anonymous inline functions in heavy lists.
	•	Keep state local; avoid global re-renders (Colocate state; use Zustand/Jotai or React Query).
	•	Data fetching:
	•	Use React Query with staleTime (30–60s) + background revalidate.
	•	Prefetch the Summary screen while the Login/Loading screen is shown.
	•	Charts:
	•	Precompute series on the server; send arrays ready to plot.
	•	Limit points (e.g., 14‑day window for “Trends”).
	•	UX:
	•	Skeleton loaders for cards.
	•	Optimistic navigation; fetch in parallel.
	•	Network:
	•	Enable gzip/Br compression on API; keep payloads < 50–100KB per request.

10) Observability & tuning
	•	Log slow queries (log_min_duration_statement = 200ms).
	•	Add pg_stat_statements; review top 10 every week.
	•	Track p95 latency per endpoint (APM: OpenTelemetry + your stack).
	•	Auto‑vacuum thresholds appropriate for write volume; consider autovacuum_vacuum_scale_factor=0.05 on hot tables.
	•	Nightly VACUUM (ANALYZE) where needed; ensure regular ANALYZE after bulk loads.

11) Scaling path (when needed)
	•	Add a read replica and route analytics reads there.
	•	Partition the biggest tables by month if row counts explode.
	•	If one tenant becomes 10× heavier, introduce an app‑level tenant router and move that tenant to its own DB with identical schema—no frontend changes.

12) Security & privacy (POPIA‑friendly)
	•	RLS on by default; separate DB role for API with no bypass rights.
	•	TLS everywhere; rotate secrets; IP‑restrict DB access.
	•	Audit table for admin actions (tenant_id, user_id, action, at).
	•	Backups: nightly full + continuous WAL; monthly restore test.

13) Deployment checklist
	•	Migrations are forward‑only; use CONCURRENTLY for new indexes in production.
	•	Blue‑green / canary deploys for API.
	•	Seed a demo tenant (synthetic data) for App Store review/testing.

14) Quick acceptance tests
	•	Summary endpoint returns < 100ms p95 (warm cache) for a typical tenant.
	•	First paint of dashboard < 1.0s on mid‑range Android; < 700ms on recent iPhone.
	•	Low‑GP / Over‑stocked lists render 20 items in < 200ms after data arrival.
	•	MTD/YTD numbers match manual SQL spot checks for 3 random days.

TL;DR
	•	Aggregate in DB, not on device.
	•	Keep daily as truth; maintain monthly/yearly rollups.
	•	Cache at API with short TTL.
	•	RN lists: FlashList, memoization, small payloads.
	•	Monitor slow queries; partition when truly needed.