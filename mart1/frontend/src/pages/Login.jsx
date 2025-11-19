import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { auth } from '../services/api';
import { Store, LogIn, User, Lock } from 'lucide-react';
import '../styles/Login.css';

function Login() {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await auth.login(credentials);
      login(response.data);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const quickLogin = (username, password) => {
    setCredentials({ username, password });
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <div className="login-logo">
            <Store size={36} />
          </div>
          <h1>SuperMarket Pro</h1>
          <p>Inventory Management System</p>
        </div>
        
        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>
              <User size={18} />
              Username
            </label>
            <input
              type="text"
              value={credentials.username}
              onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
              required
              placeholder="Enter your username"
              autoFocus
            />
          </div>
          
          <div className="form-group">
            <label>
              <Lock size={18} />
              Password
            </label>
            <input
              type="password"
              value={credentials.password}
              onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
              required
              placeholder="Enter your password"
            />
          </div>
          
          <button type="submit" className="btn-login" disabled={loading}>
            {loading ? (
              <>
                <div className="login-spinner"></div>
                Logging in...
              </>
            ) : (
              <>
                <LogIn size={20} />
                Login
              </>
            )}
          </button>
        </form>
        
        <div className="demo-credentials">
          <h3>Quick Login</h3>
          <div className="demo-buttons">
            <button onClick={() => quickLogin('alicej', 'admin123')} className="btn-demo admin">
              <div className="demo-role">Admin</div>
              <div className="demo-user">alicej</div>
            </button>
            <button onClick={() => quickLogin('carold', 'manager123')} className="btn-demo manager">
              <div className="demo-role">Manager</div>
              <div className="demo-user">carold</div>
            </button>
            <button onClick={() => quickLogin('emma', 'cashier123')} className="btn-demo cashier">
              <div className="demo-role">Cashier</div>
              <div className="demo-user">emma</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
