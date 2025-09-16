import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token && config.headers) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface ChatSession {
  id: number;
  nombre: string;
  fecha_creacion: string;
  finalizada: boolean;
  tiene_pregunta_bloqueada: boolean;
}

export interface SessionDetail {
  session: {
    id: number;
    name: string;
    status: string;
    created_at: string;
    finished_at?: string;
    readonly: boolean;
    has_blocked_questions: boolean;
  };
  messages: ChatMessage[];
  context: {
    active_context?: string;
  };
}

export interface ChatMessage {
  id: number;
  sender: string;
  content: string;
  timestamp: string;
  has_source_data: boolean;
  metadata?: {
    ids?: number[];
    tipo?: string;
    [key: string]: any;
  };
}

export interface SendMessageResponse {
  success: boolean;
  message: string;
  response?: string;
  has_source_data?: boolean;
  metadata?: {
    id_contrato?: number[];
    id_persona?: number[];
    [key: string]: any;
  };
  error?: string;
}

export interface LoginResponse {
  token: string;
  user: {
    id: number;
    username: string;
    is_staff: boolean;
  };
}

export interface AuthCheckResponse {
  id: number;
  username: string;
  is_staff: boolean;
}

export interface ContractDetail {
  id_contrato: number;
  honorario_total_bruto?: number;
  tipo_pago: string;
  viaticos?: number;
  observaciones?: string;
  enlace_funciones?: string;
  persona: {
    id: number;
    nombre_completo: string;
    rut?: string;
  };
  funcion: {
    id: number;
    descripcion: string;
    calificacion_profesional?: string;
  };
  periodo: {
    id: number;
    mes: string;
    anho: number;
    region: string;
  };
}

export interface ContractsBulkResponse {
  contracts: ContractDetail[];
}

export interface Context {
  id: number;
  nombre: string;
  prompt: string;
  activo: boolean;
  fecha_creacion: string;
}

export interface ExcludedTerm {
  id: number;
  termino: string;
  fecha_creacion: string;
}

export interface DashboardStatistics {
  total_usuarios: number;
  usuarios_activos: number;
  total_sesiones: number;
  sesiones_activas: number;
  total_mensajes: number;
  preguntas_bloqueadas: number;
}

export interface ActiveUser {
  id: number;
  username: string;
  num_sesiones: number;
  last_login: string | null;
}

export interface RecentSession {
  id: number;
  name: string;
  user: string;
  created: string | null;
  status: string;
}

export interface BlockedQuestion {
  id: number;
  question: string;
  reason: string;
  user: string;
  date: string | null;
}

export interface FrequentTerm {
  term: string;
  count: number;
}

export interface DashboardData {
  statistics: DashboardStatistics;
  active_users: ActiveUser[];
  recent_sessions: RecentSession[];
  blocked_questions: BlockedQuestion[];
  frequent_excluded_terms: FrequentTerm[];
  active_context?: Context | null;
}

export interface CreateContextRequest {
  nombre: string;
  prompt: string;
}

export interface AddTermRequest {
  termino: string;
}

export const authAPI = {
  login: (credentials: LoginCredentials) =>
    api.post<LoginResponse>('/auth/login/', credentials),
  
  logout: () =>
    api.post('/auth/logout/'),
  
  checkAuth: () =>
    api.get<AuthCheckResponse>('/auth/check/'),
};

export const chatAPI = {
  getSessions: () =>
    api.get<ChatSession[]>('/sessions/'),
  
  createSession: () =>
    api.post<{success: boolean; session_id: number; message: string}>('/sessions/create/'),
  
  getSession: (id: number) =>
    api.get<SessionDetail>(`/sessions/${id}/`),
  
  getSessionDetail: (id: number) =>
    api.get<SessionDetail>(`/sessions/${id}/`),
  
  // Messages are included in session detail, no separate endpoint needed
  
  deleteSession: (id: number) =>
    api.delete<{success: boolean; message: string}>(`/sessions/${id}/delete/`),
  
  finalizeSession: (id: number) =>
    api.post<{success: boolean; message: string}>(`/sessions/${id}/finalize/`),
  
  sendMessage: (sessionId: number, message: string) =>
    api.post<SendMessageResponse>(`/sessions/${sessionId}/message/`, { message }),
  
  getContractDetails: (contractId: number) =>
    api.get<ContractDetail>(`/contrato/${contractId}/`),
  
  getContractDetailsBulk: (contractIds: number[]) =>
    api.post<ContractsBulkResponse>('/contratos/bulk/', { contract_ids: contractIds }),
};

export const adminAPI = {
  // Dashboard
  getDashboard: () =>
    api.get<DashboardData>('/admin/dashboard/'),
  
  // Context management
  getContexts: () =>
    api.get<Context[]>('/admin/contexts/'),
  
  createContext: (data: CreateContextRequest) =>
    api.post<{success: boolean; message: string; context_id?: number}>('/admin/contexts/create/', data),
  
  activateContext: (contextId: number) =>
    api.post<{success: boolean; message: string}>(`/admin/contexts/${contextId}/activate/`),
  
  deactivateContext: (contextId: number) =>
    api.post<{success: boolean; message: string}>(`/admin/contexts/${contextId}/deactivate/`),
  
  deleteContext: (contextId: number) =>
    api.delete<{success: boolean; message: string}>(`/admin/contexts/${contextId}/delete/`),
};

export const settingsAPI = {
  // User settings - excluded terms
  getExcludedTerms: () =>
    api.get<ExcludedTerm[]>('/settings/excluded-terms/'),
  
  addExcludedTerm: (data: AddTermRequest) =>
    api.post<{success: boolean; message: string; term_id?: number}>('/settings/excluded-terms/add/', data),
  
  deleteExcludedTerm: (termId: number) =>
    api.delete<{success: boolean; message: string}>(`/settings/excluded-terms/${termId}/delete/`),
};

export default api;