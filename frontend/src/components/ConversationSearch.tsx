import React, { useState, useEffect } from 'react';
import { chatAPI, ChatSession } from '../services/api';

interface SearchResult {
  sessionId: number;
  sessionName: string;
  messageId: number;
  messageContent: string;
  messageTimestamp: string;
  sender: string;
}

interface ConversationSearchProps {
  isVisible: boolean;
  onClose: () => void;
  onNavigateToSession?: (sessionId: number) => void;
}

const ConversationSearch: React.FC<ConversationSearchProps> = ({ 
  isVisible, 
  onClose, 
  onNavigateToSession 
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);

  useEffect(() => {
    if (isVisible) {
      loadSessions();
    }
  }, [isVisible]);

  useEffect(() => {
    if (searchTerm.length >= 2) {
      performSearch();
    } else {
      setResults([]);
    }
  }, [searchTerm, sessions]);

  const loadSessions = async () => {
    try {
      const response = await chatAPI.getSessions();
      setSessions(response.data);
    } catch (error) {
      console.error('Error loading sessions for search:', error);
    }
  };

  const performSearch = async () => {
    if (searchTerm.length < 2) return;
    
    setLoading(true);
    const searchResults: SearchResult[] = [];
    
    try {
      // Search through all sessions
      for (const session of sessions) {
        try {
          const sessionDetail = await chatAPI.getSession(session.id);
          const messages = sessionDetail.data.messages;
          
          // Search in message content
          for (const message of messages) {
            if (message.content.toLowerCase().includes(searchTerm.toLowerCase())) {
              searchResults.push({
                sessionId: session.id,
                sessionName: session.nombre || `Sesión ${session.id}`,
                messageId: message.id,
                messageContent: message.content,
                messageTimestamp: message.timestamp,
                sender: message.sender
              });
            }
          }
        } catch (error) {
          // Skip sessions that can't be loaded
          continue;
        }
      }
      
      // Sort by timestamp (newest first)
      searchResults.sort((a, b) => 
        new Date(b.messageTimestamp).getTime() - new Date(a.messageTimestamp).getTime()
      );
      
      setResults(searchResults);
    } catch (error) {
      console.error('Error performing search:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('es-ES');
    } catch {
      return dateString;
    }
  };

  const highlightSearchTerm = (text: string, term: string) => {
    if (!term) return text;
    
    const regex = new RegExp(`(${term})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? 
        <mark key={index} className="bg-warning text-dark">{part}</mark> : 
        part
    );
  };

  const getContextSnippet = (text: string, searchTerm: string, maxLength: number = 200) => {
    const lowerText = text.toLowerCase();
    const lowerTerm = searchTerm.toLowerCase();
    const index = lowerText.indexOf(lowerTerm);
    
    if (index === -1) return text.substring(0, maxLength) + '...';
    
    const start = Math.max(0, index - 50);
    const end = Math.min(text.length, index + searchTerm.length + 100);
    const snippet = (start > 0 ? '...' : '') + 
                   text.substring(start, end) + 
                   (end < text.length ? '...' : '');
    
    return snippet;
  };

  if (!isVisible) return null;

  return (
    <div className="modal show d-block" tabIndex={-1}>
      <div className="modal-dialog modal-xl">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">🔍 Buscar en Conversaciones</h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <div className="modal-body">
            {/* Search Input */}
            <div className="mb-4">
              <div className="input-group">
                <span className="input-group-text">🔍</span>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Buscar en todas las conversaciones..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  autoFocus
                />
                {searchTerm && (
                  <button 
                    className="btn btn-outline-secondary"
                    onClick={() => setSearchTerm('')}
                  >
                    ❌
                  </button>
                )}
              </div>
              <small className="text-muted">
                Ingresa al menos 2 caracteres para buscar
              </small>
            </div>

            {/* Loading State */}
            {loading && (
              <div className="text-center py-3">
                <div className="spinner-border spinner-border-sm me-2"></div>
                Buscando...
              </div>
            )}

            {/* Search Results */}
            <div style={{ maxHeight: '60vh', overflowY: 'auto' }}>
              {searchTerm.length >= 2 && !loading && (
                <div className="mb-3">
                  <small className="text-muted">
                    {results.length} resultado{results.length !== 1 ? 's' : ''} encontrado{results.length !== 1 ? 's' : ''}
                  </small>
                </div>
              )}
              
              {results.map((result, index) => (
                <div key={`${result.sessionId}-${result.messageId}`} className="card mb-3">
                  <div className="card-body">
                    <div className="d-flex justify-content-between align-items-start mb-2">
                      <div>
                        <h6 className="card-title mb-1">
                          📝 {result.sessionName}
                        </h6>
                        <small className="text-muted">
                          {result.sender === 'usuario' ? '👤 Tu pregunta' : 
                           result.sender === 'ia' ? '🤖 Respuesta IA' : '⚙️ Sistema'} • 
                          {formatDate(result.messageTimestamp)}
                        </small>
                      </div>
                      {onNavigateToSession && (
                        <button 
                          className="btn btn-outline-primary btn-sm"
                          onClick={() => {
                            onNavigateToSession(result.sessionId);
                            onClose();
                          }}
                        >
                          📍 Ir a conversación
                        </button>
                      )}
                    </div>
                    
                    <div className="card-text">
                      <div 
                        className={`border-start border-3 ps-3 small ${
                          result.sender === 'usuario' ? 'border-primary' : 
                          result.sender === 'ia' ? 'border-success' : 'border-secondary'
                        }`}
                        style={{ whiteSpace: 'pre-wrap' }}
                      >
                        {highlightSearchTerm(
                          getContextSnippet(result.messageContent, searchTerm),
                          searchTerm
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {searchTerm.length >= 2 && results.length === 0 && !loading && (
                <div className="text-center py-5">
                  <div className="mb-3" style={{ fontSize: '3rem' }}>🔍</div>
                  <h6 className="text-muted">No se encontraron resultados</h6>
                  <p className="text-muted">
                    Prueba con otros términos de búsqueda
                  </p>
                </div>
              )}
            </div>
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

export default ConversationSearch;