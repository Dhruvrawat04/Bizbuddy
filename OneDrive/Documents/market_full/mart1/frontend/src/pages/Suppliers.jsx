import { useState, useEffect } from 'react';
import { suppliers, categories } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Building2, Plus, X, Edit2, Trash2, Phone, Mail, MapPin, Tag } from 'lucide-react';
import '../styles/Suppliers.css';

function Suppliers() {
  const { user } = useAuth();
  const [supplierList, setSupplierList] = useState([]);
  const [categoryList, setCategoryList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [currentSupplier, setCurrentSupplier] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    address: '',
    category_id: '',
  });

  useEffect(() => {
    loadSuppliers();
  }, []);

  const loadSuppliers = async () => {
    try {
      const [suppliersRes, categoriesRes] = await Promise.all([
        suppliers.getAll(),
        categories.getAll(),
      ]);
      setSupplierList(suppliersRes.data.suppliers);
      setCategoryList(categoriesRes.data.categories);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editMode) {
        await suppliers.update(currentSupplier.supplier_id, formData);
        alert('Supplier updated successfully!');
      } else {
        await suppliers.add(formData);
        alert('Supplier added successfully!');
      }
      resetForm();
      loadSuppliers();
    } catch (error) {
      alert('Operation failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = (supplier) => {
    setFormData({
      name: supplier.name,
      phone: supplier.phone || '',
      email: supplier.email || '',
      address: supplier.address || '',
      category_id: supplier.category_id || '',
    });
    setCurrentSupplier(supplier);
    setEditMode(true);
    setShowForm(true);
  };

  const handleDelete = async (supplierId) => {
    if (!window.confirm('Are you sure you want to delete this supplier?')) return;
    try {
      await suppliers.delete(supplierId);
      alert('Supplier deleted successfully!');
      loadSuppliers();
    } catch (error) {
      alert('Failed to delete supplier: ' + (error.response?.data?.detail || error.message));
    }
  };

  const resetForm = () => {
    setFormData({ name: '', phone: '', email: '', address: '', category_id: '' });
    setShowForm(false);
    setEditMode(false);
    setCurrentSupplier(null);
  };

  if (loading) {
    return <div className="loading">Loading suppliers...</div>;
  }

  return (
    <div className="suppliers-page">
      <div className="page-header">
        <h1><Building2 size={32} style={{ marginRight: '12px', verticalAlign: 'middle' }} />Suppliers</h1>
        {user?.role === 'ADMIN' && (
          <button className="btn-primary" onClick={() => setShowForm(true)}>
            <Plus size={20} style={{ marginRight: '6px' }} />
            Add Supplier
          </button>
        )}
      </div>

      {showForm && (
        <div className="modal" onClick={resetForm}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editMode ? 'Edit Supplier' : 'Add New Supplier'}</h2>
              <button className="modal-close" onClick={resetForm}>
                <X size={24} />
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>
                  <Building2 size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                  Supplier Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Enter supplier name"
                  required
                />
              </div>

              <div className="form-group">
                <label>
                  <Tag size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                  Category *
                </label>
                <select
                  value={formData.category_id}
                  onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                  required
                >
                  <option value="">Select Category</option>
                  {categoryList.map((cat) => (
                    <option key={cat.category_id} value={cat.category_id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
                <small style={{ color: '#999', marginTop: '4px', display: 'block' }}>
                  Supplier can only add products in this category
                </small>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>
                    <Phone size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                    Phone
                  </label>
                  <input
                    type="text"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="Enter phone number"
                  />
                </div>
                <div className="form-group">
                  <label>
                    <Mail size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                    Email
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="Enter email address"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>
                  <MapPin size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                  Address
                </label>
                <textarea
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  rows="3"
                  placeholder="Enter full address"
                />
              </div>

              <div className="modal-actions">
                <button type="submit" className="btn-primary">
                  <Plus size={18} />
                  {editMode ? 'Update' : 'Add'} Supplier
                </button>
                <button type="button" className="btn-secondary" onClick={resetForm}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="suppliers-grid">
        {supplierList.map((supplier) => (
          <div key={supplier.supplier_id} className="supplier-card">
            <div className="supplier-header">
              <h3><Building2 size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />{supplier.name}</h3>
              <div className="reliability-badge">
                Score: {supplier.reliability_score || 100}
              </div>
            </div>
            <div className="supplier-details">
              {supplier.category_name && (
                <p><Tag size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} /><strong>Category:</strong> {supplier.category_name}</p>
              )}
              <p><Phone size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} /><strong>Phone:</strong> {supplier.phone || 'N/A'}</p>
              <p><Mail size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} /><strong>Email:</strong> {supplier.email || 'N/A'}</p>
              <p><MapPin size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} /><strong>Address:</strong> {supplier.address || 'N/A'}</p>
            </div>
            {user?.role === 'ADMIN' && (
              <div className="supplier-actions">
                <button className="btn-edit" onClick={() => handleEdit(supplier)}>
                  <Edit2 size={16} /> Edit
                </button>
                <button className="btn-delete" onClick={() => handleDelete(supplier.supplier_id)}>
                  <Trash2 size={16} /> Delete
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default Suppliers;
