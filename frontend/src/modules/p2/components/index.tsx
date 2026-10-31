import React from 'react';

// Status Badge
export const Badge: React.FC<{
  status: string;
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'neutral';
}> = ({ status, variant }) => {
  let v = variant;
  if (!v) {
    const s = status.toUpperCase();
    if (['PAID', 'COMPLETED', 'ACTIVE', 'RESOLVED', 'SUCCESS'].includes(s)) v = 'success';
    else if (['PARTIALLY_PAID', 'RUNNING', 'PENDING', 'PROMISED', 'TIER 1'].includes(s)) v = 'warning';
    else if (['FAILED', 'CANCELLED', 'DISPUTED', 'TIER 3', 'OVERDUE'].includes(s)) v = 'danger';
    else if (['CONFIRMED', 'TIER 2'].includes(s)) v = 'info';
    else v = 'neutral';
  }

  const styles: Record<string, { bg: string; color: string; border: string }> = {
    success: { bg: '#ECFDF5', color: '#065F46', border: '#A7F3D0' },
    warning: { bg: '#FFFBEB', color: '#92400E', border: '#FDE68A' },
    danger: { bg: '#FEF2F2', color: '#991B1B', border: '#FECACA' },
    info: { bg: '#EFF6FF', color: '#1E40AF', border: '#BFDBFE' },
    neutral: { bg: '#F3F4F6', color: '#374151', border: '#E5E7EB' }
  };

  const style = styles[v] || styles.neutral;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 10px',
        borderRadius: '9999px',
        fontSize: '12px',
        fontWeight: 600,
        backgroundColor: style.bg,
        color: style.color,
        border: `1px solid ${style.border}`,
        textTransform: 'uppercase',
        letterSpacing: '0.025em'
      }}
    >
      {status}
    </span>
  );
};

// UI Card
export const Card: React.FC<{
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ title, subtitle, action, children, style }) => (
  <div
    style={{
      backgroundColor: '#FFFFFF',
      borderRadius: '8px',
      border: '1px solid #E5E7EB',
      boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
      padding: '20px',
      marginBottom: '20px',
      ...style
    }}
  >
    {(title || action) && (
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: subtitle ? '4px' : '16px'
        }}
      >
        {title && <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#111827' }}>{title}</h3>}
        {action && <div>{action}</div>}
      </div>
    )}
    {subtitle && <p style={{ margin: '0 0 16px 0', fontSize: '14px', color: '#6B7280' }}>{subtitle}</p>}
    {children}
  </div>
);

// Stat / Metric Card
export const StatCard: React.FC<{
  title: string;
  value: string | number;
  subtitle?: string;
  badge?: string;
  variant?: 'neutral' | 'success' | 'warning' | 'danger';
}> = ({ title, value, subtitle, badge, variant = 'neutral' }) => {
  const borderColors: Record<string, string> = {
    neutral: '#E5E7EB',
    success: '#10B981',
    warning: '#F59E0B',
    danger: '#EF4444'
  };

  return (
    <div
      style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '8px',
        border: '1px solid #E5E7EB',
        borderLeft: `4px solid ${borderColors[variant]}`,
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
        padding: '16px 20px',
        flex: 1,
        minWidth: '200px'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '13px', fontWeight: 500, color: '#6B7280', textTransform: 'uppercase' }}>
          {title}
        </span>
        {badge && <Badge status={badge} />}
      </div>
      <div style={{ fontSize: '26px', fontWeight: 700, color: '#111827', margin: '8px 0 4px 0' }}>
        {value}
      </div>
      {subtitle && <div style={{ fontSize: '13px', color: '#6B7280' }}>{subtitle}</div>}
    </div>
  );
};

// Accessible Modal
export const Modal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  width?: string;
}> = ({ isOpen, onClose, title, children, width = '550px' }) => {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '20px'
      }}
    >
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '8px',
          width: '100%',
          maxWidth: width,
          maxHeight: '90vh',
          overflowY: 'auto',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid #E5E7EB',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#111827' }}>{title}</h3>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '20px',
              cursor: 'pointer',
              color: '#9CA3AF'
            }}
          >
            ×
          </button>
        </div>
        <div style={{ padding: '20px' }}>{children}</div>
      </div>
    </div>
  );
};
