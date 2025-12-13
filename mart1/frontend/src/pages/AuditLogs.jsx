import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import '../styles/AuditLogs.css';

function AuditLogs() {
  const { user } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    action: 'ALL',
    username: '',
    table: 'ALL',
  });

  useEffect(() => {
    fetchAuditLogs();
  }, []);

  const fetchAuditLogs = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/audit-logs?limit=100&user_role=${user?.role}`);
      setLogs(response.data.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
      setLoading(false);
    }
  };



  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getActionBadge = (action) => {
    const colors = {
      LOGIN: 'blue',
      INSERT: 'green',
      UPDATE: 'orange',
      DELETE: 'red',
      SELECT: 'purple'
    };
    return <span className={`badge badge-${colors[action] || 'gray'}`}>{action}</span>;
  };

  const getStatusBadge = (status) => {
    return status === 'SUCCESS' ? 
      <span className="badge badge-success">✓ {status}</span> : 
      <span className="badge badge-danger">✗ {status}</span>;
  };

  const filteredLogs = logs.filter(log => {
    if (filter.action !== 'ALL' && log.action !== filter.action) return false;
    if (filter.username && !log.username?.toLowerCase().includes(filter.username.toLowerCase())) return false;
    if (filter.table !== 'ALL' && log.table_name !== filter.table) return false;
    return true;
  });

  const uniqueActions = [...new Set(logs.map(l => l.action))].filter(Boolean);
  const uniqueTables = [...new Set(logs.map(l => l.table_name))].filter(Boolean);

  return (
    <div className="audit-logs-container">
      <div className="page-header">
        <h1>🔍 Database Activity Monitor</h1>
        <p>Track all database operations and detect suspicious activities</p>
      </div>

      <div className="content-section">
        <div className="filters-section">
          <div className="filter-group">
            <label>Action:</label>
            <select value={filter.action} onChange={(e) => setFilter({...filter, action: e.target.value})}>
              <option value="ALL">All Actions</option>
              {uniqueActions.map(action => (
                <option key={action} value={action}>{action}</option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label>Username:</label>
            <input 
              type="text" 
              placeholder="Filter by username..."
              value={filter.username}
              onChange={(e) => setFilter({...filter, username: e.target.value})}
            />
          </div>
          <div className="filter-group">
            <label>Table:</label>
            <select value={filter.table} onChange={(e) => setFilter({...filter, table: e.target.value})}>
              <option value="ALL">All Tables</option>
              {uniqueTables.map(table => (
                <option key={table} value={table}>{table}</option>
              ))}
            </select>
          </div>
          <button className="btn-refresh" onClick={fetchAuditLogs}>🔄 Refresh</button>
        </div>

        {loading ? (
          <div className="loading">Loading audit logs...</div>
        ) : (
          <div className="audit-table-container">
            <table className="audit-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>User</th>
                  <th>Role</th>
                  <th>Action</th>
                  <th>Table</th>
                  <th>Record ID</th>
                  <th>Status</th>
                  <th>Changes</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="no-data">No audit logs found</td>
                  </tr>
                ) : (
                  filteredLogs.map((log) => (
                    <tr key={log.log_id} className={log.status === 'FAILED' ? 'failed-row' : ''}>
                      <td>{formatTimestamp(log.timestamp)}</td>
                      <td>{log.username || '-'}</td>
                      <td>{log.role || '-'}</td>
                      <td>{getActionBadge(log.action)}</td>
                      <td>{log.table_name || '-'}</td>
                      <td>{log.record_id || '-'}</td>
                      <td>{getStatusBadge(log.status)}</td>
                      <td>
                        {log.old_values || log.new_values ? (
                          <details>
                            <summary>View</summary>
                            {log.old_values && (
                              <div className="changes-detail">
                                <strong>Before:</strong>
                                <pre>{JSON.stringify(log.old_values, null, 2)}</pre>
                              </div>
                            )}
                            {log.new_values && (
                              <div className="changes-detail">
                                <strong>After:</strong>
                                <pre>{JSON.stringify(log.new_values, null, 2)}</pre>
                              </div>
                            )}
                          </details>
                        ) : '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
            <div className="total-count">
              Showing {filteredLogs.length} of {logs.length} logs
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AuditLogs;
