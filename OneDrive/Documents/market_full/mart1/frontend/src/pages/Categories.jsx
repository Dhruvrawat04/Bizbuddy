import { useState, useEffect } from 'react';
import { categories } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { FolderOpen, Plus, X, Edit2, Trash2, Tag, FileText, Package } from 'lucide-react';
import '../styles/Categories.css';

function Categories() {
  const { user } = useAuth();
  const [categoryList, setCategoryList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [currentCategory, setCurrentCategory] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const res = await categories.getAll();
      setCategoryList(res.data.categories);
    } catch (error) {
      console.error('Failed to load categories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editMode) {
        await categories.update(currentCategory.category_id, formData);
        alert('Category updated successfully!');
      } else {
        await categories.add(formData);
        alert('Category added successfully!');
      }
      resetForm();
      loadCategories();
    } catch (error) {
      alert('Operation failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = (category) => {
    setFormData({
      name: category.name,
      description: category.description || '',
    });
    setCurrentCategory(category);
    setEditMode(true);
    setShowForm(true);
  };

  const handleDelete = async (categoryId) => {
    if (!window.confirm('Are you sure you want to delete this category?')) return;
    try {
      await categories.delete(categoryId);
      alert('Category deleted successfully!');
      loadCategories();
    } catch (error) {
      alert('Failed to delete category: ' + (error.response?.data?.detail || error.message));
    }
  };

  const resetForm = () => {
    setFormData({ name: '', description: '' });
    setShowForm(false);
    setEditMode(false);
    setCurrentCategory(null);
  };

  if (loading) {
    return <div className="loading">Loading categories...</div>;
  }

  return (
    <div className="categories-page">
      <div className="page-header">
        <h1><FolderOpen size={32} style={{ marginRight: '12px', verticalAlign: 'middle' }} />Categories</h1>
        {user?.role === 'ADMIN' && (
          <button className="btn-primary" onClick={() => setShowForm(true)}>
            <Plus size={20} style={{ marginRight: '6px' }} />
            Add Category
          </button>
        )}
      </div>

      {showForm && (
        <div className="modal" onClick={resetForm}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editMode ? 'Edit Category' : 'Add New Category'}</h2>
              <button className="modal-close" onClick={resetForm}>
                <X size={24} />
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>
                  <Tag size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                  Category Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Enter category name"
                  required
                />
              </div>
              <div className="form-group">
                <label>
                  <FileText size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows="4"
                  placeholder="Enter category description (optional)"
                />
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn-primary">
                  <Plus size={18} />
                  {editMode ? 'Update' : 'Add'} Category
                </button>
                <button type="button" className="btn-secondary" onClick={resetForm}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="categories-grid">
        {categoryList.map((category) => (
          <div key={category.category_id} className="category-card">
            <div className="category-icon">
              <Package size={40} strokeWidth={1.5} />
            </div>
            <h3>{category.name}</h3>
            <p className="category-description">{category.description || 'No description provided'}</p>
            {user?.role === 'ADMIN' && (
              <div className="category-actions">
                <button className="btn-edit" onClick={() => handleEdit(category)}>
                  <Edit2 size={16} /> Edit
                </button>
                <button className="btn-delete" onClick={() => handleDelete(category.category_id)}>
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

export default Categories;
