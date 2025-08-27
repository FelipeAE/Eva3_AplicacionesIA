import React, { useState } from 'react';
import ChatSidebar from './ChatSidebar';
import ChatInterface from './ChatInterface';
import AdminPanel from './AdminPanel';
import ThemeToggle from './ThemeToggle';
import { useAuth } from '../contexts/AuthContext';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);
  const [sidebarKey, setSidebarKey] = useState(0);
  const [showAdminPanel, setShowAdminPanel] = useState(false);
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);

  console.log('Dashboard user:', user);
  console.log('Is user staff?', user?.is_staff);

  const handleSessionUpdate = () => {
    setSidebarKey(prev => prev + 1);
  };

  const handleNewSession = () => {
    setSelectedSessionId(null);
    handleSessionUpdate();
  };

  // Global keyboard shortcuts
  useKeyboardShortcuts({
    onNewSession: handleNewSession,
  });

  return (
    <div className="container-fluid p-0 vh-100">
      {/* Mobile Header */}
      <div className="d-md-none bg-white border-bottom p-2 d-flex justify-content-between align-items-center">
        <button 
          className="btn btn-outline-secondary btn-sm"
          onClick={() => setShowMobileSidebar(true)}
        >
          ☰ Conversaciones
        </button>
        <span className="fw-bold">Chatbot RRHH</span>
        <div className="dropdown">
          <button className="btn btn-sm btn-outline-secondary dropdown-toggle" 
                  type="button" data-bs-toggle="dropdown">
            {user?.username}
          </button>
          <ul className="dropdown-menu dropdown-menu-end">
            {user?.is_staff && (
              <>
                <li>
                  <button 
                    className="dropdown-item" 
                    onClick={() => setShowAdminPanel(true)}
                  >
                    ⚙️ Administración
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
              <button className="dropdown-item" onClick={() => window.location.href = '/logout'}>
                Cerrar Sesión
              </button>
            </li>
          </ul>
        </div>
      </div>

      <div className="row g-0 h-100">
        {/* Desktop Sidebar */}
        <div className="col-md-3 col-lg-2 d-none d-md-block">
          <ChatSidebar 
            key={sidebarKey}
            onSessionSelect={setSelectedSessionId}
            selectedSessionId={selectedSessionId}
            onShowAdminPanel={() => setShowAdminPanel(true)}
            isAdmin={user?.is_staff || false}
          />
        </div>
        
        {/* Mobile Sidebar Overlay */}
        {showMobileSidebar && (
          <>
            <div 
              className="position-fixed top-0 start-0 w-100 h-100 bg-black bg-opacity-50 d-md-none" 
              style={{ zIndex: 1040 }}
              onClick={() => setShowMobileSidebar(false)}
            />
            <div 
              className="position-fixed top-0 start-0 h-100 d-md-none" 
              style={{ width: '280px', zIndex: 1050 }}
            >
              <div className="h-100 bg-white">
                <div className="p-2 border-bottom d-flex justify-content-between align-items-center">
                  <span className="fw-bold">Conversaciones</span>
                  <button 
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => setShowMobileSidebar(false)}
                  >
                    ✕
                  </button>
                </div>
                <ChatSidebar 
                  key={sidebarKey}
                  onSessionSelect={(id) => {
                    setSelectedSessionId(id);
                    setShowMobileSidebar(false);
                  }}
                  selectedSessionId={selectedSessionId}
                  onShowAdminPanel={() => {
                    setShowAdminPanel(true);
                    setShowMobileSidebar(false);
                  }}
                  isAdmin={user?.is_staff || false}
                  isMobile={true}
                />
              </div>
            </div>
          </>
        )}
        
        <div className="col-12 col-md-9 col-lg-10" style={{ height: showMobileSidebar ? 'calc(100vh - 56px)' : '100vh' }}>
          <ChatInterface 
            sessionId={selectedSessionId}
            onSessionUpdate={handleSessionUpdate}
          />
        </div>
      </div>
      
      <AdminPanel 
        isVisible={showAdminPanel}
        onClose={() => setShowAdminPanel(false)}
        isAdmin={user?.is_staff || false}
      />
    </div>
  );
};

export default Dashboard;