import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function SmallBarChart({ data = [], xKey = 'name', dataKey = 'value', title = '' }) {
  return (
    <div className="chart-card">
      {title && <h3 className="chart-card-title">{title}</h3>}
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey={xKey}
              tick={{ fontSize: 11 }}
              interval={0}
              angle={-25}
              textAnchor="end"
              height={70}
            />
            <YAxis tick={{ fontSize: 11 }} width={60} />
            <Tooltip formatter={(v) => (typeof v === 'number' ? `₹${v.toFixed(2)}` : v)} />
            <Bar dataKey={dataKey} fill="#06b6d4" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
