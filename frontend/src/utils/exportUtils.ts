import { ChatMessage, SessionDetail } from '../services/api';

export type ExportFormat = 'txt' | 'json' | 'html';

export const exportConversation = (session: SessionDetail, format: ExportFormat) => {
  const { session: sessionData, messages } = session;
  const timestamp = new Date().toLocaleString('es-ES');
  
  let content = '';
  let filename = '';
  let mimeType = '';
  
  switch (format) {
    case 'txt':
      content = exportToText(sessionData, messages, timestamp);
      filename = `conversacion-${sessionData.id}-${Date.now()}.txt`;
      mimeType = 'text/plain';
      break;
      
    case 'json':
      content = exportToJSON(session, timestamp);
      filename = `conversacion-${sessionData.id}-${Date.now()}.json`;
      mimeType = 'application/json';
      break;
      
    case 'html':
      content = exportToHTML(sessionData, messages, timestamp);
      filename = `conversacion-${sessionData.id}-${Date.now()}.html`;
      mimeType = 'text/html';
      break;
  }
  
  downloadFile(content, filename, mimeType);
};

const exportToText = (sessionData: any, messages: ChatMessage[], timestamp: string): string => {
  let content = `CONVERSACIÓN EXPORTADA\n`;
  content += `================================\n\n`;
  content += `Nombre: ${sessionData.name || `Conversación ${sessionData.id}`}\n`;
  content += `ID: ${sessionData.id}\n`;
  content += `Creada: ${formatDate(sessionData.created_at)}\n`;
  content += `Estado: ${sessionData.status}\n`;
  content += `Exportado: ${timestamp}\n`;
  content += `Total mensajes: ${messages.length}\n\n`;
  content += `================================\n\n`;
  
  messages.forEach((message, index) => {
    const sender = message.sender === 'usuario' ? 'USUARIO' : 
                   message.sender === 'ia' ? 'IA' : 'SISTEMA';
    content += `[${index + 1}] ${sender} - ${formatDate(message.timestamp)}\n`;
    content += `${message.content}\n\n`;
    content += `---\n\n`;
  });
  
  return content;
};

const exportToJSON = (session: SessionDetail, timestamp: string): string => {
  const exportData = {
    exportInfo: {
      timestamp,
      version: '1.0',
      format: 'json'
    },
    session: session.session,
    messages: session.messages,
    context: session.context
  };
  
  return JSON.stringify(exportData, null, 2);
};

const exportToHTML = (sessionData: any, messages: ChatMessage[], timestamp: string): string => {
  let html = `<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conversación ${sessionData.id}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .message {
            background: white;
            margin: 10px 0;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .message-header {
            font-weight: bold;
            color: #495057;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .message-content {
            white-space: pre-wrap;
            line-height: 1.5;
        }
        .user-message {
            border-left: 4px solid #007bff;
        }
        .ai-message {
            border-left: 4px solid #28a745;
        }
        .system-message {
            border-left: 4px solid #6c757d;
        }
        .timestamp {
            font-size: 0.8em;
            color: #6c757d;
        }
        .export-info {
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 30px;
            padding: 15px;
            border-top: 1px solid #dee2e6;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📝 ${sessionData.name || `Conversación ${sessionData.id}`}</h1>
        <div>
            <strong>ID:</strong> ${sessionData.id}<br>
            <strong>Creada:</strong> ${formatDate(sessionData.created_at)}<br>
            <strong>Estado:</strong> ${sessionData.status}<br>
            <strong>Total mensajes:</strong> ${messages.length}
        </div>
    </div>`;

  messages.forEach((message, index) => {
    const senderClass = message.sender === 'usuario' ? 'user-message' : 
                       message.sender === 'ia' ? 'ai-message' : 'system-message';
    const senderName = message.sender === 'usuario' ? '👤 Usuario' : 
                      message.sender === 'ia' ? '🤖 IA' : '⚙️ Sistema';
    
    html += `
    <div class="message ${senderClass}">
        <div class="message-header">
            <span>${senderName}</span>
            <span class="timestamp">${formatDate(message.timestamp)}</span>
        </div>
        <div class="message-content">${escapeHtml(message.content)}</div>
    </div>`;
  });
  
  html += `
    <div class="export-info">
        Exportado el ${timestamp}<br>
        Chatbot de Recursos Humanos - Universidad
    </div>
</body>
</html>`;
  
  return html;
};

const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'N/A';
  try {
    return new Date(dateString).toLocaleString('es-ES');
  } catch {
    return dateString;
  }
};

const escapeHtml = (text: string): string => {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
};

const downloadFile = (content: string, filename: string, mimeType: string) => {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};