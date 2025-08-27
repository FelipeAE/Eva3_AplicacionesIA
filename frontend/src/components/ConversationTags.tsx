import React, { useState, useEffect } from 'react';
import { SessionDetail } from '../services/api';

interface ConversationTagsProps {
  isVisible: boolean;
  onClose: () => void;
  session: SessionDetail | null;
  onTagsUpdated?: (tags: string[]) => void;
}

interface TagCategory {
  name: string;
  color: string;
  icon: string;
  predefinedTags: string[];
}

const TAG_CATEGORIES: TagCategory[] = [
  {
    name: 'Área',
    color: 'primary',
    icon: '🏢',
    predefinedTags: ['RRHH', 'Finanzas', 'Legal', 'Administración', 'Operaciones', 'TI']
  },
  {
    name: 'Tipo de Consulta',
    color: 'success',
    icon: '❓',
    predefinedTags: ['Consulta', 'Reporte', 'Análisis', 'Búsqueda', 'Verificación']
  },
  {
    name: 'Urgencia',
    color: 'warning',
    icon: '⚡',
    predefinedTags: ['Urgente', 'Alta', 'Media', 'Baja', 'No urgente']
  },
  {
    name: 'Estado',
    color: 'info',
    icon: '📋',
    predefinedTags: ['Pendiente', 'En proceso', 'Completado', 'Revisión', 'Archivado']
  },
  {
    name: 'Tema',
    color: 'secondary',
    icon: '📌',
    predefinedTags: ['Contratos', 'Pagos', 'Personal', 'Honorarios', 'Viáticos', 'Funciones']
  }
];

const ConversationTags: React.FC<ConversationTagsProps> = ({ 
  isVisible, 
  onClose, 
  session,
  onTagsUpdated 
}) => {
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [customTag, setCustomTag] = useState('');
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (session && session.session.id) {
      loadSessionTags(session.session.id);
    }
  }, [session]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isVisible) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isVisible, onClose]);

  const loadSessionTags = (sessionId: number) => {
    // Load tags from localStorage
    const storedTags = localStorage.getItem(`session-tags-${sessionId}`);
    if (storedTags) {
      setSelectedTags(JSON.parse(storedTags));
    } else {
      setSelectedTags([]);
    }
  };

  const saveSessionTags = (sessionId: number, tags: string[]) => {
    localStorage.setItem(`session-tags-${sessionId}`, JSON.stringify(tags));
  };

  const handleTagToggle = (tag: string) => {
    const newTags = selectedTags.includes(tag)
      ? selectedTags.filter(t => t !== tag)
      : [...selectedTags, tag];
    
    setSelectedTags(newTags);
    
    if (session) {
      saveSessionTags(session.session.id, newTags);
      onTagsUpdated?.(newTags);
    }
  };

  const handleAddCustomTag = () => {
    const trimmedTag = customTag.trim();
    if (trimmedTag && !selectedTags.includes(trimmedTag)) {
      const newTags = [...selectedTags, trimmedTag];
      setSelectedTags(newTags);
      setCustomTag('');
      
      if (session) {
        saveSessionTags(session.session.id, newTags);
        onTagsUpdated?.(newTags);
      }
    }
  };

  const handleClearAllTags = () => {
    if (window.confirm('¿Eliminar todas las etiquetas de esta conversación?')) {
      setSelectedTags([]);
      if (session) {
        saveSessionTags(session.session.id, []);
        onTagsUpdated?.([]);
      }
    }
  };

  const getFilteredCategories = () => {
    if (!searchTerm) return TAG_CATEGORIES;
    
    return TAG_CATEGORIES.map(category => ({
      ...category,
      predefinedTags: category.predefinedTags.filter(tag => 
        tag.toLowerCase().includes(searchTerm.toLowerCase())
      )
    })).filter(category => category.predefinedTags.length > 0);
  };

  const getAllPredefinedTags = () => {
    return TAG_CATEGORIES.flatMap(category => category.predefinedTags);
  };

  const getPopularTags = () => {
    // Get all tags from all sessions
    const allSessionTags: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('session-tags-')) {
        try {
          const tags = JSON.parse(localStorage.getItem(key) || '[]');
          allSessionTags.push(...tags);
        } catch (e) {
          // Ignore invalid JSON
        }
      }
    }
    
    // Count frequency
    const tagCounts: { [key: string]: number } = {};
    allSessionTags.forEach(tag => {
      tagCounts[tag] = (tagCounts[tag] || 0) + 1;
    });
    
    // Sort by frequency and return top 10
    return Object.entries(tagCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10)
      .map(([tag]) => tag);
  };

  if (!isVisible) return null;

  const filteredCategories = getFilteredCategories();
  const popularTags = getPopularTags();

  return (
    <div className="modal show d-block" tabIndex={-1}>
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">🏷️ Etiquetas de Conversación</h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <div className="modal-body">
            {session && (
              <div className="mb-3">
                <h6 className="text-muted">
                  Conversación: {session.session.name || `Sesión ${session.session.id}`}
                </h6>
              </div>
            )}

            {/* Current tags */}
            <div className="mb-4">
              <h6>Etiquetas Actuales</h6>
              <div className="d-flex flex-wrap gap-2 mb-2">
                {selectedTags.length > 0 ? (
                  selectedTags.map((tag) => (
                    <span 
                      key={tag} 
                      className="badge bg-primary d-flex align-items-center gap-1"
                      style={{ fontSize: '0.9rem', padding: '0.5rem' }}
                    >
                      {tag}
                      <button
                        type="button"
                        className="btn-close btn-close-white"
                        style={{ fontSize: '0.6rem' }}
                        onClick={() => handleTagToggle(tag)}
                        title={`Quitar etiqueta "${tag}"`}
                      ></button>
                    </span>
                  ))
                ) : (
                  <span className="text-muted">No hay etiquetas asignadas</span>
                )}
              </div>
              {selectedTags.length > 0 && (
                <button 
                  className="btn btn-outline-danger btn-sm"
                  onClick={handleClearAllTags}
                >
                  🗑️ Eliminar todas
                </button>
              )}
            </div>

            {/* Search */}
            <div className="mb-3">
              <input
                type="text"
                className="form-control"
                placeholder="🔍 Buscar etiquetas..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            {/* Popular tags */}
            {popularTags.length > 0 && !searchTerm && (
              <div className="mb-4">
                <h6>🔥 Etiquetas Populares</h6>
                <div className="d-flex flex-wrap gap-2">
                  {popularTags.map((tag) => (
                    <button
                      key={tag}
                      className={`btn btn-sm ${
                        selectedTags.includes(tag) ? 'btn-warning' : 'btn-outline-warning'
                      }`}
                      onClick={() => handleTagToggle(tag)}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Category tabs */}
            <div className="mb-3">
              <ul className="nav nav-pills nav-fill">
                <li className="nav-item">
                  <button 
                    className={`nav-link ${!activeCategory ? 'active' : ''}`}
                    onClick={() => setActiveCategory(null)}
                  >
                    Todas
                  </button>
                </li>
                {filteredCategories.map((category) => (
                  <li key={category.name} className="nav-item">
                    <button 
                      className={`nav-link ${activeCategory === category.name ? 'active' : ''}`}
                      onClick={() => setActiveCategory(category.name)}
                    >
                      {category.icon} {category.name}
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            {/* Tag categories */}
            <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
              {filteredCategories
                .filter(category => !activeCategory || category.name === activeCategory)
                .map((category) => (
                <div key={category.name} className="mb-3">
                  <h6 className={`text-${category.color}`}>
                    {category.icon} {category.name}
                  </h6>
                  <div className="d-flex flex-wrap gap-2">
                    {category.predefinedTags.map((tag) => (
                      <button
                        key={tag}
                        className={`btn btn-sm ${
                          selectedTags.includes(tag) 
                            ? `btn-${category.color}` 
                            : `btn-outline-${category.color}`
                        }`}
                        onClick={() => handleTagToggle(tag)}
                      >
                        {tag}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Custom tag input */}
            <div className="mt-4">
              <h6>Etiqueta Personalizada</h6>
              <div className="input-group">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Escribe una etiqueta personalizada..."
                  value={customTag}
                  onChange={(e) => setCustomTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddCustomTag()}
                />
                <button 
                  className="btn btn-outline-secondary"
                  onClick={handleAddCustomTag}
                  disabled={!customTag.trim() || selectedTags.includes(customTag.trim())}
                >
                  ➕ Agregar
                </button>
              </div>
              <small className="text-muted">
                Presiona Enter o haz clic en "Agregar" para crear una etiqueta personalizada
              </small>
            </div>
          </div>
          <div className="modal-footer">
            <div className="me-auto">
              <small className="text-muted">
                {selectedTags.length} etiqueta{selectedTags.length !== 1 ? 's' : ''} seleccionada{selectedTags.length !== 1 ? 's' : ''}
              </small>
            </div>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConversationTags;