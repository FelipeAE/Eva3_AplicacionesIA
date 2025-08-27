import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(username, password);
      navigate('/');
    } catch (error: any) {
      setError(error.response?.data?.error || 'Error de autenticación');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      minHeight: '100vh',
      fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '15px',
        padding: '40px',
        boxShadow: '0 15px 35px rgba(0,0,0,0.1)',
        width: '100%',
        maxWidth: '400px'
      }}>
        <div style={{
          width: '60px',
          height: '60px',
          background: '#2563eb',
          borderRadius: '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 20px',
          color: 'white',
          fontSize: '24px'
        }}>
          💬
        </div>
        <h1 style={{
          color: '#1f2937',
          fontWeight: '600',
          fontSize: '28px',
          textAlign: 'center',
          marginBottom: '10px'
        }}>
          Chatbot RRHH
        </h1>
        <p style={{
          color: '#6b7280',
          textAlign: 'center',
          marginBottom: '30px',
          fontSize: '14px'
        }}>
          Inicia sesión para acceder al chat de RRHH
        </p>
        
        {error && (
          <div style={{
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#dc2626',
            padding: '12px',
            borderRadius: '8px',
            marginBottom: '20px',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label htmlFor="username" style={{
              color: '#374151',
              fontWeight: '500',
              marginBottom: '8px',
              display: 'block'
            }}>
              Nombre de usuario
            </label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Ingresa tu nombre de usuario"
              required
              disabled={loading}
              style={{
                width: '100%',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '12px 16px',
                fontSize: '14px',
                outline: 'none'
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#2563eb';
                e.target.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#e5e7eb';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>
          <div style={{ marginBottom: '20px' }}>
            <label htmlFor="password" style={{
              color: '#374151',
              fontWeight: '500',
              marginBottom: '8px',
              display: 'block'
            }}>
              Contraseña
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Ingresa tu contraseña"
              required
              disabled={loading}
              style={{
                width: '100%',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '12px 16px',
                fontSize: '14px',
                outline: 'none'
              }}
              onFocus={(e) => {
                e.target.style.borderColor = '#2563eb';
                e.target.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#e5e7eb';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            style={{
              background: '#2563eb',
              border: 'none',
              borderRadius: '8px',
              padding: '12px',
              width: '100%',
              color: 'white',
              fontWeight: '500',
              fontSize: '16px',
              marginBottom: '20px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
            onMouseOver={(e) => {
              if (!loading) {
                e.currentTarget.style.background = '#1d4ed8';
              }
            }}
            onMouseOut={(e) => {
              if (!loading) {
                e.currentTarget.style.background = '#2563eb';
              }
            }}
          >
            {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
          </button>
        </form>
        
        <div style={{
          textAlign: 'center',
          color: '#6b7280',
          fontSize: '14px'
        }}>
          ¿No tienes una cuenta? <Link 
            to="/register" 
            style={{
              color: '#2563eb',
              textDecoration: 'none'
            }}
            onMouseOver={(e) => e.currentTarget.style.textDecoration = 'underline'}
            onMouseOut={(e) => e.currentTarget.style.textDecoration = 'none'}
          >
            Regístrate aquí
          </Link>
        </div>
        
        <div style={{
          textAlign: 'center',
          color: '#9ca3af',
          fontSize: '12px',
          marginTop: '30px'
        }}>
          Chatbot especializado en análisis de datos en RRHH
        </div>
      </div>
    </div>
  );
};

export default Login;