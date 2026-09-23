import React, { useState, useEffect } from 'react';
import { LogOut, FilePlus, Shield, LayoutDashboard, CheckSquare, ChevronDown, ChevronUp, User, ShieldCheck, Search, PanelLeftClose, PanelLeftOpen, Bell, CheckCheck, Lock, Eye, Download, FileText } from 'lucide-react';
import { NFAFormView } from './NFAFormView';
import { NFADashboardView } from './NFADashboardView';
import { AdminConfigView } from './AdminConfigView';
import { NFAPendingApprovalsView } from './NFAPendingApprovalsView';
import { AuditorPortalView } from './AuditorPortalView';

interface DashboardHeaderProps {
  user: any;
  onLogout: () => void;
}

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({ user, onLogout }) => {
  const hasRole = (roleName: string) => {
    if (!user) return false;
    const target = roleName.toUpperCase();

    const checkString = (str: any) => {
      if (!str) return false;
      const val = str.toString().toUpperCase();
      if (val === target) return true;
      if (target === 'BUYER' && (val.includes('BUYER') || val.includes('INITIATOR'))) return true;
      if (target === 'APPROVER' && val.includes('APPROVER')) return true;
      if (target === 'ADMIN' && (val.includes('ADMIN') || val.includes('SYSTEM ADMINISTRATOR'))) return true;
      if (target === 'AUDITOR' && val.includes('AUDITOR')) return true;
      return val.includes(target);
    };

    if (user.role_name && checkString(user.role_name)) return true;
    if (user.role && checkString(user.role)) return true;
    if (Array.isArray(user.roles)) {
      return user.roles.some((r: any) => checkString(r));
    }
    return false;
  };

  const isBuyer = hasRole('BUYER') || hasRole('BUYER_USER');
  const isApprover = hasRole('APPROVER') || hasRole('APPROVER_USER');
  const isAdmin = hasRole('ADMIN') || hasRole('ADMIN_USER');
  const isAuditor = hasRole('AUDITOR') || hasRole('AUDITOR_USER');

  const mgmtRoles: string[] = [];
  if (isAdmin) mgmtRoles.push('Admin');
  if (isApprover) mgmtRoles.push('Approver');
  if (isAuditor) mgmtRoles.push('Auditor');
  const mgmtHeaderTitle = mgmtRoles.length > 0 ? mgmtRoles.join(' / ') : 'Management';

  // Default viewMode: AUDITOR -> AUDITOR, APPROVER -> PENDING_APPROVALS, BUYER/ADMIN -> MY_NFAS
  const defaultMode = isAuditor && !isAdmin && !isBuyer ? 'AUDITOR' : isApprover && !isBuyer && !isAdmin ? 'PENDING_APPROVALS' : 'MY_NFAS';

  const [viewMode, setViewMode] = useState<'MY_NFAS' | 'ASSIGNED_NFAS' | 'CREATE_NFA' | 'ADMIN' | 'PENDING_APPROVALS' | 'AUDITOR'>(defaultMode);
  const [editingDraftId, setEditingDraftId] = useState<string | null>(null);

  // In-App Notification States
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [notificationsList, setNotificationsList] = useState<any[]>([]);
  const [isNotificationBoxOpen, setIsNotificationBoxOpen] = useState(false);
  const [selectedNotificationNFA, setSelectedNotificationNFA] = useState<any | null>(null);
  

  const handleNotificationItemClick = async (item: any) => {
    // 1. Mark single notification as read & decrement unread count
    if (!item.is_read) {
      try {
        await fetch('http://127.0.0.1:8000/api/user/notifications', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ notification_id: item.notification_id }),
        });
        setUnreadCount((prev) => Math.max(0, prev - 1));
        setNotificationsList((prev) =>
          prev.map((n) => (n.notification_id === item.notification_id ? { ...n, is_read: true } : n))
        );
      } catch (e) {
        console.error('Failed to mark single notification as read', e);
      }
    }

    setIsNotificationBoxOpen(false);

    // 2. Open NFA Details Modal (with fallback for legacy notifications)
    let targetNfaId = item.nfa_request_id;

    if (!targetNfaId) {
      const match = (item.title + ' ' + item.message).match(/(NFA-[\w-]+)/);
      try {
        const listRes = await fetch(`http://127.0.0.1:8000/api/nfa/list?user_id=${user.user_id}`);
        const listData = await listRes.json();
        if (listData.isSuccess && listData.nfas && listData.nfas.length > 0) {
          const found = match ? listData.nfas.find((n: any) => n.nfa_number === match[1]) : null;
          targetNfaId = found ? found.nfa_request_id : listData.nfas[0].nfa_request_id;
        }
      } catch (err) {
        console.error('Fallback list fetch failed', err);
      }
    }

    if (targetNfaId) {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/nfa/${targetNfaId}`);
        const data = await res.json();
        if (data.isSuccess) {
          setSelectedNotificationNFA(data.nfa);
        }
      } catch (e) {
        console.error('Failed to fetch NFA details for notification', e);
      }
    }
  };

  const fetchUserNotifications = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/user/notifications?user_id=${user.user_id}`);
      const data = await res.json();
      if (data.isSuccess) {
        setUnreadCount(data.unread_count || 0);
        setNotificationsList(data.notifications || []);
      }
    } catch (e) {
      console.error('Failed to fetch user notifications', e);
    }
  };

  useEffect(() => {
    fetchUserNotifications();
    const interval = setInterval(fetchUserNotifications, 15000); // Auto-refresh every 15s
    return () => clearInterval(interval);
  }, [user.user_id]);

  const handleMarkAllAsRead = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/user/notifications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.user_id }),
      });
      const data = await res.json();
      if (data.isSuccess) {
        setUnreadCount(0);
        setNotificationsList((prev) => prev.map((n) => ({ ...n, is_read: true })));
      }
    } catch (e) {
      console.error('Failed to mark notifications as read', e);
    }
  };
  const [returnedNfaId, setReturnedNfaId] = useState<string | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [pendingCount, setPendingCount] = useState<number>(0);

  // Dropdown Collapsible Accordion States
  const [isUserMenuOpen, setIsUserMenuOpen] = useState<boolean>(true);
  const [isAdminMenuOpen, setIsAdminMenuOpen] = useState<boolean>(true);

  const getInitials = (name: string) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map((part) => part[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  };

  const fetchPendingCount = async () => {
    if (!user || !user.user_id) return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/nfa/pending-approvals?user_id=${user.user_id}`);
      const data = await res.json();
      if (data.isSuccess && data.pending_requests) {
        setPendingCount(data.pending_requests.length);
      }
    } catch (e) {
      // Ignore poll errors
    }
  };

  useEffect(() => {
    fetchPendingCount();
    const interval = setInterval(fetchPendingCount, 15000);
    return () => clearInterval(interval);
  }, [user]);

  const handleEditDraft = (nfaId: string) => {
    setEditingDraftId(nfaId);
    setReturnedNfaId(null);
    setViewMode('CREATE_NFA');
  };

  const handleEditReturned = (nfaId: string) => {
    setReturnedNfaId(nfaId);
    setEditingDraftId(null);
    setViewMode('CREATE_NFA');
  };

  const handleCreateNew = () => {
    setEditingDraftId(null);
    setReturnedNfaId(null);
    setViewMode('CREATE_NFA');
  };

  const displayRole = Array.isArray(user.roles) ? user.roles.join(', ') : (user.role_name || user.role || 'USER');

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f8fafc' }}>
      {/* Role-Based Vertical Left Sidebar */}
      <aside
        style={{
          width: isSidebarCollapsed ? '0px' : '260px',
          background: '#0f172a',
          color: 'white',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: isSidebarCollapsed ? '0px' : '24px 16px',
          borderRight: isSidebarCollapsed ? 'none' : '1px solid #1e293b',
          flexShrink: 0,
          opacity: isSidebarCollapsed ? 0 : 1,
          visibility: isSidebarCollapsed ? 'hidden' : 'visible',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          overflow: 'hidden',
          position: 'sticky',
          top: 0,
          height: '100vh',
        }}
      >
        <div style={{ flex: 1, overflowY: 'auto', paddingBottom: '16px', scrollbarWidth: 'thin' }}>
          {/* Logo Brand Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '32px', paddingLeft: isSidebarCollapsed ? '4px' : '8px', justifyContent: isSidebarCollapsed ? 'center' : 'flex-start' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '10px',
                background: '#2563eb',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(37,99,235,0.4)',
                flexShrink: 0,
              }}
            >
              <Shield size={20} color="white" />
            </div>
            {!isSidebarCollapsed && (
              <div>
                <div style={{ fontWeight: 800, fontSize: '16px', letterSpacing: '-0.02em', fontFamily: 'Outfit, sans-serif' }}>
                  NFA Workflow
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 500 }}>Enterprise Portal</div>
              </div>
            )}
          </div>

          {/* Sidebar Accordion Groups */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

            {/* GROUP 1: USER / BUYER DROPDOWN ACCORDION */}
            {(isBuyer || isAdmin) && (
              <div>
                <button
                  type="button"
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    width: '100%',
                    padding: '8px 10px',
                    background: 'transparent',
                    border: 'none',
                    color: '#94a3b8',
                    fontWeight: 700,
                    fontSize: '12px',
                    cursor: 'pointer',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <User size={16} color="#38bdf8" />
                    <span>User Portal</span>
                  </div>
                  {isUserMenuOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>

                {isUserMenuOpen && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '6px', paddingLeft: '8px' }}>
                    <button
                      onClick={() => { setEditingDraftId(null); setReturnedNfaId(null); setViewMode('MY_NFAS'); }}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        width: '100%',
                        padding: '10px 12px',
                        borderRadius: '10px',
                        border: 'none',
                        background: viewMode === 'MY_NFAS' ? '#2563eb' : 'transparent',
                        color: viewMode === 'MY_NFAS' ? 'white' : '#cbd5e1',
                        fontWeight: viewMode === 'MY_NFAS' ? 700 : 500,
                        fontSize: '13px',
                        cursor: 'pointer',
                        textAlign: 'left',
                        transition: 'all 0.2s',
                      }}
                    >
                      <LayoutDashboard size={16} />
                      <span>My NFA Requests</span>
                    </button>

                    <button
                      onClick={handleCreateNew}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        width: '100%',
                        padding: '10px 12px',
                        borderRadius: '10px',
                        border: 'none',
                        background: viewMode === 'CREATE_NFA' ? '#2563eb' : 'transparent',
                        color: viewMode === 'CREATE_NFA' ? 'white' : '#cbd5e1',
                        fontWeight: viewMode === 'CREATE_NFA' ? 700 : 500,
                        fontSize: '13px',
                        cursor: 'pointer',
                        textAlign: 'left',
                        transition: 'all 0.2s',
                      }}
                    >
                      <FilePlus size={16} />
                      <span>+ Create New NFA</span>
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* GROUP 2: APPROVER / ADMIN ACCORDION */}
            {(isApprover || isAdmin || isAuditor) && (
              <div>
                <button
                  type="button"
                  onClick={() => setIsAdminMenuOpen(!isAdminMenuOpen)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    width: '100%',
                    padding: '8px 10px',
                    background: 'transparent',
                    border: 'none',
                    color: '#94a3b8',
                    fontWeight: 700,
                    fontSize: '12px',
                    cursor: 'pointer',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <ShieldCheck size={16} color="#a855f7" />
                    <span>{mgmtHeaderTitle}</span>
                  </div>
                  {isAdminMenuOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>

                {isAdminMenuOpen && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '6px', paddingLeft: '8px' }}>
                    {(isApprover || isAdmin) && (
                      <button
                        onClick={() => { setEditingDraftId(null); setReturnedNfaId(null); setViewMode('PENDING_APPROVALS'); }}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          width: '100%',
                          padding: '10px 12px',
                          borderRadius: '10px',
                          border: 'none',
                          background: viewMode === 'PENDING_APPROVALS' ? '#2563eb' : 'transparent',
                          color: viewMode === 'PENDING_APPROVALS' ? 'white' : '#cbd5e1',
                          fontWeight: viewMode === 'PENDING_APPROVALS' ? 700 : 500,
                          fontSize: '13px',
                          cursor: 'pointer',
                          textAlign: 'left',
                          transition: 'all 0.2s',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <CheckSquare size={16} />
                          <span>Pending Approvals</span>
                        </div>
                        {pendingCount > 0 && (
                          <span
                            style={{
                              padding: '2px 8px',
                              borderRadius: '10px',
                              background: '#ef4444',
                              color: 'white',
                              fontSize: '11px',
                              fontWeight: 800,
                            }}
                          >
                            {pendingCount}
                          </span>
                        )}
                      </button>
                    )}

                    {(isApprover || isAdmin) && (
                      <button
                        onClick={() => { setEditingDraftId(null); setReturnedNfaId(null); setViewMode('ASSIGNED_NFAS'); }}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          width: '100%',
                          padding: '10px 12px',
                          borderRadius: '10px',
                          border: 'none',
                          background: viewMode === 'ASSIGNED_NFAS' ? '#2563eb' : 'transparent',
                          color: viewMode === 'ASSIGNED_NFAS' ? 'white' : '#cbd5e1',
                          fontWeight: viewMode === 'ASSIGNED_NFAS' ? 700 : 500,
                          fontSize: '13px',
                          cursor: 'pointer',
                          textAlign: 'left',
                          transition: 'all 0.2s',
                        }}
                      >
                        <LayoutDashboard size={16} />
                        <span>Assigned NFA Requests</span>
                      </button>
                    )}

                    {(isAuditor || isAdmin) && (
                      <button
                        onClick={() => { setEditingDraftId(null); setReturnedNfaId(null); setViewMode('AUDITOR'); }}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          width: '100%',
                          padding: '10px 12px',
                          borderRadius: '10px',
                          border: 'none',
                          background: viewMode === 'AUDITOR' ? '#2563eb' : 'transparent',
                          color: viewMode === 'AUDITOR' ? 'white' : '#cbd5e1',
                          fontWeight: viewMode === 'AUDITOR' ? 700 : 500,
                          fontSize: '13px',
                          cursor: 'pointer',
                          textAlign: 'left',
                          transition: 'all 0.2s',
                        }}
                      >
                        <Search size={16} />
                        <span>Auditor Compliance Portal</span>
                      </button>
                    )}

                    {isAdmin && (
                      <button
                        onClick={() => { setEditingDraftId(null); setReturnedNfaId(null); setViewMode('ADMIN'); }}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          width: '100%',
                          padding: '10px 12px',
                          borderRadius: '10px',
                          border: 'none',
                          background: viewMode === 'ADMIN' ? '#2563eb' : 'transparent',
                          color: viewMode === 'ADMIN' ? 'white' : '#cbd5e1',
                          fontWeight: viewMode === 'ADMIN' ? 700 : 500,
                          fontSize: '13px',
                          cursor: 'pointer',
                          textAlign: 'left',
                          transition: 'all 0.2s',
                        }}
                      >
                        <Shield size={16} />
                        <span>Admin Control Panel</span>
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}

          </div>
        </div>

        {/* Footer User Info & Sign Out */}
        <div style={{ borderTop: '1px solid #1e293b', paddingTop: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px', paddingLeft: '4px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                background: '#2563eb',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '13px',
              }}
            >
              {getInitials(user.full_name)}
            </div>
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontWeight: 700, fontSize: '13px', color: 'white', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                {user.full_name}
              </div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                {user.employee_code} • {user.department_name}
              </div>
            </div>
          </div>

          <button
            onClick={onLogout}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              width: '100%',
              padding: '10px',
              borderRadius: '10px',
              border: '1px solid #334155',
              background: '#1e293b',
              color: '#f87171',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            <LogOut size={16} /> Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Body */}
      <main style={{ flex: 1, padding: '32px', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', paddingBottom: '16px', borderBottom: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button
              onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
              title={isSidebarCollapsed ? "Expand Left Menu" : "Fullscreen View (Collapse Left Menu)"}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 14px',
                borderRadius: '10px',
                border: '1px solid #cbd5e1',
                background: isSidebarCollapsed ? '#2563eb' : 'white',
                color: isSidebarCollapsed ? 'white' : '#334155',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
              }}
            >
              {isSidebarCollapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
              <span>{isSidebarCollapsed ? 'Show Menu' : 'Fullscreen'}</span>
            </button>

            <div style={{ fontSize: '13px', color: '#64748b', fontWeight: 600 }}>
              Department: <strong style={{ color: '#0f172a' }}>{user.department_name}</strong>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, padding: '4px 10px', borderRadius: '12px', background: '#eff6ff', color: '#2563eb', textTransform: 'uppercase' }}>
              {displayRole}
            </span>

            {/* Notification Bell Button & Popover Container */}
            <div style={{ position: 'relative' }}>
              <button
                type="button"
                onClick={() => setIsNotificationBoxOpen(!isNotificationBoxOpen)}
                style={{
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '38px',
                  height: '38px',
                  borderRadius: '50%',
                  border: '1px solid #cbd5e1',
                  background: isNotificationBoxOpen ? '#eff6ff' : 'white',
                  color: isNotificationBoxOpen ? '#2563eb' : '#475569',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                }}
                title="Notifications"
              >
                <Bell size={18} />
                {unreadCount > 0 && (
                  <span
                    style={{
                      position: 'absolute',
                      top: '-2px',
                      right: '-2px',
                      background: '#ef4444',
                      color: 'white',
                      fontSize: '10px',
                      fontWeight: 800,
                      width: '18px',
                      height: '18px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      border: '2px solid white',
                      boxShadow: '0 2px 4px rgba(239,68,68,0.3)',
                    }}
                  >
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </button>

              {/* Floating Dropdown Notification Box */}
              {isNotificationBoxOpen && (
                <div
                  style={{
                    position: 'absolute',
                    right: 0,
                    top: '48px',
                    width: '360px',
                    maxHeight: '480px',
                    background: 'white',
                    borderRadius: '16px',
                    border: '1px solid #e2e8f0',
                    boxShadow: '0 20px 40px rgba(0,0,0,0.15)',
                    zIndex: 1000,
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                  }}
                >
                  {/* Box Header */}
                  <div
                    style={{
                      padding: '14px 18px',
                      background: '#f8fafc',
                      borderBottom: '1px solid #e2e8f0',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Bell size={16} color="#2563eb" />
                      <strong style={{ fontSize: '14px', color: '#0f172a' }}>Notifications</strong>
                      {unreadCount > 0 && (
                        <span style={{ fontSize: '11px', background: '#dbeafe', color: '#1e40af', padding: '2px 8px', borderRadius: '10px', fontWeight: 700 }}>
                          {unreadCount} new
                        </span>
                      )}
                    </div>

                    {unreadCount > 0 && (
                      <button
                        type="button"
                        onClick={handleMarkAllAsRead}
                        style={{
                          fontSize: '12px',
                          fontWeight: 700,
                          color: '#2563eb',
                          background: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}
                      >
                        <CheckCheck size={14} /> Mark All Read
                      </button>
                    )}
                  </div>

                  {/* Notifications List Body */}
                  <div style={{ overflowY: 'auto', flex: 1, padding: '8px 0', maxHeight: '380px' }}>
                    {notificationsList.length === 0 ? (
                      <div style={{ padding: '32px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>
                        No notifications found.
                      </div>
                    ) : (
                      notificationsList.map((item: any) => (
                        <div
                          key={item.notification_id}
                          onClick={() => handleNotificationItemClick(item)}
                          style={{
                            padding: '12px 18px',
                            borderBottom: '1px solid #f1f5f9',
                            background: item.is_read ? 'white' : '#eff6ff',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                          }}
                          className="hover:bg-blue-50"
                        >
                          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px', marginBottom: '4px' }}>
                            <span style={{ fontWeight: 700, fontSize: '13px', color: item.is_read ? '#334155' : '#0f172a' }}>
                              {item.title}
                            </span>
                            {!item.is_read && (
                              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#2563eb', flexShrink: 0, marginTop: '4px' }} />
                            )}
                          </div>
                          <p style={{ fontSize: '12px', color: '#475569', margin: '0 0 6px 0', lineHeight: 1.4 }}>
                            {item.message}
                          </p>
                          <span style={{ fontSize: '10px', color: '#94a3b8', fontWeight: 500 }}>
                            {new Date(item.created_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {viewMode === 'CREATE_NFA' ? (
          <NFAFormView
            user_id={user.user_id}
            draft_id={editingDraftId}
            returned_nfa_id={returnedNfaId}
            onBack={() => { setEditingDraftId(null); setReturnedNfaId(null); setViewMode('MY_NFAS'); }}
            onSubmitted={() => { setEditingDraftId(null); setReturnedNfaId(null); setViewMode('MY_NFAS'); }}
          />
        ) : viewMode === 'ADMIN' ? (
          <AdminConfigView />
        ) : viewMode === 'AUDITOR' ? (
          <AuditorPortalView />
        ) : viewMode === 'PENDING_APPROVALS' ? (
          <NFAPendingApprovalsView
            user={user}
            onRefreshBadge={fetchPendingCount}
          />
        ) : viewMode === 'ASSIGNED_NFAS' ? (
          <NFADashboardView
            user={user}
            roleMode="APPROVER"
            onEditDraft={handleEditDraft}
            onEditReturned={handleEditReturned}
          />
        ) : (
          <NFADashboardView
            user={user}
            roleMode="BUYER"
            onEditDraft={handleEditDraft}
            onEditReturned={handleEditReturned}
          />
        )}
        {/* Notification NFA Detail Modal */}
        {selectedNotificationNFA && (
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1100, padding: '20px' }}>
            <div style={{ background: 'white', borderRadius: '24px', width: '100%', maxWidth: '840px', maxHeight: '90vh', overflowY: 'auto', padding: '32px', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)' }}>
              {/* Modal Header */}
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '24px', paddingBottom: '16px', borderBottom: '1px solid #e2e8f0' }}>
                <div>
                  <span style={{ fontSize: '11px', fontWeight: 800, padding: '4px 10px', borderRadius: '10px', background: '#dbeafe', color: '#1e40af', textTransform: 'uppercase' }}>
                    {selectedNotificationNFA.current_status}
                  </span>
                  <h2 style={{ fontSize: '22px', fontWeight: 800, color: '#0f172a', margin: '8px 0 4px 0', fontFamily: 'Outfit, sans-serif' }}>
                    {selectedNotificationNFA.nfa_number} — {selectedNotificationNFA.title}
                  </h2>
                  <p style={{ fontSize: '13px', color: '#64748b', margin: 0 }}>
                    Buyer: <strong>{selectedNotificationNFA.buyer_full_name || selectedNotificationNFA.buyer_name || (typeof selectedNotificationNFA.buyer === 'object' ? selectedNotificationNFA.buyer?.full_name : selectedNotificationNFA.buyer) || 'Buyer'}</strong> • Department: <strong>{selectedNotificationNFA.department_name}</strong>
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedNotificationNFA(null)}
                  style={{ background: '#f1f5f9', border: 'none', borderRadius: '50%', width: '32px', height: '32px', fontSize: '16px', cursor: 'pointer', color: '#64748b' }}
                >
                  ✕
                </button>
              </div>

              {/* Modal Content */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {/* Financial Summary */}
                <div style={{ padding: '16px 20px', background: '#f8fafc', borderRadius: '14px', border: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>ESTIMATED TOTAL AMOUNT</span>
                    <div style={{ fontSize: '24px', fontWeight: 800, color: '#166534', fontFamily: 'Outfit, sans-serif' }}>
                      ₹{parseFloat(selectedNotificationNFA.total_amount_usd || '0').toLocaleString('en-IN', { minimumFractionDigits: 2 })} <span style={{ fontSize: '14px', color: '#64748b' }}>INR</span>
                    </div>
                  </div>
                  {selectedNotificationNFA.vendor_name && (
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>SELECTED VENDOR</span>
                      <div style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>{selectedNotificationNFA.vendor_name}</div>
                    </div>
                  )}
                </div>

                {/* Justification & Impact */}
                <div>
                  <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '6px' }}>Business Justification</h4>
                  <div style={{ padding: '14px', background: '#ffffff', borderRadius: '10px', border: '1px solid #e2e8f0', fontSize: '13px', color: '#334155', lineHeight: 1.5 }}>
                    {selectedNotificationNFA.business_justification || 'No justification provided.'}
                  </div>
                </div>

                {selectedNotificationNFA.commercial_impact && (
                  <div>
                    <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '6px' }}>Commercial Impact</h4>
                    <div style={{ padding: '14px', background: '#ffffff', borderRadius: '10px', border: '1px solid #e2e8f0', fontSize: '13px', color: '#334155', lineHeight: 1.5 }}>
                      {selectedNotificationNFA.commercial_impact}
                    </div>
                  </div>
                )}

                {/* Attached Documents (Option A Version-Grouped Cards) */}
                <div>
                  <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '10px' }}>Attached Documents & Revisions</h4>
                  {!selectedNotificationNFA.attachments || selectedNotificationNFA.attachments.length === 0 ? (
                    <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '10px', fontSize: '13px', color: '#94a3b8', textAlign: 'center' }}>
                      No document attachments linked to this request.
                    </div>
                  ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
                      {selectedNotificationNFA.attachments.map((att: any) => (
                        <div key={att.attachment_id} style={{ padding: '12px 14px', borderRadius: '12px', border: '1px solid #cbd5e1', background: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
                            <FileText size={20} color="#2563eb" style={{ flexShrink: 0 }} />
                            <div style={{ overflow: 'hidden' }}>
                              <div style={{ fontWeight: 700, fontSize: '12px', color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {att.file_name}
                              </div>
                              <div style={{ fontSize: '10px', color: '#64748b' }}>
                                Version {att.version_number || 1} • {att.file_size ? `${(att.file_size / (1024 * 1024)).toFixed(2)} MB` : 'File'}
                              </div>
                            </div>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                            {att.file_url && (
                              <>
                                <a href={`http://127.0.0.1:8000${att.file_url}`} target="_blank" rel="noreferrer" style={{ padding: '5px 8px', borderRadius: '6px', background: '#eff6ff', color: '#2563eb', fontSize: '11px', fontWeight: 700, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                  <Eye size={12} /> View
                                </a>
                                <a href={`http://127.0.0.1:8000${att.file_url}`} download style={{ padding: '5px 8px', borderRadius: '6px', background: '#f1f5f9', color: '#475569', fontSize: '11px', fontWeight: 700, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                  <Download size={12} />
                                </a>
                              </>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Return Reason / Revision Required Card */}
                {(selectedNotificationNFA.current_status === 'RETURNED' || selectedNotificationNFA.return_reason) && (
                  <div style={{ marginBottom: '20px', padding: '16px 20px', background: '#fef3c7', borderRadius: '14px', border: '1px solid #fde68a' }}>
                    <div style={{ fontSize: '11px', fontWeight: 800, color: '#b45309', textTransform: 'uppercase', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      ⚠️ REASON FOR RETURN / REVISION REQUIRED
                      {selectedNotificationNFA.returned_by_name && (
                        <span style={{ color: '#92400e', fontWeight: 600 }}>(By {selectedNotificationNFA.returned_by_name})</span>
                      )}
                    </div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: '#78350f', lineHeight: 1.5 }}>
                      "{selectedNotificationNFA.return_reason || 'Request returned for revision.'}"
                    </div>
                  </div>
                )}

                {/* Approver Chain Timeline */}
                <div>
                  <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '10px' }}>Assigned Approver Chain</h4>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflowX: 'auto', padding: '4px 0' }}>
                    {selectedNotificationNFA.approver_chain?.map((step: any, idx: number) => {
                      const isPast = step.level < selectedNotificationNFA.current_level;
                      const isActive = step.level === selectedNotificationNFA.current_level;
                      const isReassigned = step.is_reassigned;
                      return (
                        <React.Fragment key={step.level}>
                          <div style={{ padding: '8px 12px', borderRadius: '10px', border: isReassigned ? '1px dashed #f59e0b' : isActive ? '2px solid #2563eb' : '1px solid #cbd5e1', background: isReassigned ? '#fffbeb' : isActive ? '#eff6ff' : isPast ? '#f8fafc' : '#ffffff', minWidth: '140px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '10px', fontWeight: 800, marginBottom: '2px' }}>
                              <span>Level {step.level}</span>
                              {isPast && <span style={{ color: '#94a3b8' }}><Lock size={9} /></span>}
                              {isActive && <span style={{ color: '#2563eb' }}>⭐ Active</span>}
                              {isReassigned && <span style={{ color: '#b45309' }}>🔄 Reassigned</span>}
                            </div>
                            <div style={{ fontWeight: 700, fontSize: '12px', color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {step.full_name}
                            </div>
                            <div style={{ fontSize: '10px', color: '#64748b' }}>
                              {step.department_name || 'General'}
                            </div>
                          </div>
                          {idx < selectedNotificationNFA.approver_chain.length - 1 && (
                            <span style={{ color: '#cbd5e1', fontWeight: 800 }}>→</span>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => setSelectedNotificationNFA(null)}
                  style={{ padding: '10px 24px', background: '#2563eb', color: 'white', border: 'none', borderRadius: '10px', fontWeight: 700, fontSize: '13px', cursor: 'pointer' }}
                >
                  Close Details
                </button>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
};
