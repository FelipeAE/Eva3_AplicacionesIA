import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

const Register: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password1, setPassword1] = useState('');
  const [password2, setPassword2] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<any>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setErrors({});
    setLoading(true);

    try {
      const response = await api.post('/auth/register/', {
        username,
        password1,
        password2
      });
      setSuccess('Cuenta creada exitosamente. Ahora puedes iniciar sesión.');
      setUsername('');
      setPassword1('');
      setPassword2('');
    } catch (error: any) {
      if (error.response?.data) {
        if (error.response.data.error) {
          setError(error.response.data.error);
        } else {
          setErrors(error.response.data);
        }
      } else {
        setError('Error al crear la cuenta');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
      minHeight: '100vh',
      fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px 0'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '15px',
        padding: '40px',
        boxShadow: '0 15px 35px rgba(0,0,0,0.1)',
        width: '100%',
        maxWidth: '450px'
      }}>
        <div style={{
          width: '60px',
          height: '60px',
          background: '#10b981',
          borderRadius: '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 20px',
          color: 'white',
          fontSize: '24px'
        }}>
          👤
        </div>
        <h1 style={{
          color: '#1f2937',
          fontWeight: '600',
          fontSize: '28px',
          textAlign: 'center',
          marginBottom: '10px'
        }}>
          Crear Cuenta
        </h1>
        <p style={{
          color: '#6b7280',
          textAlign: 'center',
          marginBottom: '30px',
          fontSize: '14px'
        }}>
          Regístrate para acceder al chatbot de RRHH
        </p>
        
        {success && (
          <div style={{
            backgroundColor: '#f0fdf4',
            border: '1px solid #bbf7d0',
            color: '#166534',
            padding: '12px',
            borderRadius: '8px',
            marginBottom: '20px',
            fontSize: '14px'
          }}>
            {success}
          </div>
        )}

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
                e.target.style.borderColor = '#10b981';
                e.target.style.boxShadow = '0 0 0 3px rgba(16, 185, 129, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#e5e7eb';
                e.target.style.boxShadow = 'none';
              }}
            />
            {errors.username && (
              <div style={{
                color: '#dc2626',
                fontSize: '12px',
                marginTop: '4px'
              }}>
                {errors.username.join(' ')}
              </div>
            )}
            <div style={{
              fontSize: '12px',
              color: '#6b7280',
              marginTop: '4px'
            }}>
              Solo letras, números y guiones bajos. Mínimo 3 caracteres.
            </div>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label htmlFor="password1" style={{
              color: '#374151',
              fontWeight: '500',
              marginBottom: '8px',
              display: 'block'
            }}>
              Contraseña
            </label>
            <input
              type="password"
              id="password1"
              value={password1}
              onChange={(e) => setPassword1(e.target.value)}
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
                e.target.style.borderColor = '#10b981';
                e.target.style.boxShadow = '0 0 0 3px rgba(16, 185, 129, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#e5e7eb';
                e.target.style.boxShadow = 'none';
              }}
            />
            {errors.password1 && (
              <div style={{
                color: '#dc2626',
                fontSize: '12px',
                marginTop: '4px'
              }}>
                {errors.password1.join(' ')}
              </div>
            )}
            <div style={{
              fontSize: '12px',
              color: '#6b7280',
              marginTop: '4px'
            }}>
              Mínimo 6 caracteres.
            </div>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label htmlFor="password2" style={{
              color: '#374151',
              fontWeight: '500',
              marginBottom: '8px',
              display: 'block'
            }}>
              Confirmar contraseña
            </label>
            <input
              type="password"
              id="password2"
              value={password2}
              onChange={(e) => setPassword2(e.target.value)}
              placeholder="Confirma tu contraseña"
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
                e.target.style.borderColor = '#10b981';
                e.target.style.boxShadow = '0 0 0 3px rgba(16, 185, 129, 0.1)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = '#e5e7eb';
                e.target.style.boxShadow = 'none';
              }}
            />
            {errors.password2 && (
              <div style={{
                color: '#dc2626',
                fontSize: '12px',
                marginTop: '4px'
              }}>
                {errors.password2.join(' ')}
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              background: '#10b981',
              border: 'none',
              borderRadius: '8px',
              padding: '12px',
              width: '100%',
              color: 'white',
              fontWeight: '500',
              fontSize: '16px',
              margin: '20px 0',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
            onMouseOver={(e) => {
              if (!loading) {
                e.currentTarget.style.background = '#059669';
              }
            }}
            onMouseOut={(e) => {
              if (!loading) {
                e.currentTarget.style.background = '#10b981';
              }
            }}
          >
            {loading ? 'Creando cuenta...' : 'Crear Cuenta'}
          </button>
        </form>
        
        <div style={{
          textAlign: 'center',
          color: '#6b7280',
          fontSize: '14px'
        }}>
          ¿Ya tienes una cuenta? <Link 
            to="/login" 
            style={{
              color: '#10b981',
              textDecoration: 'none'
            }}
            onMouseOver={(e) => e.currentTarget.style.textDecoration = 'underline'}
            onMouseOut={(e) => e.currentTarget.style.textDecoration = 'none'}
          >
            Inicia sesión aquí
          </Link>
        </div>
        
        <div style={{
          textAlign: 'center',
          color: '#9ca3af',
          fontSize: '12px',
          marginTop: '20px'
        }}>
          Al registrarte, aceptas nuestros términos de servicio y política de privacidad
        </div>
      </div>
    </div>
  );
};

export default Register;