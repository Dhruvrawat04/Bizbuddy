import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { dashboard } from '../services/api';
import { Package, DollarSign, TrendingUp, AlertTriangle, Calendar, RefreshCw } from 'lucide-react';
import '../styles/Dashboard.css';
import SmallLineChart from '../components/SmallLineChart';
import SmallBarChart from '../components/SmallBarChart';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [periodLoading, setPeriodLoading] = useState(false);
  const [salesByDay, setSalesByDay] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [dateRange, setDateRange] = useState(0);
  const requestIdRef = useRef(0);
  const isFirstLoadRef = useRef(true);

  const formatSalesChartData = (rows, range) => {
    if (!Array.isArray(rows) || rows.length === 0) return [];

    if (range === 0 && rows.length > 60) {
      const monthlyTotals = rows.reduce((acc, row) => {
        const month = String(row.day).slice(0, 7);
        acc[month] = (acc[month] || 0) + Number(row.total || 0);
        return acc;
      }, {});

      return Object.entries(monthlyTotals).map(([day, total]) => ({ day, total }));
    }

    return rows.map((row) => ({
      day: row.day,
      total: Number(row.total || 0),
    }));
  };

  const applyOverviewData = (data, range) => {
    setStats(data.stats || null);
    setSalesByDay(formatSalesChartData(data.sales_by_day || [], range));
    setTopProducts(
      (data.top_products || []).map((row) => ({
        name: row.name,
        value: Number(row.revenue || 0),
      }))
    );
  };

  const loadDashboardData = async (range = dateRange, isInitial = false) => {
    const requestId = ++requestIdRef.current;

    if (isInitial) {
      setLoading(true);
    } else {
      setPeriodLoading(true);
      setStats(null);
      setSalesByDay([]);
      setTopProducts([]);
    }

    try {
      const response = await dashboard.getOverview(range, 5);
      if (requestId !== requestIdRef.current) return;

      applyOverviewData(response.data, range);
    } catch (error) {
      if (requestId !== requestIdRef.current) return;
      console.error('Failed to load dashboard data:', error);
    } finally {
      if (requestId !== requestIdRef.current) return;
      setLoading(false);
      setPeriodLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData(dateRange, isFirstLoadRef.current);
    isFirstLoadRef.current = false;
  }, [dateRange]);

  const handleDateRangeChange = (value) => {
    setDateRange(Number(value));
  };

  if (loading && !stats) {
    return (
      <div className="dashboard">
        <div className="dashboard-header">
          <div>
            <h1>Dashboard Overview</h1>
            <p className="dashboard-subtitle">Loading your business summary...</p>
          </div>
        </div>
        <div className="loading-container">
          <p>Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      className="dashboard"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="dashboard-header">
        <div>
          <h1>Dashboard Overview</h1>
          <p className="dashboard-subtitle">Welcome back! Here's your business summary</p>
        </div>
        <div className="dashboard-actions">
          <motion.button
            className="refresh-btn"
            onClick={() => loadDashboardData(dateRange, false)}
            disabled={periodLoading}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <RefreshCw size={18} className={periodLoading ? 'spinning' : ''} />
            Refresh
          </motion.button>
          <div className="date-range-selector">
            <Calendar size={18} />
            <label>Sales Period:</label>
            <select
              value={dateRange}
              onChange={(e) => handleDateRangeChange(e.target.value)}
              disabled={periodLoading}
            >
              <option value={0}>All Time</option>
              <option value={7}>Last 7 Days</option>
              <option value={14}>Last 14 Days</option>
              <option value={30}>Last 30 Days</option>
              <option value={90}>Last 90 Days</option>
            </select>
          </div>
        </div>
      </div>

      <div className={`dashboard-content ${periodLoading ? 'is-updating' : ''}`}>
        {periodLoading && (
          <div className="dashboard-period-loading">
            <div className="loading-spinner" />
            <p>Updating dashboard...</p>
          </div>
        )}

        <div className="stats-grid">
          <motion.div
            className="stat-card gradient-blue"
            whileHover={{ scale: 1.02, y: -4 }}
            transition={{ type: 'spring', stiffness: 300 }}
          >
            <div className="stat-content">
              <div className="stat-icon-wrapper">
                <Package className="stat-icon" size={28} />
              </div>
              <div className="stat-info">
                <h3>Total Products</h3>
                <p className="stat-value">{stats?.total_products ?? '—'}</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            className="stat-card gradient-green"
            whileHover={{ scale: 1.02, y: -4 }}
            transition={{ type: 'spring', stiffness: 300 }}
          >
            <div className="stat-content">
              <div className="stat-icon-wrapper">
                <TrendingUp className="stat-icon" size={28} />
              </div>
              <div className="stat-info">
                <h3>Total Sales</h3>
                <p className="stat-value">{stats?.total_sales ?? '—'}</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            className="stat-card gradient-purple"
            whileHover={{ scale: 1.02, y: -4 }}
            transition={{ type: 'spring', stiffness: 300 }}
          >
            <div className="stat-content">
              <div className="stat-icon-wrapper">
                <DollarSign className="stat-icon" size={28} />
              </div>
              <div className="stat-info">
                <h3>Total Revenue</h3>
                <p className="stat-value">
                  {stats ? `₹${(parseFloat(stats.total_revenue) || 0).toFixed(2)}` : '—'}
                </p>
              </div>
            </div>
          </motion.div>

          <motion.div
            className="stat-card gradient-orange"
            whileHover={{ scale: 1.02, y: -4 }}
            transition={{ type: 'spring', stiffness: 300 }}
          >
            <div className="stat-content">
              <div className="stat-icon-wrapper">
                <AlertTriangle className="stat-icon" size={28} />
              </div>
              <div className="stat-info">
                <h3>Low Stock Items</h3>
                <p className="stat-value">{stats?.low_stock_count ?? '—'}</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            className="stat-card gradient-pink"
            whileHover={{ scale: 1.02, y: -4 }}
            transition={{ type: 'spring', stiffness: 300 }}
          >
            <div className="stat-content">
              <div className="stat-icon-wrapper">
                <Calendar className="stat-icon" size={28} />
              </div>
              <div className="stat-info">
                <h3>Today's Sales</h3>
                <p className="stat-value">
                  {stats ? `₹${(parseFloat(stats.today_sales) || 0).toFixed(2)}` : '—'}
                </p>
              </div>
            </div>
          </motion.div>
        </div>

        <div className="charts-grid">
          {salesByDay.length > 0 ? (
            <SmallLineChart data={salesByDay} xKey="day" dataKey="total" title="Sales Over Time" />
          ) : (
            <div className="chart-empty-state">
              <h3>Sales Over Time</h3>
              <p>{periodLoading ? 'Loading sales data...' : 'No sales data for the selected period.'}</p>
            </div>
          )}
          {topProducts.length > 0 ? (
            <SmallBarChart data={topProducts} xKey="name" dataKey="value" title="Top Products (Revenue)" />
          ) : (
            <div className="chart-empty-state">
              <h3>Top Products (Revenue)</h3>
              <p>{periodLoading ? 'Loading product data...' : 'No product sales for the selected period.'}</p>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default Dashboard;
