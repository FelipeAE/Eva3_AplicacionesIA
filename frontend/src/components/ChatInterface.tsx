import React, { useState, useEffect, useRef } from 'react';
import { ChatMessage, SessionDetail, ContractDetail, chatAPI } from '../services/api';
import TypingIndicator from './TypingIndicator';
import QuestionTemplates from './QuestionTemplates';
import FavoritesPanel from './FavoritesPanel';
import ConversationSearch from './ConversationSearch';
import ContractComparison from './ContractComparison';
import ConversationTags from './ConversationTags';
import { useFavorites } from '../hooks/useFavorites';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import { useConversationTags } from '../hooks/useConversationTags';
import { exportConversation, ExportFormat } from '../utils/exportUtils';
import '../styles/typing-indicator.css';

interface ChatInterfaceProps {
  sessionId: number | null;
  onSessionUpdate?: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ sessionId, onSessionUpdate }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [contractDetails, setContractDetails] = useState<ContractDetail[]>([]);
  const [showContractModal, setShowContractModal] = useState(false);
  
  // New UI states
  const [showTemplates, setShowTemplates] = useState(false);
  const [showFavorites, setShowFavorites] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [showComparison, setShowComparison] = useState(false);
  const [showTags, setShowTags] = useState(false);
  const [isInputFocused, setIsInputFocused] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  // Hooks
  const { toggleFavorite, isFavorite } = useFavorites();
  const { getSessionTags } = useConversationTags();
  
  // Keyboard shortcuts
  useKeyboardShortcuts({
    onSend: () => sendMessage(),
    onToggleTemplates: () => setShowTemplates(true),
    onToggleFavorites: () => setShowFavorites(true),
    onSearch: () => setShowSearch(true),
    onExport: () => handleExport('html'),
    isInputFocused
  });

  // Close modals on escape
  useEffect(() => {
    const handleCloseModals = () => {
      setShowTemplates(false);
      setShowFavorites(false);
      setShowSearch(false);
      setShowComparison(false);
      setShowTags(false);
      setShowContractModal(false);
    };

    window.addEventListener('closeModals', handleCloseModals);
    return () => window.removeEventListener('closeModals', handleCloseModals);
  }, []);

  useEffect(() => {
    if (sessionId) {
      loadSession();
    } else {
      setMessages([]);
      setSession(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadSession = async () => {
    if (!sessionId) return;
    
    setLoadingMessages(true);
    try {
      const response = await chatAPI.getSession(sessionId);
      setSession(response.data);
      setMessages(response.data.messages);
    } catch (error) {
      console.error('Error loading session:', error);
    } finally {
      setLoadingMessages(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !sessionId || loading) return;
    
    setLoading(true);
    const messageText = newMessage;
    setNewMessage('');

    try {
      const response = await chatAPI.sendMessage(sessionId, messageText);
      
      await loadSession();
      onSessionUpdate?.();
      
      if (response.data.response) {
        // Check if we have metadata with contract IDs
        if (response.data.metadata && response.data.metadata.id_contrato) {
          console.log('=== CONTRACT METADATA FOUND ===');
          console.log('Contract IDs from metadata:', response.data.metadata.id_contrato);
          loadContractDetails(response.data.metadata.id_contrato);
        } else {
          // Fallback to parsing text (for old messages)
          extractContractIds(response.data.response);
        }
      }
    } catch (error: any) {
      console.error('Error sending message:', error);
      if (error.response?.data?.error) {
        alert(`Error: ${error.response.data.error}`);
      }
      setNewMessage(messageText);
    } finally {
      setLoading(false);
    }
  };

  const extractContractIds = (response: string) => {
    console.log('=== EXTRACT CONTRACT IDS DEBUG ===');
    console.log('Full response:', response);
    console.log('Response length:', response.length);
    console.log('Response type:', typeof response);
    
    try {
      // Try different JSON patterns
      const patterns = [
        /\{[^{}]*"id_contrato"[^{}]*\}/g,  // Original pattern
        /\{.*?"id_contrato".*?\}/g,       // More flexible
        /\{[\s\S]*?"id_contrato"[\s\S]*?\}/g, // Include newlines
        /\["id_contrato":\s*\[([\d,\s]*)\]\}/g // Different format
      ];
      
      let found = false;
      for (let i = 0; i < patterns.length; i++) {
        const matches = response.match(patterns[i]);
        console.log(`Pattern ${i + 1} matches:`, matches);
        
        if (matches) {
          for (const match of matches) {
            try {
              console.log('Trying to parse:', match);
              const jsonData = JSON.parse(match);
              console.log('Parsed JSON data:', jsonData);
              
              if (jsonData.id_contrato && Array.isArray(jsonData.id_contrato)) {
                console.log('✅ Contract IDs found:', jsonData.id_contrato);
                loadContractDetails(jsonData.id_contrato);
                found = true;
                break;
              }
            } catch (parseError) {
              console.log('Parse error for match:', match, parseError);
            }
          }
        }
        if (found) break;
      }
      
      if (!found) {
        console.log('❌ No contract IDs found in any format');
        console.log('Raw response for manual inspection:');
        console.log('---START---');
        console.log(response);
        console.log('---END---');
        alert('Este mensaje no contiene datos de contratos para mostrar.\n\nRevisa la consola para ver el contenido completo del mensaje.');
      }
      
    } catch (error) {
      console.error('Error parsing contract IDs:', error);
      alert('Error procesando datos del mensaje: ' + error);
    }
  };

  const loadContractDetails = async (contractIds: number[]) => {
    try {
      if (contractIds.length === 1) {
        // Single contract - use individual endpoint
        const response = await chatAPI.getContractDetails(contractIds[0]);
        setContractDetails([response.data]);
      } else {
        // Multiple contracts - use bulk endpoint
        const response = await chatAPI.getContractDetailsBulk(contractIds);
        setContractDetails(response.data.contracts);
      }
      setShowContractModal(true);
    } catch (error) {
      console.error('Error loading contract details:', error);
    }
  };

  const finalizeSession = async () => {
    if (!sessionId || !session) return;
    
    if (!window.confirm('¿Está seguro de que desea finalizar esta sesión? No podrá agregar más mensajes.')) {
      return;
    }

    try {
      await chatAPI.finalizeSession(sessionId);
      await loadSession();
      onSessionUpdate?.();
    } catch (error) {
      console.error('Error finalizing session:', error);
    }
  };

  const deleteSession = async () => {
    if (!sessionId || !session) return;
    
    if (!window.confirm('¿Está seguro de que desea eliminar esta conversación? Esta acción no se puede deshacer.')) {
      return;
    }

    try {
      await chatAPI.deleteSession(sessionId);
      onSessionUpdate?.();
      // Redirect to home or clear current session
      window.location.href = '/';
    } catch (error) {
      console.error('Error deleting session:', error);
      alert('Error eliminando la conversación. Es posible que contenga preguntas bloqueadas que deben conservarse.');
    }
  };

  // New functions for enhanced features
  const handleTemplateSelect = (templateQuestion: string) => {
    setNewMessage(templateQuestion);
    setShowTemplates(false);
    inputRef.current?.focus();
  };

  const handleFavoriteToggle = (message: ChatMessage) => {
    if (message.sender !== 'ia' || !session) return;
    
    const favoriteMessage = {
      id: message.id,
      content: message.content,
      timestamp: message.timestamp,
      sessionId: session.session.id,
      sessionName: session.session.name || `Conversación ${session.session.id}`
    };
    
    const added = toggleFavorite(favoriteMessage);
    console.log(added ? 'Added to favorites' : 'Removed from favorites');
  };

  const handleExport = (format: ExportFormat) => {
    if (!session) return;
    
    try {
      exportConversation(session, format);
    } catch (error) {
      console.error('Error exporting conversation:', error);
      alert('Error exportando la conversación');
    }
  };

  const handleNavigateToSession = (targetSessionId: number) => {
    window.location.href = `/sesion/${targetSessionId}/`;
  };

  const formatMessage = (text: string | undefined | null) => {
    if (!text) return '';
    const jsonMatch = text.match(/\{[^{}]*"id_contrato"[^{}]*\}/);
    if (jsonMatch) {
      return text.replace(jsonMatch[0], '').trim();
    }
    return text;
  };

  const formatDate = (dateString: string | undefined | null) => {
    if (!dateString) return '';
    try {
      return new Date(dateString).toLocaleString('es-ES');
    } catch (error) {
      return dateString;
    }
  };

  if (!sessionId) {
    return (
      <div className="d-flex align-items-center justify-content-center h-100 text-muted">
        <div className="text-center">
          <h5>Selecciona una conversación</h5>
          <p>O crea una nueva para comenzar</p>
        </div>
      </div>
    );
  }

  return (
    <div className="d-flex flex-column h-100">
      {session && (
        <div className="p-2 p-md-3 border-bottom bg-white">
          <div className="d-flex justify-content-between align-items-start">
            <div className="flex-grow-1">
              <h6 className="mb-1 d-flex align-items-center gap-2">
                <span className="text-truncate" style={{ maxWidth: '200px' }}>
                  {session.session.name}
                </span>
                <button 
                  className="btn btn-sm btn-outline-secondary d-none d-md-inline-block"
                  onClick={() => setShowTags(true)}
                  title="Gestionar etiquetas"
                >
                  🏷️
                </button>
              </h6>
              <div className="d-flex flex-column d-md-block">
                <small className="text-muted">
                  <span className="d-inline-block">Creada: {formatDate(session.session.created_at)}</span>
                  {session.session.finished_at && (
                    <span className="badge bg-secondary ms-1 ms-md-2">Finalizada</span>
                  )}
                </small>
                {session?.context?.active_context && (
                  <small className="text-muted d-block d-md-inline">
                    <span className="d-none d-md-inline"> | </span>
                    Contexto: <strong className="text-info">{session.context.active_context}</strong>
                  </small>
                )}
              </div>
              {getSessionTags(session.session.id).length > 0 && (
                <div className="d-flex gap-1">
                  {getSessionTags(session.session.id).slice(0, 3).map((tag) => (
                    <span key={tag} className="badge bg-primary" style={{ fontSize: '0.7rem' }}>
                      {tag}
                    </span>
                  ))}
                  {getSessionTags(session.session.id).length > 3 && (
                    <span className="badge bg-secondary" style={{ fontSize: '0.7rem' }}>
                      +{getSessionTags(session.session.id).length - 3}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
          <div className="d-flex flex-column flex-md-row gap-2 mt-2 mt-md-0">
            {/* Mobile: Show fewer buttons, compact layout */}
            <div className="btn-group btn-group-sm d-md-none">
              <button 
                className="btn btn-outline-secondary"
                onClick={() => setShowTemplates(true)}
                title="Templates"
              >
                💡
              </button>
              <button 
                className="btn btn-outline-secondary"
                onClick={() => setShowFavorites(true)}
                title="Favoritos"
              >
                ⭐
              </button>
              <button 
                className="btn btn-outline-secondary"
                onClick={() => setShowTags(true)}
                title="Etiquetas"
              >
                🏷️
              </button>
            </div>
            
            {/* Desktop: Full toolbar */}
            <div className="btn-group btn-group-sm d-none d-md-flex">
              <button 
                className="btn btn-outline-secondary"
                onClick={() => setShowTemplates(true)}
                title="Templates de preguntas (Ctrl+Shift+T)"
              >
                💡
              </button>
              <button 
                className="btn btn-outline-secondary"
                onClick={() => setShowFavorites(true)}
                title="Ver favoritos (Ctrl+Shift+S)"
              >
                ⭐
              </button>
              <button 
                className="btn btn-outline-secondary"
                onClick={() => setShowSearch(true)}
                title="Buscar en conversaciones (Ctrl+F)"
              >
                🔍
              </button>
              <button 
                className="btn btn-outline-secondary"
                onClick={() => setShowComparison(true)}
                title="Comparar contratos"
              >
                ⚖️
              </button>
              <div className="dropdown">
                <button 
                  className="btn btn-outline-secondary dropdown-toggle"
                  type="button" 
                  data-bs-toggle="dropdown"
                  title="Exportar conversación"
                >
                  📥
                </button>
                <ul className="dropdown-menu">
                  <li>
                    <button 
                      className="dropdown-item"
                      onClick={() => handleExport('txt')}
                    >
                      📄 Texto (.txt)
                    </button>
                  </li>
                  <li>
                    <button 
                      className="dropdown-item"
                      onClick={() => handleExport('html')}
                    >
                      🌐 HTML (.html)
                    </button>
                  </li>
                  <li>
                    <button 
                      className="dropdown-item"
                      onClick={() => handleExport('json')}
                    >
                      🔧 JSON (.json)
                    </button>
                  </li>
                </ul>
              </div>
            </div>

            {/* Session control buttons */}
            {!session.session.readonly && (
              <div className="btn-group btn-group-sm">
                <button 
                  className="btn btn-outline-warning"
                  onClick={finalizeSession}
                  title="Finalizar sesión"
                >
                  Finalizar
                </button>
                <button 
                  className="btn btn-outline-danger"
                  onClick={deleteSession}
                  title="Eliminar conversación"
                >
                  🗑️
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="flex-grow-1 overflow-auto p-3 bg-light">
        {loadingMessages ? (
          <div className="text-center">
            <div className="spinner-border" role="status">
              <span className="visually-hidden">Cargando mensajes...</span>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center text-muted">
            <p>No hay mensajes en esta conversación</p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div key={message.id} className="mb-3">
              <div className={`d-flex justify-content-${message.sender === 'usuario' ? 'end' : 'start'} mb-2`}>
                <div 
                  className={`${message.sender === 'usuario' ? 'bg-primary text-white' : 'bg-white border'} rounded p-2`}
                  style={{ maxWidth: '70%' }}
                >
                  <div className={`fw-medium mb-1 ${message.sender === 'usuario' ? 'text-white' : message.sender === 'ia' ? 'text-success' : 'text-muted'}`}>
                    {message.sender === 'usuario' ? 'Tu pregunta:' : message.sender === 'ia' ? 'Respuesta:' : 'Sistema:'}
                  </div>
                  <div style={{ whiteSpace: 'pre-wrap' }}>
                    {message.sender === 'ia' ? formatMessage(message.content) : message.content}
                  </div>
                  <div className="d-flex justify-content-between align-items-center mt-2">
                    <small className={message.sender === 'usuario' ? 'text-light opacity-75' : 'text-muted'}>
                      {formatDate(message.timestamp)}
                    </small>
                    {message.sender === 'ia' && (
                      <div className="d-flex gap-1">
                        <button 
                          className="btn btn-sm btn-outline-info"
                          onClick={() => {
                            console.log('Datos button clicked for message:', message.id);
                            console.log('Message metadata:', message.metadata);
                            
                            // Check if we have metadata with contract IDs
                            if (message.metadata && message.metadata.tipo === 'id_contrato' && message.metadata.ids) {
                              console.log('=== CONTRACT METADATA FOUND IN MESSAGE ===');
                              console.log('Contract IDs from message metadata:', message.metadata.ids);
                              loadContractDetails(message.metadata.ids);
                            } else {
                              // Fallback to parsing text content
                              console.log('No contract metadata in message, trying to parse content...');
                              extractContractIds(message.content);
                            }
                          }}
                          title="Ver datos fuente"
                        >
                          📊 Datos
                        </button>
                        <button 
                          className={`btn btn-sm ${isFavorite(message.id) ? 'btn-warning' : 'btn-outline-warning'}`}
                          onClick={() => handleFavoriteToggle(message)}
                          title={isFavorite(message.id) ? 'Quitar de favoritos' : 'Agregar a favoritos'}
                        >
                          ⭐
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {/* Typing indicator */}
          {loading && <TypingIndicator />}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {session && !session.session.readonly && (
        <div className="p-2 p-md-3 border-top bg-white">
          {/* Mobile: Stack input and button vertically on very small screens */}
          <div className="d-block d-sm-none">
            <div className="mb-2">
              <input
                ref={inputRef}
                type="text"
                className="form-control"
                placeholder="Escribe tu pregunta..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                onFocus={() => setIsInputFocused(true)}
                onBlur={() => setIsInputFocused(false)}
                disabled={loading}
              />
            </div>
            <button
              className="btn btn-primary w-100"
              onClick={sendMessage}
              disabled={loading || !newMessage.trim()}
            >
              {loading ? (
                <div className="spinner-border spinner-border-sm" role="status">
                  <span className="visually-hidden">Enviando...</span>
                </div>
              ) : (
                '📤 Enviar'
              )}
            </button>
          </div>
          
          {/* Tablet and Desktop: Keep horizontal layout */}
          <div className="input-group d-none d-sm-flex">
            <input
              ref={inputRef}
              type="text"
              className="form-control"
              placeholder="Escribe tu pregunta sobre RRHH... (o presiona 💡 para templates)"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              onFocus={() => setIsInputFocused(true)}
              onBlur={() => setIsInputFocused(false)}
              disabled={loading}
            />
            <button
              className="btn btn-primary"
              onClick={sendMessage}
              disabled={loading || !newMessage.trim()}
            >
              {loading ? (
                <div className="spinner-border spinner-border-sm" role="status">
                  <span className="visually-hidden">Enviando...</span>
                </div>
              ) : (
                'Enviar'
              )}
            </button>
          </div>
        </div>
      )}

      {showContractModal && contractDetails.length > 0 && (
        <div className="modal show d-block" tabIndex={-1}>
          <div className="modal-dialog modal-lg modal-dialog-scrollable"
               style={{ maxHeight: '90vh', margin: '1rem' }}>
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Detalles de Contratos</h5>
                <button 
                  type="button" 
                  className="btn-close" 
                  onClick={() => setShowContractModal(false)}
                ></button>
              </div>
              <div className="modal-body">
                {contractDetails.map((contract, index: number) => (
                  <div key={contract.id_contrato || index} className="card mb-3">
                    <div className="card-header">
                      <h6 className="mb-0">
                        <strong>Contrato #{contract.id_contrato}</strong> - {contract.persona?.nombre_completo}
                      </h6>
                    </div>
                    <div className="card-body">
                      <div className="row">
                        <div className="col-md-6">
                          <h6 className="text-primary">Información Personal</h6>
                          <p><strong>Nombre:</strong> {contract.persona?.nombre_completo}</p>
                          {contract.persona?.rut && <p><strong>RUT:</strong> {contract.persona.rut}</p>}
                          
                          <h6 className="text-success mt-3">Función</h6>
                          <p><strong>Descripción:</strong> {contract.funcion?.descripcion}</p>
                          <p><strong>Calificación:</strong> {contract.funcion?.calificacion_profesional}</p>
                        </div>
                        <div className="col-md-6">
                          <h6 className="text-info">Periodo y Ubicación</h6>
                          <p><strong>Mes:</strong> {contract.periodo?.mes}</p>
                          <p><strong>Año:</strong> {contract.periodo?.anho}</p>
                          <p><strong>Región:</strong> {contract.periodo?.region}</p>
                          
                          <h6 className="text-warning mt-3">Información Económica</h6>
                          {contract.honorario_total_bruto && (
                            <p><strong>Honorario Bruto:</strong> ${contract.honorario_total_bruto?.toLocaleString('es-CL')}</p>
                          )}
                          {contract.viaticos && (
                            <p><strong>Viáticos:</strong> ${contract.viaticos?.toLocaleString('es-CL')}</p>
                          )}
                          <p><strong>Tipo Pago:</strong> {contract.tipo_pago}</p>
                        </div>
                      </div>
                      
                      {(contract.observaciones || contract.enlace_funciones) && (
                        <div className="mt-3">
                          <h6 className="text-secondary">Información Adicional</h6>
                          {contract.observaciones && (
                            <p><strong>Observaciones:</strong> {contract.observaciones}</p>
                          )}
                          {contract.enlace_funciones && (
                            <p><strong>Enlace Funciones:</strong> {contract.enlace_funciones}</p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <div className="modal-footer d-flex justify-content-between">
                <div>
                  {contractDetails.length >= 2 && (
                    <button 
                      type="button" 
                      className="btn btn-info"
                      onClick={() => {
                        setShowContractModal(false);
                        setShowComparison(true);
                      }}
                      title="Comparar estos contratos lado a lado"
                    >
                      ⚖️ Comparar todos
                    </button>
                  )}
                </div>
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={() => setShowContractModal(false)}
                >
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* New Feature Modals */}
      <QuestionTemplates 
        isVisible={showTemplates}
        onClose={() => setShowTemplates(false)}
        onSelectTemplate={handleTemplateSelect}
      />
      
      <FavoritesPanel 
        isVisible={showFavorites}
        onClose={() => setShowFavorites(false)}
        onNavigateToMessage={handleNavigateToSession}
      />
      
      <ConversationSearch 
        isVisible={showSearch}
        onClose={() => setShowSearch(false)}
        onNavigateToSession={handleNavigateToSession}
      />
      
      <ContractComparison 
        isVisible={showComparison}
        onClose={() => setShowComparison(false)}
        initialContracts={contractDetails.length >= 2 ? contractDetails.map(c => c.id_contrato) : []}
      />
      
      <ConversationTags 
        isVisible={showTags}
        onClose={() => setShowTags(false)}
        session={session}
        onTagsUpdated={() => {
          // Force re-render to show updated tags
          const event = new CustomEvent('tagsUpdated');
          window.dispatchEvent(event);
        }}
      />
    </div>
  );
};

export default ChatInterface;