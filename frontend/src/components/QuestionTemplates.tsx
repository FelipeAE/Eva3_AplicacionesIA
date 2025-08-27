import React, { useState } from 'react';

interface Template {
  id: string;
  title: string;
  question: string;
  category: string;
  icon: string;
}

const questionTemplates: Template[] = [
  // Consultas de Honorarios
  { id: '1', title: 'Top 5 Honorarios', question: 'dame el top 5 de honorarios más altos', category: 'Honorarios', icon: '💰' },
  { id: '2', title: 'Honorarios por Mes', question: 'cuáles son los honorarios de [mes]', category: 'Honorarios', icon: '📅' },
  { id: '3', title: 'Promedio Honorarios', question: 'cuál es el promedio de honorarios por región', category: 'Honorarios', icon: '📊' },
  
  // Consultas de Personal
  { id: '4', title: 'Buscar Persona', question: 'busca información de [nombre de la persona]', category: 'Personal', icon: '👤' },
  { id: '5', title: 'Personal por Región', question: 'cuántas personas trabajan en [región]', category: 'Personal', icon: '🗺️' },
  { id: '6', title: 'Funciones Activas', question: 'qué funciones están activas este mes', category: 'Personal', icon: '💼' },
  
  // Consultas de Contratos
  { id: '7', title: 'Contratos Activos', question: 'cuántos contratos están activos', category: 'Contratos', icon: '📋' },
  { id: '8', title: 'Contratos por Función', question: 'contratos relacionados con [tipo de función]', category: 'Contratos', icon: '🔍' },
  { id: '9', title: 'Estadísticas Mensuales', question: 'estadísticas de contratos del mes actual', category: 'Contratos', icon: '📈' },
  
  // Consultas Financieras
  { id: '10', title: 'Total Viáticos', question: 'cuál es el total de viáticos pagados', category: 'Finanzas', icon: '🧾' },
  { id: '11', title: 'Costos por Región', question: 'costos totales por región este año', category: 'Finanzas', icon: '💸' },
  { id: '12', title: 'Presupuesto Mensual', question: 'cuál es el gasto total en honorarios de [mes]', category: 'Finanzas', icon: '💳' }
];

interface QuestionTemplatesProps {
  onSelectTemplate: (question: string) => void;
  isVisible: boolean;
  onClose: () => void;
}

const QuestionTemplates: React.FC<QuestionTemplatesProps> = ({ onSelectTemplate, isVisible, onClose }) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  if (!isVisible) return null;

  const categories = ['all', ...Array.from(new Set(questionTemplates.map(t => t.category)))];
  
  const filteredTemplates = questionTemplates.filter(template => {
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    const matchesSearch = template.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.question.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleTemplateSelect = (template: Template) => {
    onSelectTemplate(template.question);
    onClose();
  };

  return (
    <div className="modal show d-block" tabIndex={-1}>
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">💡 Templates de Preguntas</h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <div className="modal-body">
            {/* Search and Filter */}
            <div className="row mb-3">
              <div className="col-md-8">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Buscar templates..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <div className="col-md-4">
                <select 
                  className="form-select"
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                >
                  <option value="all">Todas las categorías</option>
                  {categories.slice(1).map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Templates Grid */}
            <div className="row">
              {filteredTemplates.map((template) => (
                <div key={template.id} className="col-md-6 col-lg-4 mb-3">
                  <div className="card h-100 shadow-sm" style={{ cursor: 'pointer' }}
                       onClick={() => handleTemplateSelect(template)}>
                    <div className="card-body d-flex flex-column">
                      <div className="d-flex align-items-start mb-2">
                        <span className="fs-4 me-2">{template.icon}</span>
                        <div className="flex-grow-1">
                          <h6 className="card-title mb-1">{template.title}</h6>
                          <small className="text-muted">{template.category}</small>
                        </div>
                      </div>
                      <p className="card-text small flex-grow-1">
                        "{template.question}"
                      </p>
                      <div className="text-end">
                        <small className="text-primary">Clic para usar →</small>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {filteredTemplates.length === 0 && (
              <div className="text-center py-4">
                <p className="text-muted">No se encontraron templates que coincidan con tu búsqueda.</p>
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

export default QuestionTemplates;