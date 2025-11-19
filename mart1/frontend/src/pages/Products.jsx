import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { products, categories, suppliers } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Package, Plus, X, RefreshCw, Search, Edit, Trash2 } from 'lucide-react';
import ConfirmModal from '../components/ConfirmModal';
import { TableSkeleton } from '../components/LoadingSkeleton';
import '../styles/Products.css';

function Products() {
  const { user } = useAuth();
  const [productList, setProductList] = useState([]);
  const [categoryList, setCategoryList] = useState([]);
  const [supplierList, setSupplierList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showRestockForm, setShowRestockForm] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [newProduct, setNewProduct] = useState({
    name: '',
    barcode: '',
    price: '',
    stock_quantity: '',
    category_id: '',
    supplier_id: '',
    low_stock_threshold: 10,
  });
  const [restockQuantity, setRestockQuantity] = useState('');
  const [filteredSuppliers, setFilteredSuppliers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState({ isOpen: false, productId: null, productName: '' });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    // Filter suppliers based on selected category
    if (newProduct.category_id) {
      const filtered = supplierList.filter(
        (supplier) => supplier.category_id === parseInt(newProduct.category_id)
      );
      setFilteredSuppliers(filtered);
      
      // Reset supplier selection if current supplier doesn't match category
      if (newProduct.supplier_id) {
        const isValidSupplier = filtered.some(
          (s) => s.supplier_id === parseInt(newProduct.supplier_id)
        );
        if (!isValidSupplier) {
          setNewProduct({ ...newProduct, supplier_id: '' });
        }
      }
    } else {
      setFilteredSuppliers([]);
    }
  }, [newProduct.category_id, supplierList]);

  const loadData = async () => {
    try {
      const [productsRes, categoriesRes, suppliersRes] = await Promise.all([
        products.getAll(),
        categories.getAll(),
        suppliers.getAll(),
      ]);
      setProductList(productsRes.data.products);
      setCategoryList(categoriesRes.data.categories);
      setSupplierList(suppliersRes.data.suppliers);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddProduct = async (e) => {
    e.preventDefault();
    const loadingToast = toast.loading('Adding product...');
    try {
      await products.add({
        ...newProduct,
        price: parseFloat(newProduct.price),
        stock_quantity: parseInt(newProduct.stock_quantity),
        category_id: parseInt(newProduct.category_id),
        supplier_id: parseInt(newProduct.supplier_id),
        low_stock_threshold: parseInt(newProduct.low_stock_threshold),
      });
      toast.success('Product added successfully!', { id: loadingToast });
      setShowAddForm(false);
      setNewProduct({
        name: '',
        barcode: '',
        price: '',
        stock_quantity: '',
        category_id: '',
        supplier_id: '',
        low_stock_threshold: 10,
      });
      loadData();
    } catch (error) {
      toast.error('Failed to add product: ' + (error.response?.data?.detail || error.message), { id: loadingToast });
    }
  };

  const handleRestock = async (e) => {
    e.preventDefault();
    const loadingToast = toast.loading('Updating stock...');
    try {
      await products.updateStock(selectedProduct.product_id, parseInt(restockQuantity));
      toast.success(`Stock updated! Added ${restockQuantity} units to ${selectedProduct.name}`, { id: loadingToast });
      setShowRestockForm(false);
      setSelectedProduct(null);
      setRestockQuantity('');
      loadData();
    } catch (error) {
      toast.error('Failed to update stock: ' + (error.response?.data?.detail || error.message), { id: loadingToast });
    }
  };

  const handleDeleteClick = (product) => {
    setDeleteConfirm({
      isOpen: true,
      productId: product.product_id,
      productName: product.name
    });
  };

  const handleDeleteConfirm = async () => {
    const loadingToast = toast.loading('Deleting product...');
    try {
      await products.delete(deleteConfirm.productId);
      toast.success(`Product "${deleteConfirm.productName}" deleted successfully!`, { id: loadingToast });
      setDeleteConfirm({ isOpen: false, productId: null, productName: '' });
      loadData();
    } catch (error) {
      toast.error('Failed to delete product: ' + (error.response?.data?.detail || error.message), { id: loadingToast });
    }
  };

  const filteredProducts = productList.filter(product =>
    product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.barcode.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="products-page">
        <div className="page-header">
          <h1>Products</h1>
        </div>
        <TableSkeleton rows={8} columns={7} />
      </div>
    );
  }

  return (
    <motion.div 
      className="products-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <ConfirmModal
        isOpen={deleteConfirm.isOpen}
        onClose={() => setDeleteConfirm({ isOpen: false, productId: null, productName: '' })}
        onConfirm={handleDeleteConfirm}
        title="Delete Product?"
        message={`Are you sure you want to delete "${deleteConfirm.productName}"? This action cannot be undone.`}
        type="danger"
      />
      <div className="page-header">
        <div className="page-title">
          <Package size={32} />
          <h1>Products</h1>
        </div>
        <div className="page-actions">
          <div className="search-bar">
            <Search size={20} />
            <input
              type="text"
              placeholder="Search products by name or barcode..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          {user?.role === 'ADMIN' && (
            <motion.button 
              className="btn-primary" 
              onClick={() => setShowAddForm(true)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Plus size={20} />
              Add Product
            </motion.button>
          )}
        </div>
      </div>

      <div className="products-table-container">
        <table className="products-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Barcode</th>
              <th>Price</th>
              <th>Stock</th>
              <th>Threshold</th>
              <th>Category</th>
              <th>Supplier</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredProducts.map((product) => (
              <tr key={product.product_id} className={product.stock_quantity <= product.low_stock_threshold ? 'low-stock' : ''}>
                <td>{product.product_id}</td>
                <td><strong>{product.name}</strong></td>
                <td>{product.barcode || '-'}</td>
                <td>₹{product.price.toFixed(2)}</td>
                <td>
                  <span className={`stock-badge ${product.stock_quantity <= product.low_stock_threshold ? 'low' : 'normal'}`}>
                    {product.stock_quantity}
                  </span>
                </td>
                <td>{product.low_stock_threshold}</td>
                <td>{product.category}</td>
                <td>{product.supplier}</td>
                <td>
                  {(user?.role === 'ADMIN' || user?.role === 'MANAGER') && (
                    <button 
                      className="btn-small"
                      onClick={() => {
                        setSelectedProduct(product);
                        setShowRestockForm(true);
                      }}
                    >
                      <RefreshCw size={16} />
                      Restock
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showAddForm && (
        <div className="modal" onClick={() => setShowAddForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Add New Product</h2>
              <button className="modal-close" onClick={() => setShowAddForm(false)}>
                <X size={24} />
              </button>
            </div>
            <form onSubmit={handleAddProduct}>
              <div className="form-group">
                <label>Product Name *</label>
                <input
                  type="text"
                  value={newProduct.name}
                  onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
                  required
                  placeholder="Enter product name"
                />
              </div>
              
              <div className="form-group">
                <label>Barcode</label>
                <input
                  type="text"
                  value={newProduct.barcode}
                  onChange={(e) => setNewProduct({ ...newProduct, barcode: e.target.value })}
                  placeholder="Enter barcode (optional)"
                />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Price *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newProduct.price}
                    onChange={(e) => setNewProduct({ ...newProduct, price: e.target.value })}
                    required
                    placeholder="0.00"
                  />
                </div>
                
                <div className="form-group">
                  <label>Stock Quantity *</label>
                  <input
                    type="number"
                    value={newProduct.stock_quantity}
                    onChange={(e) => setNewProduct({ ...newProduct, stock_quantity: e.target.value })}
                    required
                    placeholder="0"
                  />
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label>Category *</label>
                  <select
                    value={newProduct.category_id}
                    onChange={(e) => setNewProduct({ ...newProduct, category_id: e.target.value, supplier_id: '' })}
                    required
                  >
                    <option value="">Select Category</option>
                    {categoryList.map((cat) => (
                      <option key={cat.category_id} value={cat.category_id}>
                        {cat.name}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="form-group">
                  <label>Supplier *</label>
                  <select
                    value={newProduct.supplier_id}
                    onChange={(e) => setNewProduct({ ...newProduct, supplier_id: e.target.value })}
                    required
                    disabled={!newProduct.category_id}
                  >
                    <option value="">
                      {!newProduct.category_id 
                        ? 'Select Category First' 
                        : filteredSuppliers.length === 0 
                        ? 'No suppliers for this category'
                        : 'Select Supplier'}
                    </option>
                    {filteredSuppliers.map((sup) => (
                      <option key={sup.supplier_id} value={sup.supplier_id}>
                        {sup.name}
                      </option>
                    ))}
                  </select>
                  {newProduct.category_id && filteredSuppliers.length === 0 && (
                    <small style={{ color: '#ff6b6b', marginTop: '4px', display: 'block' }}>
                      ⚠️ No suppliers available for this category. Please add a supplier first.
                    </small>
                  )}
                </div>
              </div>
              
              <div className="form-group">
                <label>Low Stock Threshold</label>
                <input
                  type="number"
                  value={newProduct.low_stock_threshold}
                  onChange={(e) => setNewProduct({ ...newProduct, low_stock_threshold: e.target.value })}
                  placeholder="10"
                />
              </div>
              
              <div className="modal-actions">
                <button type="submit" className="btn-primary">
                  <Plus size={18} />
                  Add Product
                </button>
                <button type="button" className="btn-secondary" onClick={() => setShowAddForm(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showRestockForm && selectedProduct && (
        <div className="modal" onClick={() => setShowRestockForm(false)}>
          <div className="modal-content modal-small" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Restock Product</h2>
              <button className="modal-close" onClick={() => setShowRestockForm(false)}>
                <X size={24} />
              </button>
            </div>
            <div className="restock-info">
              <p><strong>Product:</strong> {selectedProduct.name}</p>
              <p><strong>Current Stock:</strong> {selectedProduct.stock_quantity}</p>
            </div>
            <form onSubmit={handleRestock}>
              <div className="form-group">
                <label>Add Quantity</label>
                <input
                  type="number"
                  value={restockQuantity}
                  onChange={(e) => setRestockQuantity(e.target.value)}
                  required
                  min="1"
                  placeholder="Enter quantity to add"
                  autoFocus
                />
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn-primary">
                  <RefreshCw size={18} />
                  Update Stock
                </button>
                <button type="button" className="btn-secondary" onClick={() => setShowRestockForm(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </motion.div>
  );
}

export default Products;
