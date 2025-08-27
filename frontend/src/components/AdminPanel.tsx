import React, { useState, useEffect } from 'react';
import { Context, ExcludedTerm, adminAPI, settingsAPI } from '../services/api';
import AdminDashboard from './AdminDashboard';

interface AdminPanelProps {
  isVisible: boolean;
  onClose: () => void;
  isAdmin: boolean;
}

const AdminPanel: React.FC<AdminPanelProps> = ({ isVisible, onClose, isAdmin }) => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'contexts' | 'terms'>('dashboard');
  const [contexts, setContexts] = useState<Context[]>([]);
  const [excludedTerms, setExcludedTerms] = useState<ExcludedTerm[]>([]);
  const [loading, setLoading] = useState(false);

  // Context form
  const [newContextName, setNewContextName] = useState('');
  const [newContextPrompt, setNewContextPrompt] = useState('');

  // Term form
  const [newTerm, setNewTerm] = useState('');

  useEffect(() => {
    console.log('AdminPanel useEffect triggered:', { isVisible, isAdmin });
    if (isVisible) {
      console.log('Starting to load data...');
      loadContexts();
      loadExcludedTerms();
    }
  }, [isVisible, isAdmin]);

  const loadContexts = async () => {
    console.log('loadContexts called, isAdmin:', isAdmin);
    if (!isAdmin) {
      console.log('User is not admin, skipping contexts load');
      return;
    }
    setLoading(true);
    try {
      console.log('Making API call to get contexts...');
      console.log('Auth token exists:', !!localStorage.getItem('authToken'));
      const response = await adminAPI.getContexts();
      console.log('Contexts response:', response);
      console.log('Contexts response.data:', response.data);
      console.log('Is response.data an array?', Array.isArray(response.data));
      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);
      // Ensure it's an array
      const contextsData = Array.isArray(response.data) ? response.data : [];
      console.log('Setting contexts:', contextsData);
      setContexts(contextsData);
    } catch (error: any) {
      console.error('Error loading contexts:', error);
      console.error('Error details:', error.response?.data, error.response?.status);
      console.error('Full error object:', error);
      setContexts([]);
    } finally {
      setLoading(false);
    }
  };

  const loadExcludedTerms = async () => {
    setLoading(true);
    try {
      const response = await settingsAPI.getExcludedTerms();
      console.log('Excluded terms response:', response.data);
      // Ensure it's an array
      setExcludedTerms(Array.isArray(response.data) ? response.data : []);
    } catch (error: any) {
      console.error('Error loading excluded terms:', error);
      setExcludedTerms([]);
    } finally {
      setLoading(false);
    }
  };

  const createContext = async () => {
    if (!newContextName.trim() || !newContextPrompt.trim()) return;
    
    try {
      const response = await adminAPI.createContext({
        nombre: newContextName,
        prompt: newContextPrompt
      });
      if (response.data.success) {
        setNewContextName('');
        setNewContextPrompt('');
        loadContexts();
        alert('Contexto creado exitosamente');
      }
    } catch (error: any) {
      console.error('Error creating context:', error);
      alert('Error al crear contexto');
    }
  };

  const toggleContext = async (contextId: number, isActive: boolean) => {
    try {
      if (isActive) {
        await adminAPI.deactivateContext(contextId);
      } else {
        await adminAPI.activateContext(contextId);
      }
      loadContexts();
    } catch (error: any) {
      console.error('Error toggling context:', error);
      alert('Error al cambiar estado del contexto');
    }
  };

  const deleteContext = async (contextId: number) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar este contexto?')) return;
    
    try {
      await adminAPI.deleteContext(contextId);
      loadContexts();
      alert('Contexto eliminado');
    } catch (error: any) {
      console.error('Error deleting context:', error);
      alert('Error al eliminar contexto');
    }
  };

  const addExcludedTerm = async () => {
    if (!newTerm.trim()) return;
    
    try {
      const response = await settingsAPI.addExcludedTerm({ termino: newTerm });
      if (response.data.success) {
        setNewTerm('');
        loadExcludedTerms();
        alert('Término excluido agregado');
      }
    } catch (error: any) {
      console.error('Error adding excluded term:', error);
      alert('Error al agregar término');
    }
  };

  const deleteExcludedTerm = async (termId: number) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar este término?')) return;
    
    try {
      await settingsAPI.deleteExcludedTerm(termId);
      loadExcludedTerms();
      alert('Término eliminado');
    } catch (error: any) {
      console.error('Error deleting excluded term:', error);
      alert('Error al eliminar término');
    }
  };

  if (!isVisible) return null;

  return (
    <div className="modal show d-block" tabIndex={-1}>
      <div className="modal-dialog modal-xl">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">
              {isAdmin ? 'Panel de Administración' : 'Configuración'}
            </h5>
            <button 
              type="button" 
              className="btn-close" 
              onClick={onClose}
            ></button>
          </div>
          <div className="modal-body">
            {/* Tabs */}
            <ul className="nav nav-tabs mb-3">
              {isAdmin && (
                <li className="nav-item">
                  <button
                    className={`nav-link ${activeTab === 'dashboard' ? 'active' : ''}`}
                    onClick={() => setActiveTab('dashboard')}
                  >
                    📊 Dashboard
                  </button>
                </li>
              )}
              {isAdmin && (
                <li className="nav-item">
                  <button
                    className={`nav-link ${activeTab === 'contexts' ? 'active' : ''}`}
                    onClick={() => setActiveTab('contexts')}
                  >
                    🧠 Contextos IA
                  </button>
                </li>
              )}
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === 'terms' ? 'active' : ''}`}
                  onClick={() => setActiveTab('terms')}
                >
                  🔒 Términos Excluidos
                </button>
              </li>
            </ul>

            {/* Dashboard Tab */}
            {isAdmin && activeTab === 'dashboard' && (
              <div>
                <AdminDashboard />
              </div>
            )}

            {/* Contexts Tab */}
            {isAdmin && activeTab === 'contexts' && (
              <div>
                <h6>Gestión de Contextos de IA</h6>
                
                {/* Create Context Form */}
                <div className="card mb-3">
                  <div className="card-header">Crear Nuevo Contexto</div>
                  <div className="card-body">
                    <div className="mb-3">
                      <label className="form-label">Nombre del Contexto</label>
                      <input
                        type="text"
                        className="form-control"
                        value={newContextName}
                        onChange={(e) => setNewContextName(e.target.value)}
                        placeholder="Ej: Contexto de Finanzas"
                      />
                    </div>
                    <div className="mb-3">
                      <label className="form-label">Prompt del Sistema</label>
                      <textarea
                        className="form-control"
                        rows={4}
                        value={newContextPrompt}
                        onChange={(e) => setNewContextPrompt(e.target.value)}
                        placeholder="Instrucciones para el comportamiento de la IA..."
                      />
                    </div>
                    <button
                      className="btn btn-primary"
                      onClick={createContext}
                      disabled={!newContextName.trim() || !newContextPrompt.trim()}
                    >
                      Crear Contexto
                    </button>
                  </div>
                </div>

                {/* Contexts List */}
                <div className="card">
                  <div className="card-header">Contextos Existentes</div>
                  <div className="card-body">
                    {loading ? (
                      <div className="text-center">
                        <div className="spinner-border" role="status">
                          <span className="visually-hidden">Cargando...</span>
                        </div>
                      </div>
                    ) : (!Array.isArray(contexts) || contexts.length === 0) ? (
                      <p className="text-muted">No hay contextos configurados</p>
                    ) : (
                      <div className="table-responsive">
                        <table className="table">
                          <thead>
                            <tr>
                              <th>Nombre</th>
                              <th>Estado</th>
                              <th>Fecha Creación</th>
                              <th>Acciones</th>
                            </tr>
                          </thead>
                          <tbody>
                            {contexts.filter(context => context && context.id).map((context) => (
                              <tr key={context.id}>
                                <td>{context.nombre}</td>
                                <td>
                                  <span className={`badge ${context.activo ? 'bg-success' : 'bg-secondary'}`}>
                                    {context.activo ? 'Activo' : 'Inactivo'}
                                  </span>
                                </td>
                                <td>{new Date(context.fecha_creacion).toLocaleDateString('es-ES')}</td>
                                <td>
                                  <div className="btn-group" role="group">
                                    <button
                                      className={`btn btn-sm ${context.activo ? 'btn-warning' : 'btn-success'}`}
                                      onClick={() => toggleContext(context.id, context.activo)}
                                    >
                                      {context.activo ? 'Desactivar' : 'Activar'}
                                    </button>
                                    <button
                                      className="btn btn-sm btn-danger"
                                      onClick={() => deleteContext(context.id)}
                                    >
                                      Eliminar
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Excluded Terms Tab */}
            {activeTab === 'terms' && (
              <div>
                <h6>Gestión de Términos Excluidos</h6>
                
                {/* Add Term Form */}
                <div className="card mb-3">
                  <div className="card-header">Agregar Término Excluido</div>
                  <div className="card-body">
                    <div className="input-group">
                      <input
                        type="text"
                        className="form-control"
                        value={newTerm}
                        onChange={(e) => setNewTerm(e.target.value)}
                        placeholder="Término a excluir de los resultados"
                        onKeyPress={(e) => e.key === 'Enter' && addExcludedTerm()}
                      />
                      <button
                        className="btn btn-primary"
                        onClick={addExcludedTerm}
                        disabled={!newTerm.trim()}
                      >
                        Agregar
                      </button>
                    </div>
                    <small className="form-text text-muted">
                      Los términos excluidos se filtrarán automáticamente de los resultados de las consultas.
                    </small>
                  </div>
                </div>

                {/* Terms List */}
                <div className="card">
                  <div className="card-header">Términos Excluidos Actuales</div>
                  <div className="card-body">
                    {loading ? (
                      <div className="text-center">
                        <div className="spinner-border" role="status">
                          <span className="visually-hidden">Cargando...</span>
                        </div>
                      </div>
                    ) : (!Array.isArray(excludedTerms) || excludedTerms.length === 0) ? (
                      <p className="text-muted">No hay términos excluidos configurados</p>
                    ) : (
                      <div className="table-responsive">
                        <table className="table">
                          <thead>
                            <tr>
                              <th>Término</th>
                              <th>Fecha Agregado</th>
                              <th>Acciones</th>
                            </tr>
                          </thead>
                          <tbody>
                            {excludedTerms.filter(term => term && term.id).map((term) => (
                              <tr key={term.id}>
                                <td><code>{term.termino}</code></td>
                                <td>{new Date(term.fecha_creacion).toLocaleDateString('es-ES')}</td>
                                <td>
                                  <button
                                    className="btn btn-sm btn-danger"
                                    onClick={() => deleteExcludedTerm(term.id)}
                                  >
                                    Eliminar
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;