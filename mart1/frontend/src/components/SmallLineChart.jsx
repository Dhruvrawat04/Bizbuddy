import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

export default function SmallLineChart({ data = [], xKey = 'day', dataKey = 'total', title = '' }) {
  return (
    <div className="chart-card">
      {title && <h3 className="chart-card-title">{title}</h3>}
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey={xKey}
              tick={{ fontSize: 11 }}
              minTickGap={24}
              angle={-35}
              textAnchor="end"
              height={60}
            />
            <YAxis tick={{ fontSize: 11 }} width={60} />
            <Tooltip formatter={(v) => (typeof v === 'number' ? `₹${v.toFixed(2)}` : v)} />
            <Line type="monotone" dataKey={dataKey} stroke="#4F46E5" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
