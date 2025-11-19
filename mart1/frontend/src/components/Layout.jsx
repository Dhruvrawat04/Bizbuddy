import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  Package, 
  ShoppingCart, 
  Users, 
  UserCog, 
  Factory, 
  FolderOpen, 
  ClipboardList, 
  Bell, 
  LogOut, 
  User,
  Store,
  BarChart3,
  ExternalLink
} from 'lucide-react';
import '../styles/Layout.css';

function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <div className="layout">
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <Store className="sidebar-logo" size={28} />
          <h2>SuperMarket Pro</h2>
        </div>
        
        <nav className="sidebar-nav">
          <Link 
            to="/dashboard" 
            className={`nav-item ${isActive('/dashboard') ? 'active' : ''}`}
            onClick={() => setSidebarOpen(false)}
          >
            <LayoutDashboard className="nav-icon" size={20} />
            <span className="nav-text">Dashboard</span>
          </Link>
          
          <Link 
            to="/products" 
            className={`nav-item ${isActive('/products') ? 'active' : ''}`}
            onClick={() => setSidebarOpen(false)}
          >
            <Package className="nav-icon" size={20} />
            <span className="nav-text">Products</span>
          </Link>
          
          <Link 
            to="/sales" 
            className={`nav-item ${isActive('/sales') ? 'active' : ''}`}
            onClick={() => setSidebarOpen(false)}
          >
            <ShoppingCart className="nav-icon" size={20} />
            <span className="nav-text">Sales</span>
          </Link>
          
          {(user?.role === 'ADMIN' || user?.role === 'MANAGER') && (
            <Link 
              to="/customers" 
              className={`nav-item ${isActive('/customers') ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <Users className="nav-icon" size={20} />
              <span className="nav-text">Customers</span>
            </Link>
          )}
          
          {user?.role === 'ADMIN' && (
            <Link 
              to="/employees" 
              className={`nav-item ${isActive('/employees') ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <UserCog className="nav-icon" size={20} />
              <span className="nav-text">Employees</span>
            </Link>
          )}

          {user?.role === 'ADMIN' && (
            <Link 
              to="/suppliers" 
              className={`nav-item ${isActive('/suppliers') ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <Factory className="nav-icon" size={20} />
              <span className="nav-text">Suppliers</span>
            </Link>
          )}

          {user?.role === 'ADMIN' && (
            <Link 
              to="/categories" 
              className={`nav-item ${isActive('/categories') ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <FolderOpen className="nav-icon" size={20} />
              <span className="nav-text">Categories</span>
            </Link>
          )}

          {(user?.role === 'ADMIN' || user?.role === 'MANAGER') && (
            <Link 
              to="/purchase-orders" 
              className={`nav-item ${isActive('/purchase-orders') ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <ClipboardList className="nav-icon" size={20} />
              <span className="nav-text">Purchase Orders</span>
            </Link>
          )}

          <Link 
            to="/notifications" 
            className={`nav-item ${isActive('/notifications') ? 'active' : ''}`}
            onClick={() => setSidebarOpen(false)}
          >
            <Bell className="nav-icon" size={20} />
            <span className="nav-text">Notifications</span>
          </Link>

          <div className="nav-divider"></div>

          <a 
            href="http://localhost:5500" 
            target="_blank"
            rel="noopener noreferrer"
            className="nav-item analytics-link"
            onClick={() => setSidebarOpen(false)}
          >
            <BarChart3 className="nav-icon" size={20} />
            <span className="nav-text">Analytics Dashboard</span>
            <ExternalLink className="external-icon" size={14} />
          </a>
        </nav>
        
        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">
              <User size={20} />
            </div>
            <div className="user-details">
              <div className="user-name">{user?.name}</div>
              <div className="user-role">{user?.role}</div>
            </div>
          </div>
          <button className="btn-logout" onClick={handleLogout}>
            <LogOut size={18} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      <div className="main-wrapper">
        <header className="topbar">
          <button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            <span></span>
            <span></span>
            <span></span>
          </button>
          <div className="topbar-title">
            <h1>{location.pathname.slice(1).charAt(0).toUpperCase() + location.pathname.slice(2)}</h1>
          </div>
        </header>
        
        <main className="main-content">
          {children}
        </main>
      </div>
      
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)}></div>
      )}
    </div>
  );
}

export default Layout;
