import React, { useState, useEffect } from 'react';
import { chatAPI, ContractDetail } from '../services/api';

interface ContractComparisonProps {
  isVisible: boolean;
  onClose: () => void;
  initialContracts?: number[];
}

const ContractComparison: React.FC<ContractComparisonProps> = ({ 
  isVisible, 
  onClose, 
  initialContracts = [] 
}) => {
  const [contracts, setContracts] = useState<ContractDetail[]>([]);
  const [loading, setLoading] = useState(false);
  const [contractIds, setContractIds] = useState<string>('');
  
  useEffect(() => {
    if (initialContracts.length > 0) {
      setContractIds(initialContracts.join(', '));
      loadContracts(initialContracts);
    }
  }, [initialContracts]);

  const loadContracts = async (ids: number[]) => {
    if (ids.length === 0) return;
    
    setLoading(true);
    try {
      const contractPromises = ids.map(id => chatAPI.getContractDetails(id));
      const responses = await Promise.all(contractPromises);
      setContracts(responses.map(r => r.data));
    } catch (error) {
      console.error('Error loading contracts for comparison:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadContracts = () => {
    const ids = contractIds
      .split(',')
      .map(id => parseInt(id.trim()))
      .filter(id => !isNaN(id));
    
    if (ids.length < 2) {
      alert('Ingresa al menos 2 IDs de contrato para comparar');
      return;
    }
    
    if (ids.length > 4) {
      alert('Máximo 4 contratos para comparar');
      return;
    }
    
    loadContracts(ids);
  };

  const formatCurrency = (amount: number | null | undefined) => {
    if (!amount) return 'N/A';
    return new Intl.NumberFormat('es-CL', { 
      style: 'currency', 
      currency: 'CLP' 
    }).format(amount);
  };

  if (!isVisible) return null;

  return (
    <div className="modal show d-block" tabIndex={-1}>
      <div className="modal-dialog modal-xl">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">⚖️ Comparación de Contratos</h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <div className="modal-body">
            {/* Input for contract IDs */}
            <div className="mb-4">
              <label className="form-label">IDs de Contratos (separados por comas):</label>
              <div className="input-group">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Ej: 722, 648, 173"
                  value={contractIds}
                  onChange={(e) => setContractIds(e.target.value)}
                />
                <button 
                  className="btn btn-primary"
                  onClick={handleLoadContracts}
                  disabled={loading}
                >
                  {loading ? 'Cargando...' : 'Comparar'}
                </button>
              </div>
              <div className="form-text">
                Ingresa entre 2 y 4 IDs de contrato para comparar
              </div>
            </div>

            {/* Loading state */}
            {loading && (
              <div className="text-center py-4">
                <div className="spinner-border"></div>
                <p>Cargando contratos...</p>
              </div>
            )}

            {/* Comparison table */}
            {contracts.length >= 2 && !loading && (
              <div className="table-responsive">
                <table className="table table-bordered table-hover">
                  <thead className="table-dark">
                    <tr>
                      <th>Campo</th>
                      {contracts.map((contract) => (
                        <th key={contract.id_contrato} className="text-center">
                          Contrato #{contract.id_contrato}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {/* Personal Information */}
                    <tr className="table-info">
                      <td colSpan={contracts.length + 1}>
                        <strong>📋 Información Personal</strong>
                      </td>
                    </tr>
                    <tr>
                      <td><strong>Nombre Completo</strong></td>
                      {contracts.map((contract) => (
                        <td key={contract.id_contrato}>
                          {contract.persona?.nombre_completo || 'N/A'}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td><strong>RUT</strong></td>
                      {contracts.map((contract) => (
                        <td key={contract.id_contrato}>
                          {contract.persona?.rut || 'N/A'}
                        </td>
                      ))}
                    </tr>
                    
                    {/* Financial Information */}
                    <tr className="table-success">
                      <td colSpan={contracts.length + 1}>
                        <strong>💰 Información Económica</strong>
                      </td>
                    </tr>
                    <tr>
                      <td><strong>Honorario Total Bruto</strong></td>
                      {contracts.map((contract) => (
                        <td key={contract.id_contrato} className="text-end">
                          <strong className="text-success">
                            {formatCurrency(contract.honorario_total_bruto)}
                          </strong>
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td><strong>Viáticos</strong></td>
                      {contracts.map((contract) => (
                        <td key={contract.id_contrato} className="text-end">
                          {typeof contract.viaticos === 'number' 
                            ? formatCurrency(contract.viaticos)
                            : contract.viaticos || 'N/A'
                          }
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td><strong>Tipo de Pago</strong></td>
                      {contracts.map((contract) => (
                        <td key={contract.id_contrato}>
                          {contract.tipo_pago || 'N/A'}
                        </td>
                      ))}
                    </tr>
                    
                    {/* Function Information */}
                    <tr className="table-warning">
                      <td colSpan={contracts.length + 1}>
                        <strong>💼 Información de Función</strong>
                      </td>
                    </tr>
                    <tr>
                      <td><strong>Descripción</strong></td>
                      {contracts.map((contract) => (
                        <td key={contract.id_contrato} style={{ maxWidth: '200px' }}>
                          <div style={{ whiteSpace: 'normal', wordWrap: 'break-word' }}>
                            {contract.funcion?.descripcion || 'N/A'}
                          </div>
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td><strong>Calificación Profesional</strong></td>
                      {contracts.map((contract) => (
                        <td key={contract.id_contrato}>
                          {contract.funcion?.calificacion_profesional || 'N/A'}
                        </td>
                      ))}
                    </tr>
                    
                    {/* Period Information */}
                    <tr className="table-info">
                      <td colSpan={contracts.length + 1}>
                        <strong>📅 Información del Periodo</strong>
                      </td>
                    </tr>
                    <tr>
                      <td><strong>Mes</strong></td>
                      {contracts.map((contract) => (
                        <td key={contract.id_contrato}>
                          {contract.periodo?.mes || 'N/A'}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td><strong>Año</strong></td>
                      {contracts.map((contract) => (
                        <td key={contract.id_contrato}>
                          {contract.periodo?.anho || 'N/A'}
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td><strong>Región</strong></td>
                      {contracts.map((contract) => (
                        <td key={contract.id_contrato}>
                          {contract.periodo?.region || 'N/A'}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            )}

            {contracts.length === 0 && !loading && (
              <div className="text-center py-5">
                <div className="mb-3" style={{ fontSize: '3rem' }}>⚖️</div>
                <h6 className="text-muted">Comparación de Contratos</h6>
                <p className="text-muted">
                  Ingresa los IDs de los contratos que quieres comparar para ver sus diferencias lado a lado.
                </p>
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

export default ContractComparison;