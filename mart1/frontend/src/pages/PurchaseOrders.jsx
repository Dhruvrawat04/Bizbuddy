import { useState, useEffect } from 'react';
import { purchaseOrders, suppliers, products as productsApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { ShoppingCart, Plus, X, Eye, Package, Truck, Building2, Calendar, Tag, Hash, DollarSign, Minus } from 'lucide-react';
import '../styles/PurchaseOrders.css';

function PurchaseOrders() {
  const { user } = useAuth();
  const [orderList, setOrderList] = useState([]);
  const [supplierList, setSupplierList] = useState([]);
  const [productList, setProductList] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [orderItems, setOrderItems] = useState([]);
  const [formData, setFormData] = useState({
    supplier_id: '',
    items: [{ product_id: '', quantity: '', unit_price: '' }],
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    // Filter products based on selected supplier's category
    if (formData.supplier_id) {
      const selectedSupplier = supplierList.find(
        (s) => s.supplier_id === parseInt(formData.supplier_id)
      );
      
      if (selectedSupplier && selectedSupplier.category_id) {
        const filtered = productList.filter(
          (product) => product.category_id === selectedSupplier.category_id
        );
        setFilteredProducts(filtered);
      } else {
        setFilteredProducts(productList);
      }
    } else {
      setFilteredProducts([]);
    }
  }, [formData.supplier_id, supplierList, productList]);

  const loadData = async () => {
    try {
      const [ordersRes, suppliersRes, productsRes] = await Promise.all([
        purchaseOrders.getAll(),
        suppliers.getAll(),
        productsApi.getAll(),
      ]);
      setOrderList(ordersRes.data.purchase_orders);
      setSupplierList(suppliersRes.data.suppliers);
      setProductList(productsRes.data.products);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSupplierChange = (supplierId) => {
    setFormData({
      supplier_id: supplierId,
      items: [{ product_id: '', quantity: '', unit_price: '' }],
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await purchaseOrders.create({
        supplier_id: parseInt(formData.supplier_id),
        items: formData.items.map(item => ({
          product_id: parseInt(item.product_id),
          quantity: parseInt(item.quantity),
          unit_price: parseFloat(item.unit_price),
        })),
      });
      alert('Purchase order created successfully!');
      resetForm();
      loadData();
    } catch (error) {
      alert('Failed to create purchase order: ' + (error.response?.data?.detail || error.message));
    }
  };

  const addItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { product_id: '', quantity: '', unit_price: '' }],
    });
  };

  const removeItem = (index) => {
    const newItems = formData.items.filter((_, i) => i !== index);
    setFormData({ ...formData, items: newItems });
  };

  const updateItem = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = value;
    setFormData({ ...formData, items: newItems });
  };

  const viewOrderDetails = async (order) => {
    try {
      const res = await purchaseOrders.getDetails(order.order_id);
      setOrderItems(res.data.items);
      setSelectedOrder(order);
    } catch (error) {
      alert('Failed to load order details: ' + (error.response?.data?.detail || error.message));
    }
  };

  const receiveOrder = async (orderId) => {
    if (!window.confirm('Mark this order as received and update stock?')) return;
    try {
      await purchaseOrders.receive(orderId);
      alert('Order received and stock updated successfully!');
      setSelectedOrder(null);
      loadData();
    } catch (error) {
      alert('Failed to receive order: ' + (error.response?.data?.detail || error.message));
    }
  };

  const resetForm = () => {
    setFormData({ supplier_id: '', items: [{ product_id: '', quantity: '', unit_price: '' }] });
    setShowForm(false);
  };

  if (loading) {
    return <div className="loading">Loading purchase orders...</div>;
  }

  return (
    <div className="purchase-orders-page">
      <div className="page-header">
        <h1><ShoppingCart size={32} style={{ marginRight: '12px', verticalAlign: 'middle' }} />Purchase Orders</h1>
        {(user?.role === 'ADMIN' || user?.role === 'MANAGER') && (
          <button className="btn-primary" onClick={() => setShowForm(true)}>
            <Plus size={20} style={{ marginRight: '6px' }} />
            Create Order
          </button>
        )}
      </div>

      {showForm && (
        <div className="modal" onClick={resetForm}>
          <div className="modal-content large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create Purchase Order</h2>
              <button className="modal-close" onClick={resetForm}>
                <X size={24} />
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>
                  <Building2 size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                  Supplier *
                </label>
                <select
                  value={formData.supplier_id}
                  onChange={(e) => handleSupplierChange(e.target.value)}
                  required
                >
                  <option value="">Select Supplier</option>
                  {supplierList.map((supplier) => (
                    <option key={supplier.supplier_id} value={supplier.supplier_id}>
                      {supplier.name} {supplier.category_name ? `(${supplier.category_name})` : ''}
                    </option>
                  ))}
                </select>
                {formData.supplier_id && (
                  <small style={{ color: '#4CAF50', marginTop: '4px', display: 'block' }}>
                    ✓ Products filtered by supplier's category
                  </small>
                )}
              </div>

              <div className="items-section">
                <h3>
                  <Package size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                  Order Items
                </h3>
                {formData.items.map((item, index) => (
                  <div key={index} className="item-row">
                    <div className="item-field product-field">
                      <label>Product *</label>
                      <select
                        value={item.product_id}
                        onChange={(e) => updateItem(index, 'product_id', e.target.value)}
                        required
                        disabled={!formData.supplier_id}
                      >
                        <option value="">
                          {!formData.supplier_id 
                            ? 'Select Supplier First' 
                            : filteredProducts.length === 0
                            ? 'No products available for this supplier\'s category'
                            : 'Select Product'}
                        </option>
                        {filteredProducts.map((product) => (
                          <option key={product.product_id} value={product.product_id}>
                            {product.name} (Stock: {product.stock_quantity})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="item-field">
                      <label>Quantity *</label>
                      <input
                        type="number"
                        placeholder="0"
                        value={item.quantity}
                        onChange={(e) => updateItem(index, 'quantity', e.target.value)}
                        required
                        min="1"
                      />
                    </div>
                    <div className="item-field">
                      <label>Unit Price *</label>
                      <input
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        value={item.unit_price}
                        onChange={(e) => updateItem(index, 'unit_price', e.target.value)}
                        required
                        min="0"
                      />
                    </div>
                    {formData.items.length > 1 && (
                      <button 
                        type="button" 
                        className="btn-remove" 
                        onClick={() => removeItem(index)}
                        title="Remove item"
                      >
                        <Minus size={18} />
                      </button>
                    )}
                  </div>
                ))}
                <button 
                  type="button" 
                  className="btn-add-item" 
                  onClick={addItem}
                  disabled={!formData.supplier_id}
                >
                  <Plus size={18} style={{ marginRight: '6px' }} />
                  Add Item
                </button>
              </div>

              <div className="modal-actions">
                <button type="submit" className="btn-primary">
                  <ShoppingCart size={18} />
                  Create Order
                </button>
                <button type="button" className="btn-secondary" onClick={resetForm}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedOrder && (
        <div className="modal" onClick={() => setSelectedOrder(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>
                <Hash size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
                Order Details - #{selectedOrder.order_id}
              </h2>
              <button className="modal-close" onClick={() => setSelectedOrder(null)}>
                <X size={24} />
              </button>
            </div>
            <div className="order-info">
              <p><Building2 size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} /><strong>Supplier:</strong> {selectedOrder.supplier_name}</p>
              <p><Calendar size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} /><strong>Date:</strong> {new Date(selectedOrder.order_date).toLocaleDateString()}</p>
              <p><Tag size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} /><strong>Status:</strong> <span className={`status-badge ${selectedOrder.status.toLowerCase()}`}>{selectedOrder.status}</span></p>
            </div>
            
            <h3 style={{ marginTop: '20px', marginBottom: '12px' }}>
              <Package size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
              Items
            </h3>
            <table className="order-items-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Quantity</th>
                  <th>Unit Price</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {orderItems.map((item, index) => (
                  <tr key={index}>
                    <td>{item.product_name}</td>
                    <td>{item.quantity}</td>
                    <td>₹{item.unit_price.toFixed(2)}</td>
                    <td>₹{(item.quantity * item.unit_price).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="modal-actions">
              {selectedOrder.status === 'PENDING' && (user?.role === 'ADMIN' || user?.role === 'MANAGER') && (
                <button type="button" className="btn-primary" onClick={() => receiveOrder(selectedOrder.order_id)}>
                  <Truck size={18} />
                  Mark as Received
                </button>
              )}
              <button type="button" className="btn-secondary" onClick={() => setSelectedOrder(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="orders-table-container">
        <table className="orders-table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Supplier</th>
              <th>Date</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {orderList.map((order) => (
              <tr key={order.order_id}>
                <td>#{order.order_id}</td>
                <td>{order.supplier_name}</td>
                <td>{new Date(order.order_date).toLocaleDateString()}</td>
                <td>
                  <span className={`status-badge ${order.status.toLowerCase()}`}>
                    {order.status}
                  </span>
                </td>
                <td>
                  <button className="btn-view" onClick={() => viewOrderDetails(order)}>
                    <Eye size={16} style={{ marginRight: '4px' }} />
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default PurchaseOrders;
