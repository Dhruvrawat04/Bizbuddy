import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import './LoadingSkeleton.css';

export function StatsCardSkeleton() {
  return (
    <div className="stats-grid">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="stat-card skeleton-card">
          <Skeleton height={80} borderRadius={12} />
        </div>
      ))}
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="chart-container skeleton-card">
      <Skeleton height={40} width={200} style={{ marginBottom: 20 }} />
      <Skeleton height={300} borderRadius={12} />
    </div>
  );
}

export function TableSkeleton({ rows = 5, columns = 4 }) {
  return (
    <div className="table-skeleton">
      <Skeleton height={50} style={{ marginBottom: 10 }} />
      {[...Array(rows)].map((_, i) => (
        <div key={i} style={{ display: 'flex', gap: '10px', marginBottom: '8px' }}>
          {[...Array(columns)].map((_, j) => (
            <Skeleton key={j} height={40} style={{ flex: 1 }} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function FormSkeleton() {
  return (
    <div className="form-skeleton">
      <Skeleton height={40} style={{ marginBottom: 16 }} />
      <Skeleton height={40} style={{ marginBottom: 16 }} />
      <Skeleton height={100} style={{ marginBottom: 16 }} />
      <Skeleton height={44} width={120} />
    </div>
  );
}
