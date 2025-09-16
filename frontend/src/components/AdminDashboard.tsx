import React, { useState, useEffect } from 'react';
import { adminAPI, DashboardData } from '../services/api';
import AdminCharts from './AdminCharts';

const AdminDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('Loading dashboard data...');
      const response = await adminAPI.getDashboard();
      console.log('Dashboard response:', response.data);
      setDashboardData(response.data);
    } catch (error: any) {
      console.error('Error loading dashboard:', error);
      setError(error.response?.data?.error || 'Error cargando dashboard');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Nunca';
    try {
      return new Date(dateString).toLocaleString('es-ES');
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <div className="text-center py-4">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Cargando dashboard...</span>
        </div>
        <p>Cargando estadísticas del sistema...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger" role="alert">
        <strong>Error:</strong> {error}
        <button 
          className="btn btn-outline-danger btn-sm ms-2"
          onClick={loadDashboard}
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="alert alert-warning" role="alert">
        No se pudieron cargar las estadísticas del dashboard.
      </div>
    );
  }

  const { statistics, active_users, recent_sessions, blocked_questions, frequent_excluded_terms, active_context } = dashboardData;

  return (
    <div>
      {/* Estadísticas principales */}
      <div className="row mb-4">
        <div className="col-md-2 col-sm-6">
          <div className="card bg-primary text-white">
            <div className="card-body">
              <h4 className="card-title">{statistics.total_usuarios}</h4>
              <p className="card-text">Total Usuarios</p>
            </div>
          </div>
        </div>
        <div className="col-md-2 col-sm-6">
          <div className="card bg-success text-white">
            <div className="card-body">
              <h4 className="card-title">{statistics.usuarios_activos}</h4>
              <p className="card-text">Activos (30d)</p>
            </div>
          </div>
        </div>
        <div className="col-md-2 col-sm-6">
          <div className="card bg-info text-white">
            <div className="card-body">
              <h4 className="card-title">{statistics.total_sesiones}</h4>
              <p className="card-text">Total Sesiones</p>
            </div>
          </div>
        </div>
        <div className="col-md-2 col-sm-6">
          <div className="card bg-warning text-dark">
            <div className="card-body">
              <h4 className="card-title">{statistics.sesiones_activas}</h4>
              <p className="card-text">Sesiones Activas</p>
            </div>
          </div>
        </div>
        <div className="col-md-2 col-sm-6">
          <div className="card bg-secondary text-white">
            <div className="card-body">
              <h4 className="card-title">{statistics.total_mensajes}</h4>
              <p className="card-text">Total Mensajes</p>
            </div>
          </div>
        </div>
        <div className="col-md-2 col-sm-6">
          <div className="card bg-danger text-white">
            <div className="card-body">
              <h4 className="card-title">{statistics.preguntas_bloqueadas}</h4>
              <p className="card-text">Preguntas Bloqueadas</p>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Charts */}
      <AdminCharts dashboardData={dashboardData} />

      <div className="row">
        {/* Usuarios más activos */}
        <div className="col-lg-6 mb-4">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">👥 Usuarios Más Activos</h5>
            </div>
            <div className="card-body">
              {active_users.length > 0 ? (
                <div className="table-responsive">
                  <table className="table table-sm">
                    <thead>
                      <tr>
                        <th>Usuario</th>
                        <th>Sesiones</th>
                        <th>Último Acceso</th>
                      </tr>
                    </thead>
                    <tbody>
                      {active_users.map((user) => (
                        <tr key={user.id}>
                          <td><strong>{user.username}</strong></td>
                          <td>
                            <span className="badge bg-primary">{user.num_sesiones}</span>
                          </td>
                          <td>
                            <small className="text-muted">{formatDate(user.last_login)}</small>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-muted">No hay usuarios con sesiones registradas.</p>
              )}
            </div>
          </div>
        </div>

        {/* Sesiones recientes */}
        <div className="col-lg-6 mb-4">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">💬 Sesiones Recientes</h5>
            </div>
            <div className="card-body" style={{ maxHeight: '300px', overflowY: 'auto' }}>
              {recent_sessions.length > 0 ? (
                recent_sessions.map((session) => (
                  <div key={session.id} className="border-bottom pb-2 mb-2">
                    <div className="d-flex justify-content-between align-items-start">
                      <div>
                        <strong>{session.name || `Sesión #${session.id}`}</strong>
                        <br />
                        <small className="text-muted">
                          Usuario: {session.user} • {formatDate(session.created)}
                        </small>
                      </div>
                      <span className={`badge ${session.status === 'activa' ? 'bg-success' : 'bg-secondary'}`}>
                        {session.status}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-muted">No hay sesiones recientes.</p>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="row">
        {/* Preguntas bloqueadas recientes */}
        <div className="col-lg-8 mb-4">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">🚫 Preguntas Bloqueadas Recientes</h5>
            </div>
            <div className="card-body" style={{ maxHeight: '300px', overflowY: 'auto' }}>
              {blocked_questions.length > 0 ? (
                blocked_questions.map((question) => (
                  <div key={question.id} className="border-bottom pb-2 mb-2">
                    <div className="mb-1">
                      <strong>"{question.question}"</strong>
                    </div>
                    <div>
                      <small className="text-danger">
                        <strong>Razón:</strong> {question.reason}
                      </small>
                      <br />
                      <small className="text-muted">
                        Usuario: {question.user} • {formatDate(question.date)}
                      </small>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-muted">No hay preguntas bloqueadas recientes.</p>
              )}
            </div>
          </div>
        </div>

        {/* Términos más excluidos */}
        <div className="col-lg-4 mb-4">
          <div className="card">
            <div className="card-header">
              <h5 className="card-title mb-0">🔒 Términos Más Excluidos</h5>
            </div>
            <div className="card-body">
              {frequent_excluded_terms.length > 0 ? (
                frequent_excluded_terms.map((term, index) => (
                  <div key={term.term} className="d-flex justify-content-between align-items-center mb-2">
                    <span>
                      <strong>#{index + 1}</strong> {term.term}
                    </span>
                    <span className="badge bg-secondary">{term.count}</span>
                  </div>
                ))
              ) : (
                <p className="text-muted">No hay términos excluidos registrados.</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Contexto Activo */}
      <div className="row">
        <div className="col-lg-6 mb-4">
          <div className="card">
            <div className="card-header bg-primary text-white">
              <h5 className="card-title mb-0">🧠 Contexto Activo</h5>
            </div>
            <div className="card-body">
              {active_context ? (
                <div>
                  <div className="mb-3">
                    <h6 className="text-primary d-flex align-items-center">
                      <span className="badge bg-success me-2">Activo</span>
                      {active_context.nombre}
                    </h6>
                  </div>
                  <div className="border-start border-3 border-primary ps-3 mb-3">
                    <small className="text-muted">
                      <strong>¿Qué hace este contexto?</strong><br />
                      <em>{active_context.prompt}</em>
                    </small>
                  </div>
                  <div className="text-center">
                    <small className="text-muted">
                      El chatbot está usando este contexto personalizado para generar respuestas
                    </small>
                  </div>
                </div>
              ) : (
                <div className="text-center text-muted py-3">
                  <i className="fas fa-exclamation-triangle fa-2x mb-3 text-warning"></i>
                  <h6>No hay contexto activo</h6>
                  <p className="mb-0">Se está usando el contexto por defecto del sistema</p>
                  <small>Ve a la pestaña "Contextos" para activar uno personalizado</small>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Botón de actualizar */}
      <div className="text-center">
        <button 
          className="btn btn-outline-primary"
          onClick={loadDashboard}
          disabled={loading}
        >
          🔄 Actualizar Dashboard
        </button>
      </div>
    </div>
  );
};

export default AdminDashboard;