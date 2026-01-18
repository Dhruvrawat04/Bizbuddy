import { useState, useEffect } from 'react';
import { notifications } from '../services/api';
import Pagination from '../components/Pagination';
import '../styles/Notifications.css';

function Notifications() {
  const [notificationList, setNotificationList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 50,
    total_items: 0,
    total_pages: 1,
    has_next: false,
    has_previous: false
  });
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadNotifications();
  }, [currentPage]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const res = await notifications.getAll(currentPage, 50);
      setNotificationList(res.data.notifications);
      if (res.data.pagination) {
        setPagination(res.data.pagination);
      }
    } catch (error) {
      console.error('Failed to load notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await notifications.update(notificationId, 'read');
      loadNotifications();
    } catch (error) {
      alert('Failed to update notification: ' + (error.response?.data?.detail || error.message));
    }
  };

  const filteredNotifications = notificationList.filter(n => {
    if (filter === 'all') return true;
    return n.status === filter;
  });

  const unreadCount = notificationList.filter(n => n.status === 'unread').length;

  if (loading) {
    return <div className="loading">Loading notifications...</div>;
  }

  return (
    <div className="notifications-page">
      <div className="page-header">
        <h1>🔔 Notifications</h1>
        <div className="notification-badge">{unreadCount} Unread</div>
      </div>

      <div className="filter-bar">
        <button 
          className={filter === 'all' ? 'active' : ''} 
          onClick={() => setFilter('all')}
        >
          All ({notificationList.length})
        </button>
        <button 
          className={filter === 'unread' ? 'active' : ''} 
          onClick={() => setFilter('unread')}
        >
          Unread ({unreadCount})
        </button>
        <button 
          className={filter === 'read' ? 'active' : ''} 
          onClick={() => setFilter('read')}
        >
          Read ({notificationList.length - unreadCount})
        </button>
      </div>

      <div className="notifications-list">
        {filteredNotifications.length === 0 ? (
          <div className="no-notifications">
            <p>No notifications to display</p>
          </div>
        ) : (
          filteredNotifications.map((notification) => (
            <div 
              key={notification.notification_id} 
              className={`notification-item ${notification.status}`}
            >
              <div className="notification-icon">
                {notification.type === 'low_stock' ? '⚠️' : '📢'}
              </div>
              <div className="notification-content">
                <p className="notification-message">{notification.message}</p>
                <div className="notification-meta">
                  <span className="notification-time">
                    {new Date(notification.created_at).toLocaleString()}
                  </span>
                  {notification.product_name && (
                    <span className="notification-product">
                      Product: {notification.product_name}
                    </span>
                  )}
                </div>
              </div>
              {notification.status === 'unread' && (
                <button 
                  className="btn-mark-read" 
                  onClick={() => markAsRead(notification.notification_id)}
                >
                  Mark as Read
                </button>
              )}
            </div>
          ))
        )}
      </div>

      <Pagination
        currentPage={pagination.page}
        totalPages={pagination.total_pages}
        totalItems={pagination.total_items}
        pageSize={pagination.page_size}
        onPageChange={(page) => setCurrentPage(page)}
        loading={loading}
      />
    </div>
  );
}

export default Notifications;
