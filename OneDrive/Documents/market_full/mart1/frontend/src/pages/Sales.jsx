import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { sales, products, customers } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { ShoppingCart, Plus, Minus, X, Search, CreditCard, Wallet, DollarSign, User, Star, MessageSquare, Trash2 } from 'lucide-react';
import '../styles/Sales.css';

function Sales() {
  const { user } = useAuth();
  const [salesList, setSalesList] = useState([]);
  const [productList, setProductList] = useState([]);
  const [customerList, setCustomerList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewSaleForm, setShowNewSaleForm] = useState(false);
  const [cart, setCart] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('CASH');
  const [discount, setDiscount] = useState(0);
  const [rating, setRating] = useState('');
  const [feedback, setFeedback] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [salesRes, productsRes, customersRes] = await Promise.all([
        sales.getAll(),
        products.getAll(),
        customers.getAll(),
      ]);
      setSalesList(salesRes.data.sales);
      setProductList(productsRes.data.products);
      setCustomerList(customersRes.data.customers);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = (product) => {
    if (product.stock_quantity === 0) {
      toast.error('Product out of stock!');
      return;
    }
    const existingItem = cart.find(item => item.product_id === product.product_id);
    if (existingItem) {
      if (existingItem.quantity >= product.stock_quantity) {
        toast.error('Cannot add more than available stock!');
        return;
      }
      setCart(cart.map(item =>
        item.product_id === product.product_id
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
      toast.success(`Added another ${product.name}`, { duration: 1500 });
    } else {
      setCart([...cart, { ...product, quantity: 1 }]);
      toast.success(`${product.name} added to cart`, { duration: 1500 });
    }
  };

  const updateQuantity = (productId, newQuantity) => {
    if (newQuantity <= 0) {
      setCart(cart.filter(item => item.product_id !== productId));
    } else {
      setCart(cart.map(item =>
        item.product_id === productId
          ? { ...item, quantity: newQuantity }
          : item
      ));
    }
  };

  const calculateTotal = () => {
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
  };

  const calculateDiscountedTotal = () => {
    const subtotal = calculateTotal();
    if (discount > 0) {
      return subtotal - (subtotal * discount / 100);
    }
    return subtotal;
  };

  const handleProcessSale = async (e) => {
    e.preventDefault();
    if (cart.length === 0) {
      toast.error('Cart is empty!');
      return;
    }

    const loadingToast = toast.loading('Processing sale...');
    try {
      const saleData = {
        items: cart.map(item => ({
          product_id: item.product_id,
          quantity: item.quantity,
        })),
        payment_method: paymentMethod,
        customer_id: selectedCustomer ? parseInt(selectedCustomer) : null,
        employee_id: user.employee_id,
        discount_percentage: discount || 0,
        customer_rating: rating ? parseFloat(rating) : null,
        feedback: feedback || null,
      };

      await sales.create(saleData);
      toast.success('Sale completed successfully! 🎉', { id: loadingToast, duration: 3000 });
      
      // Reset form
      setCart([]);
      setSelectedCustomer('');
      setPaymentMethod('CASH');
      setDiscount(0);
      setRating('');
      setFeedback('');
      setShowNewSaleForm(false);
      loadData();
    } catch (error) {
      toast.error('Failed to process sale: ' + (error.response?.data?.detail || error.message), { id: loadingToast });
    }
  };

  const filteredProducts = productList.filter(product => {
    const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || product.category_id === parseInt(categoryFilter);
    return matchesSearch && matchesCategory;
  });

  const categories = [...new Set(productList.map(p => ({ id: p.category_id, name: p.category })))];
  const uniqueCategories = categories.filter((cat, index, self) =>
    index === self.findIndex((c) => c.id === cat.id)
  );

  if (loading) {
    return <div className="loading">Loading sales...</div>;
  }

  return (
    <div className="sales-page">
      <div className="page-header">
        <h1>💰 Sales</h1>
        {(user?.role === 'ADMIN' || user?.role === 'MANAGER' || user?.role === 'CASHIER') && (
          <button className="btn-primary" onClick={() => setShowNewSaleForm(true)}>
            + New Sale
          </button>
        )}
      </div>

      <div className="sales-table-container">
        <table className="sales-table">
          <thead>
            <tr>
              <th>Sale ID</th>
              <th>Date & Time</th>
              <th>Total Amount</th>
              <th>Discount</th>
              <th>Payment Method</th>
              <th>Rating</th>
              <th>Feedback</th>
              <th>Customer</th>
              <th>Employee</th>
            </tr>
          </thead>
          <tbody>
            {salesList.map((sale) => (
              <tr key={sale.sale_id}>
                <td>{sale.sale_id}</td>
                <td>{new Date(sale.sale_time).toLocaleString()}</td>
                <td>₹{sale.total_amount.toFixed(2)}</td>
                <td>{sale.discount_percentage ? `${sale.discount_percentage}%` : '-'}</td>
                <td>{sale.payment_method}</td>
                <td>{sale.customer_rating ? `⭐ ${sale.customer_rating}` : '-'}</td>
                <td>
                  {sale.feedback && (
                    <span className={`feedback-badge ${sale.feedback.toLowerCase()}`}>
                      {sale.feedback}
                    </span>
                  )}
                </td>
                <td>{sale.customer || 'Walk-in'}</td>
                <td>{sale.employee}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showNewSaleForm && (
        <AnimatePresence>
          <motion.div 
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowNewSaleForm(false)}
          >
            <motion.div 
              className="modal-content-large"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h2><ShoppingCart size={28} /> New Sale</h2>
                <button className="close-btn" onClick={() => setShowNewSaleForm(false)}>
                  <X size={24} />
                </button>
              </div>
            
              <div className="sale-form-container">
                {/* Products Section */}
                <div className="products-section">
                  <div className="products-header">
                    <h3>Select Products</h3>
                    <div className="product-filters">
                      <div className="search-bar-small">
                        <Search size={18} />
                        <input
                          type="text"
                          placeholder="Search products..."
                          value={searchTerm}
                          onChange={(e) => setSearchTerm(e.target.value)}
                        />
                      </div>
                      <select 
                        value={categoryFilter}
                        onChange={(e) => setCategoryFilter(e.target.value)}
                        className="category-filter"
                      >
                        <option value="all">All Categories</option>
                        {uniqueCategories.map(cat => (
                          <option key={cat.id} value={cat.id}>{cat.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  
                  <div className="product-grid">
                    {filteredProducts.map((product) => (
                      <motion.div 
                        key={product.product_id} 
                        className="product-card"
                        whileHover={{ scale: 1.03, y: -4 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <div className="product-info">
                          <h4>{product.name}</h4>
                          <p className="product-price">₹{product.price.toFixed(2)}</p>
                          <p className={`product-stock ${product.stock_quantity < 10 ? 'low' : ''}`}>
                            Stock: {product.stock_quantity}
                          </p>
                        </div>
                        <button
                          className="btn-add-cart"
                          onClick={() => addToCart(product)}
                          disabled={product.stock_quantity === 0}
                        >
                          <Plus size={18} />
                          Add to Cart
                        </button>
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* Cart Section */}
                <div className="cart-section">
                  <div className="cart-header">
                    <h3>Cart</h3>
                    {cart.length > 0 && (
                      <span className="cart-count">{cart.length} items</span>
                    )}
                  </div>
                  
                  {cart.length === 0 ? (
                    <div className="empty-cart">
                      <ShoppingCart size={64} strokeWidth={1} />
                      <p>Your cart is empty</p>
                      <small>Add products to get started</small>
                    </div>
                  ) : (
                    <>
                      <div className="cart-items">
                        <AnimatePresence>
                          {cart.map((item) => (
                            <motion.div 
                              key={item.product_id} 
                              className="cart-item"
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              exit={{ opacity: 0, x: 20 }}
                            >
                              <div className="cart-item-info">
                                <strong>{item.name}</strong>
                                <p>₹{item.price.toFixed(2)} × {item.quantity}</p>
                              </div>
                              <div className="cart-item-actions">
                                <div className="quantity-controls">
                                  <button onClick={() => updateQuantity(item.product_id, item.quantity - 1)}>
                                    <Minus size={16} />
                                  </button>
                                  <span className="quantity">{item.quantity}</span>
                                  <button onClick={() => updateQuantity(item.product_id, item.quantity + 1)}>
                                    <Plus size={16} />
                                  </button>
                                </div>
                                <div className="cart-item-total">
                                  <strong>₹{(item.price * item.quantity).toFixed(2)}</strong>
                                </div>
                                <button 
                                  className="btn-remove"
                                  onClick={() => updateQuantity(item.product_id, 0)}
                                >
                                  <Trash2 size={16} />
                                </button>
                              </div>
                            </motion.div>
                          ))}
                        </AnimatePresence>
                      </div>

                      <div className="cart-summary">
                        <div className="summary-row">
                          <span>Subtotal:</span>
                          <span className="amount">₹{calculateTotal().toFixed(2)}</span>
                        </div>
                        {discount > 0 && (
                          <>
                            <div className="summary-row discount">
                              <span>Discount ({discount}%):</span>
                              <span className="amount">-₹{(calculateTotal() * discount / 100).toFixed(2)}</span>
                            </div>
                            <div className="summary-divider"></div>
                          </>
                        )}
                        <div className="summary-row total">
                          <strong>Total:</strong>
                          <strong className="amount-large">₹{calculateDiscountedTotal().toFixed(2)}</strong>
                        </div>
                      </div>

                      <form onSubmit={handleProcessSale} className="checkout-form">
                        <div className="form-row">
                          <div className="form-group">
                            <label><CreditCard size={18} /> Payment Method</label>
                            <select
                              value={paymentMethod}
                              onChange={(e) => setPaymentMethod(e.target.value)}
                              required
                            >
                              <option value="CASH">💵 Cash</option>
                              <option value="CARD">💳 Card</option>
                              <option value="UPI">📱 UPI</option>
                              <option value="WALLET">👛 Wallet</option>
                            </select>
                          </div>

                          <div className="form-group">
                            <label><User size={18} /> Customer (Optional)</label>
                            <select
                              value={selectedCustomer}
                              onChange={(e) => setSelectedCustomer(e.target.value)}
                            >
                              <option value="">Walk-in Customer</option>
                              {customerList.map((customer) => (
                                <option key={customer.customer_id} value={customer.customer_id}>
                                  {customer.name}
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>

                        <div className="form-row">
                          <div className="form-group">
                            <label><DollarSign size={18} /> Discount (%) - Optional</label>
                            <input
                              type="number"
                              min="0"
                              max="100"
                              value={discount}
                              onChange={(e) => setDiscount(parseFloat(e.target.value) || 0)}
                              placeholder="0"
                            />
                          </div>

                          <div className="form-group">
                            <label><Star size={18} /> Customer Rating (Optional)</label>
                            <select
                              value={rating}
                              onChange={(e) => setRating(e.target.value)}
                            >
                              <option value="">No rating</option>
                              <option value="5.0">⭐⭐⭐⭐⭐ 5.0</option>
                              <option value="4.5">⭐⭐⭐⭐✰ 4.5</option>
                              <option value="4.0">⭐⭐⭐⭐ 4.0</option>
                              <option value="3.5">⭐⭐⭐✰✰ 3.5</option>
                              <option value="3.0">⭐⭐⭐ 3.0</option>
                            </select>
                          </div>
                        </div>

                        <div className="form-group">
                          <label><MessageSquare size={18} /> Customer Feedback (Optional)</label>
                          <select
                            value={feedback}
                            onChange={(e) => setFeedback(e.target.value)}
                          >
                            <option value="">No feedback</option>
                            <option value="Excellent">😊 Excellent</option>
                            <option value="Good">🙂 Good</option>
                            <option value="Average">😐 Average</option>
                            <option value="Poor">😞 Poor</option>
                          </select>
                        </div>

                        <div className="form-actions">
                          <button 
                            type="button" 
                            className="btn-secondary" 
                            onClick={() => setShowNewSaleForm(false)}
                          >
                            Cancel
                          </button>
                          <button 
                            type="submit" 
                            className="btn-complete-sale"
                          >
                            <ShoppingCart size={20} />
                            Complete Sale
                          </button>
                        </div>
                      </form>
                    </>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  );
}

export default Sales;
