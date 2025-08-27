import React, { useEffect, useRef } from 'react';
import { DashboardData } from '../services/api';

interface AdminChartsProps {
  dashboardData: DashboardData;
}

const AdminCharts: React.FC<AdminChartsProps> = ({ dashboardData }) => {
  const sessionsChartRef = useRef<HTMLCanvasElement>(null);
  const usersChartRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    drawSessionsChart();
    drawUsersChart();
  }, [dashboardData]);

  const drawSessionsChart = () => {
    const canvas = sessionsChartRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const { statistics } = dashboardData;
    const data = [
      { label: 'Activas', value: statistics.sesiones_activas, color: '#28a745' },
      { label: 'Finalizadas', value: statistics.total_sesiones - statistics.sesiones_activas, color: '#6c757d' }
    ];

    const total = data.reduce((sum, item) => sum + item.value, 0);
    if (total === 0) return;

    // Draw pie chart
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 10;

    let currentAngle = -Math.PI / 2;

    data.forEach((item, index) => {
      const sliceAngle = (item.value / total) * 2 * Math.PI;

      // Draw slice
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
      ctx.lineTo(centerX, centerY);
      ctx.fillStyle = item.color;
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Draw label
      const labelAngle = currentAngle + sliceAngle / 2;
      const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7);
      const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7);

      ctx.fillStyle = '#fff';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(`${item.value}`, labelX, labelY);

      currentAngle += sliceAngle;
    });
  };

  const drawUsersChart = () => {
    const canvas = usersChartRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const { active_users } = dashboardData;
    if (active_users.length === 0) return;

    const maxSessions = Math.max(...active_users.map(u => u.num_sesiones));
    const barWidth = (canvas.width - 40) / active_users.length;
    const maxBarHeight = canvas.height - 60;

    active_users.forEach((user, index) => {
      const barHeight = (user.num_sesiones / maxSessions) * maxBarHeight;
      const x = 20 + index * barWidth;
      const y = canvas.height - 40 - barHeight;

      // Draw bar
      ctx.fillStyle = '#007bff';
      ctx.fillRect(x, y, barWidth - 10, barHeight);

      // Draw value label
      ctx.fillStyle = '#333';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(user.num_sesiones.toString(), x + barWidth / 2, y - 5);

      // Draw username label
      ctx.save();
      ctx.translate(x + barWidth / 2, canvas.height - 20);
      ctx.rotate(-Math.PI / 4);
      ctx.textAlign = 'right';
      ctx.fillText(user.username.substring(0, 8), 0, 0);
      ctx.restore();
    });

    // Draw title
    ctx.fillStyle = '#333';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Usuarios Más Activos', canvas.width / 2, 20);
  };

  return (
    <div className="row mb-4">
      <div className="col-md-6">
        <div className="card">
          <div className="card-header">
            <h6 className="card-title mb-0">📊 Estado de Sesiones</h6>
          </div>
          <div className="card-body text-center">
            <canvas
              ref={sessionsChartRef}
              width={300}
              height={200}
              style={{ maxWidth: '100%', height: 'auto' }}
            />
            <div className="mt-3">
              <span className="badge bg-success me-2">
                ● Activas: {dashboardData.statistics.sesiones_activas}
              </span>
              <span className="badge bg-secondary">
                ● Finalizadas: {dashboardData.statistics.total_sesiones - dashboardData.statistics.sesiones_activas}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="col-md-6">
        <div className="card">
          <div className="card-header">
            <h6 className="card-title mb-0">👥 Actividad por Usuario</h6>
          </div>
          <div className="card-body text-center">
            <canvas
              ref={usersChartRef}
              width={300}
              height={200}
              style={{ maxWidth: '100%', height: 'auto' }}
            />
            <small className="text-muted">Top 5 usuarios por número de sesiones</small>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminCharts;