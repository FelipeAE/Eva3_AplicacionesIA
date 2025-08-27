import React, { useState, useEffect } from 'react';
import { ChatSession, chatAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import ThemeToggle from './ThemeToggle';

interface ChatSidebarProps {
  onSessionSelect: (sessionId: number) => void;
  selectedSessionId: number | null;
  onShowAdminPanel?: () => void;
  isAdmin?: boolean;
  isMobile?: boolean;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({ onSessionSelect, selectedSessionId, onShowAdminPanel, isAdmin, isMobile = false }) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewSessionModal, setShowNewSessionModal] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const { user, logout } = useAuth();

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const response = await chatAPI.getSessions();
      setSessions(response.data);
    } catch (error) {
      console.error('Error loading sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const createSession = async () => {
    if (!newSessionName.trim()) return;
    
    try {
      const response = await chatAPI.createSession();
      // After creating, fetch the updated sessions list
      const sessionsResponse = await chatAPI.getSessions();
      setSessions(sessionsResponse.data);
      setNewSessionName('');
      setShowNewSessionModal(false);
      onSessionSelect(response.data.session_id);
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const deleteSession = async (sessionId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (!window.confirm('¿Está seguro de que desea eliminar esta sesión?')) {
      return;
    }

    try {
      await chatAPI.deleteSession(sessionId);
      setSessions(sessions.filter(s => s.id !== sessionId));
      if (selectedSessionId === sessionId) {
        onSessionSelect(sessions.length > 1 ? sessions[0].id : 0);
      }
    } catch (error) {
      console.error('Error deleting session:', error);
      alert('No se puede eliminar la sesión. Puede tener preguntas bloqueadas.');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="d-flex flex-column h-100 bg-light border-end">
      {/* Desktop header - hidden on mobile when in mobile mode */}
      {!isMobile && (
        <div className="p-3 border-bottom bg-white">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h5 className="mb-0">Chatbot RRHH</h5>
            <div className="dropdown">
              <button className="btn btn-sm btn-outline-secondary dropdown-toggle" 
                      type="button" data-bs-toggle="dropdown">
                {user?.username}
              </button>
              <ul className="dropdown-menu">
                {(isAdmin || onShowAdminPanel) && (
                  <>
                    <li>
                      <button 
                        className="dropdown-item" 
                        onClick={onShowAdminPanel}
                      >
                        {isAdmin ? '⚙️ Administración' : '⚙️ Configuración'}
                      </button>
                    </li>
                    <li><hr className="dropdown-divider" /></li>
                  </>
                )}
                <li>
                  <div className="dropdown-item-text d-flex align-items-center justify-content-between">
                    <span>🎨 Tema</span>
                    <ThemeToggle />
                  </div>
                </li>
                <li><hr className="dropdown-divider" /></li>
                <li>
                  <button className="dropdown-item" onClick={logout}>
                    Cerrar Sesión
                  </button>
                </li>
              </ul>
            </div>
          </div>
          <button 
            className="btn btn-primary btn-sm w-100"
            onClick={() => setShowNewSessionModal(true)}
          >
            Nueva Conversación
          </button>
        </div>
      )}
      
      {/* Mobile-only new conversation button */}
      {isMobile && (
        <div className="p-2">
          <button 
            className="btn btn-primary btn-sm w-100"
            onClick={() => setShowNewSessionModal(true)}
          >
            + Nueva Conversación
          </button>
        </div>
      )}

      <div className="flex-grow-1 overflow-auto">
        {loading ? (
          <div className="p-3 text-center">
            <div className="spinner-border spinner-border-sm" role="status">
              <span className="visually-hidden">Cargando...</span>
            </div>
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-3 text-center text-muted">
            No hay conversaciones
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              className={`d-flex align-items-center p-2 m-2 rounded cursor-pointer ${
                selectedSessionId === session.id ? 'bg-primary text-white' : 'bg-white'
              }`}
              onClick={() => onSessionSelect(session.id)}
              style={{ cursor: 'pointer' }}
            >
              <div className="flex-grow-1">
                <div className="fw-medium text-truncate">
                  {session.nombre}
                  {session.finalizada && (
                    <span className="badge bg-secondary ms-1">Finalizada</span>
                  )}
                  {session.tiene_pregunta_bloqueada && (
                    <span className="badge bg-warning ms-1">Bloqueada</span>
                  )}
                </div>
                <small className={selectedSessionId === session.id ? 'text-light' : 'text-muted'}>
                  {formatDate(session.fecha_creacion)}
                </small>
              </div>
              {!session.tiene_pregunta_bloqueada && (
                <button
                  className="btn btn-sm btn-outline-danger"
                  onClick={(e) => deleteSession(session.id, e)}
                  title="Eliminar sesión"
                >
                  ×
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {showNewSessionModal && (
        <div className="modal show d-block" tabIndex={-1}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Nueva Conversación</h5>
                <button 
                  type="button" 
                  className="btn-close" 
                  onClick={() => setShowNewSessionModal(false)}
                ></button>
              </div>
              <div className="modal-body">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Nombre de la conversación"
                  value={newSessionName}
                  onChange={(e) => setNewSessionName(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && createSession()}
                  autoFocus
                />
              </div>
              <div className="modal-footer">
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => setShowNewSessionModal(false)}
                >
                  Cancelar
                </button>
                <button 
                  type="button" 
                  className="btn btn-primary"
                  onClick={createSession}
                  disabled={!newSessionName.trim()}
                >
                  Crear
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatSidebar;