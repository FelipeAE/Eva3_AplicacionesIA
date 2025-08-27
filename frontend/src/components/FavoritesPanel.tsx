import React from 'react';
import { useFavorites } from '../hooks/useFavorites';

interface FavoritesPanelProps {
  isVisible: boolean;
  onClose: () => void;
  onNavigateToMessage?: (sessionId: number, messageId: number) => void;
}

const FavoritesPanel: React.FC<FavoritesPanelProps> = ({ isVisible, onClose, onNavigateToMessage }) => {
  const { favorites, clearAllFavorites, removeFavorite } = useFavorites();

  if (!isVisible) return null;

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('es-ES');
    } catch {
      return dateString;
    }
  };

  const handleClearAll = () => {
    if (window.confirm('¿Estás seguro de que quieres eliminar todos los favoritos?')) {
      clearAllFavorites();
    }
  };

  return (
    <div className="modal show d-block" tabIndex={-1}>
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">⭐ Mensajes Favoritos</h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <div className="modal-body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
            {favorites.length === 0 ? (
              <div className="text-center py-5">
                <div className="mb-3" style={{ fontSize: '3rem' }}>⭐</div>
                <h6 className="text-muted">No tienes mensajes favoritos</h6>
                <p className="text-muted">
                  Haz clic en la ⭐ al lado de cualquier respuesta de la IA para agregarla a favoritos.
                </p>
              </div>
            ) : (
              <div>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <span className="text-muted">{favorites.length} mensaje{favorites.length !== 1 ? 's' : ''} favorito{favorites.length !== 1 ? 's' : ''}</span>
                  <button 
                    className="btn btn-outline-danger btn-sm"
                    onClick={handleClearAll}
                  >
                    🗑️ Eliminar todos
                  </button>
                </div>
                
                {favorites.map((favorite, index) => (
                  <div key={favorite.id} className="card mb-3">
                    <div className="card-body">
                      <div className="d-flex justify-content-between align-items-start mb-2">
                        <h6 className="card-title mb-0">
                          📝 {favorite.sessionName || `Conversación ${favorite.sessionId}`}
                        </h6>
                        <div className="btn-group btn-group-sm">
                          {onNavigateToMessage && (
                            <button 
                              className="btn btn-outline-primary"
                              onClick={() => onNavigateToMessage(favorite.sessionId, favorite.id)}
                              title="Ir al mensaje"
                            >
                              📍 Ir
                            </button>
                          )}
                          <button 
                            className="btn btn-outline-danger"
                            onClick={() => removeFavorite(favorite.id)}
                            title="Quitar de favoritos"
                          >
                            ❌
                          </button>
                        </div>
                      </div>
                      
                      <div className="card-text">
                        <div 
                          className="border-start border-3 border-success ps-3 mb-2"
                          style={{ 
                            maxHeight: '150px', 
                            overflowY: 'auto',
                            whiteSpace: 'pre-wrap',
                            fontSize: '0.9rem'
                          }}
                        >
                          {favorite.content.length > 300 
                            ? favorite.content.substring(0, 300) + '...' 
                            : favorite.content
                          }
                        </div>
                        
                        <small className="text-muted">
                          💾 Guardado el {formatDate(favorite.timestamp)}
                        </small>
                      </div>
                    </div>
                  </div>
                ))}
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

export default FavoritesPanel;