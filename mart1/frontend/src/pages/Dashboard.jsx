import { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { dashboard, reports } from '../services/api';
import { Package, DollarSign, TrendingUp, AlertTriangle, Calendar, BarChart3, PieChart as PieChartIcon, Trophy } from 'lucide-react';
import '../styles/Dashboard.css';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [salesTrend, setSalesTrend] = useState([]);
  const [categorySales, setCategorySales] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState(7);

  useEffect(() => {
    loadDashboardData();
  }, [dateRange]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [statsRes, salesRes, categoryRes, productsRes] = await Promise.all([
        dashboard.getStats(),
        reports.getSalesByDate(dateRange),
        reports.getCategorySales(),
        reports.getTopProducts(5),
      ]);
      
      setStats(statsRes.data);
      setSalesTrend(salesRes.data.sales_by_date);
      setCategorySales(categoryRes.data.category_sales);
      setTopProducts(productsRes.data.top_products);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#ec4899', '#f43f5e'];

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Dashboard Overview</h1>
          <p className="dashboard-subtitle">Welcome back! Here's your business summary</p>
        </div>
        <div className="date-range-selector">
          <Calendar size={18} />
          <label>Sales Period:</label>
          <select value={dateRange} onChange={(e) => setDateRange(Number(e.target.value))}>
            <option value={7}>Last 7 Days</option>
            <option value={14}>Last 14 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>
        </div>
      </div>
      
      <div className="stats-grid">
        <div className="stat-card gradient-blue">
          <div className="stat-content">
            <div className="stat-icon-wrapper">
              <Package className="stat-icon" size={28} />
            </div>
            <div className="stat-info">
              <h3>Total Products</h3>
              <p className="stat-value">{stats?.total_products || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card gradient-green">
          <div className="stat-content">
            <div className="stat-icon-wrapper">
              <TrendingUp className="stat-icon" size={28} />
            </div>
            <div className="stat-info">
              <h3>Total Sales</h3>
              <p className="stat-value">{stats?.total_sales || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card gradient-purple">
          <div className="stat-content">
            <div className="stat-icon-wrapper">
              <DollarSign className="stat-icon" size={28} />
            </div>
            <div className="stat-info">
              <h3>Total Revenue</h3>
              <p className="stat-value">₹{stats?.total_revenue?.toFixed(2) || '0.00'}</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card gradient-orange">
          <div className="stat-content">
            <div className="stat-icon-wrapper">
              <AlertTriangle className="stat-icon" size={28} />
            </div>
            <div className="stat-info">
              <h3>Low Stock Items</h3>
              <p className="stat-value">{stats?.low_stock_count || 0}</p>
            </div>
          </div>
        </div>
        
        <div className="stat-card gradient-pink">
          <div className="stat-content">
            <div className="stat-icon-wrapper">
              <Calendar className="stat-icon" size={28} />
            </div>
            <div className="stat-info">
              <h3>Today's Sales</h3>
              <p className="stat-value">₹{stats?.today_sales?.toFixed(2) || '0.00'}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <div className="chart-header">
            <BarChart3 size={22} />
            <h2>Sales Trend (Last {dateRange} Days)</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={salesTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="date" stroke="#6b7280" style={{ fontSize: '0.875rem' }} />
              <YAxis stroke="#6b7280" style={{ fontSize: '0.875rem' }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white', 
                  borderRadius: '12px', 
                  border: '1px solid #e5e7eb', 
                  boxShadow: '0 10px 40px rgba(0,0,0,0.1)' 
                }}
              />
              <Legend wrapperStyle={{ fontSize: '0.875rem' }} />
              <Line type="monotone" dataKey="total" stroke="#3b82f6" strokeWidth={3} name="Revenue (₹)" dot={{ fill: '#3b82f6', r: 5 }} activeDot={{ r: 7 }} />
              <Line type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={3} name="Sales Count" dot={{ fill: '#6366f1', r: 5 }} activeDot={{ r: 7 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <div className="chart-header">
            <PieChartIcon size={22} />
            <h2>Category Sales Distribution</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={categorySales}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ category, percent }) => `${category} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {categorySales.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white', 
                  borderRadius: '12px', 
                  border: '1px solid #e5e7eb', 
                  boxShadow: '0 10px 40px rgba(0,0,0,0.1)' 
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card wide">
          <div className="chart-header">
            <Trophy size={22} />
            <h2>Top 5 Products by Revenue</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topProducts}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="product" stroke="#6b7280" style={{ fontSize: '0.875rem' }} />
              <YAxis stroke="#6b7280" style={{ fontSize: '0.875rem' }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'white', 
                  borderRadius: '12px', 
                  border: '1px solid #e5e7eb', 
                  boxShadow: '0 10px 40px rgba(0,0,0,0.1)' 
                }}
              />
              <Legend wrapperStyle={{ fontSize: '0.875rem' }} />
              <Bar dataKey="revenue" fill="url(#colorRevenue)" name="Revenue (₹)" radius={[8, 8, 0, 0]} />
              <defs>
                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.9}/>
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.9}/>
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
