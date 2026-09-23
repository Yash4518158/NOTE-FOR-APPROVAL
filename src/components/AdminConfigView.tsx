import React, { useState, useEffect } from 'react';
import { Save, AlertCircle, Mail, Bell, Eye, Download, UserCheck, RefreshCw, Lock, Search, CheckCircle2, ListChecks, Info } from 'lucide-react';

export const AdminConfigView: React.FC = () => {
  useEffect(() => {
    fetchStatusMasterList();
  }, []);

  const fetchStatusMasterList = async () => {
    setLoadingStatuses(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/admin/status-master');
      const data = await res.json();
      if (data.isSuccess) {
        setStatusMasterList(data.statuses || []);
      }
    } catch (e) {
      console.error('Failed fetching status master entries', e);
    } finally {
      setLoadingStatuses(false);
    }
  };

  const [activeTab, setActiveTab] = useState<'MODE' | 'RETURN' | 'NOTIFICATIONS' | 'REASSIGNMENT' | 'STATUS_MASTER'>('STATUS_MASTER');
  const [departments, setDepartments] = useState<any[]>([]);
  const [selectedDeptId, setSelectedDeptId] = useState<number>(1);
  const [approverMode, setApproverMode] = useState<'MANUAL' | 'DYNAMIC'>('DYNAMIC');

  // Return Mode State
  const [returnMode, setReturnMode] = useState<'RETURN_TO_INITIATOR' | 'RETURN_TO_PREVIOUS_APPROVER'>('RETURN_TO_INITIATOR');

  // Email Notification Templates State
  const [masterEmailFlag, setMasterEmailFlag] = useState<boolean>(true);
  const [masterInAppFlag, setMasterInAppFlag] = useState<boolean>(true);
  const [notificationTemplates, setNotificationTemplates] = useState<any[]>([]);

  // Reassignment Tab State
  const [reassignNFAs, setReassignNFAs] = useState<any[]>([]);
  const [loadingReassignNFAs, setLoadingReassignNFAs] = useState(false);

  // Status Master (mst_status) State
  const [statusMasterList, setStatusMasterList] = useState<any[]>([]);
  const [loadingStatuses, setLoadingStatuses] = useState(false);
  const [searchReassignInput, setSearchReassignInput] = useState('');
  const [searchReassignQuery, setSearchReassignQuery] = useState('');

  // 300ms Debounce for Table Search Bar
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchReassignQuery(searchReassignInput);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchReassignInput]);

  const handleDownloadAuditDocumentation = () => {
    if (!reassignNFAs || filteredReassignNFAs.length === 0) return;

    const headers = [
      'NFA Number',
      'Title',
      'Buyer Name',
      'Department',
      'Amount (INR)',
      'Current Level',
      'Current Status',
      'Assigned Approver Chain Sequence',
      'Reassigned Approver Log Details'
    ];

    const rows = filteredReassignNFAs.map((nfa) => {
      const chainStr = nfa.approver_chain
        ? nfa.approver_chain.map((s: any) => `Level ${s.level}: ${s.full_name} (${s.department_name || 'General'})`).join(' | ')
        : 'N/A';

      const reassignedSteps = nfa.approver_chain ? nfa.approver_chain.filter((s: any) => s.is_reassigned) : [];
      const reassignedLogStr = reassignedSteps.length > 0
        ? reassignedSteps.map((s: any) => `[Level ${s.level} Replaced: ${s.old_approver_name || 'Previous'} -> ${s.full_name}. Reason: ${s.reassignment_reason || 'Admin Reassignment'}]`).join('; ')
        : 'No Reassignments in Chain';

      return [
        `"${nfa.nfa_number || ''}"`,
        `"${(nfa.title || '').replace(/"/g, '""')}"`,
        `"${nfa.buyer_name || ''}"`,
        `"${nfa.department_name || ''}"`,
        `"${parseFloat(nfa.total_amount_usd || '0').toLocaleString('en-IN', { minimumFractionDigits: 2 })}"`,
        `"Level ${nfa.current_level}"`,
        `"${nfa.current_status}"`,
        `"${chainStr.replace(/"/g, '""')}"`,
        `"${reassignedLogStr.replace(/"/g, '""')}"`
      ].join(',');
    });

    const csvContent = '\uFEFF' + [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `NFA_Approver_Reassignment_Audit_Report_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filteredReassignNFAs = reassignNFAs.filter((nfa) => {
    if (!searchReassignQuery) return true;
    const q = searchReassignQuery.toLowerCase().trim();
    const matchNumber = nfa.nfa_number?.toLowerCase().includes(q);
    const matchTitle = nfa.title?.toLowerCase().includes(q);
    const matchBuyer = nfa.buyer_name?.toLowerCase().includes(q);
    const matchDept = nfa.department_name?.toLowerCase().includes(q);
    const matchApprovers = nfa.approver_chain?.some((s: any) =>
      s.full_name?.toLowerCase().includes(q) ||
      s.username?.toLowerCase().includes(q) ||
      s.old_approver_name?.toLowerCase().includes(q)
    );
    return matchNumber || matchTitle || matchBuyer || matchDept || matchApprovers;
  });
  const [selectedReassignNFA, setSelectedReassignNFA] = useState<any | null>(null);
  const [selectedInspectChainNFA, setSelectedInspectChainNFA] = useState<any | null>(null);
  const [targetLevel, setTargetLevel] = useState<number>(1);
  const [searchEmployeeQuery, setSearchEmployeeQuery] = useState('');
  const [employeeSearchResults, setEmployeeSearchResults] = useState<any[]>([]);
  const [selectedNewUser, setSelectedNewUser] = useState<any | null>(null);
  const [reassignReason, setReassignReason] = useState('Employee Resignation');
  const [submittingReassignment, setSubmittingReassignment] = useState(false);

  const fetchReassignNFAs = async () => {
    setLoadingReassignNFAs(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/admin/reassignment-list');
      const data = await res.json();
      if (data.isSuccess) {
        setReassignNFAs(data.nfas || []);
      }
    } catch (e) {
      console.error('Failed fetching reassignment NFAs', e);
    } finally {
      setLoadingReassignNFAs(false);
    }
  };

  // 300ms Debounce for Employee API Search Bar
  useEffect(() => {
    if (!searchEmployeeQuery || searchEmployeeQuery.length < 2) {
      setEmployeeSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/employees/search?query=${encodeURIComponent(searchEmployeeQuery)}`);
        const data = await res.json();
        if (data.isSuccess) {
          setEmployeeSearchResults(data.employees || []);
        }
      } catch (e) {
        console.error('Employee search failed', e);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchEmployeeQuery]);

  const handleSearchEmployee = (query: string) => {
    setSearchEmployeeQuery(query);
  };

  const handleExecuteReassignment = async () => {
    if (!selectedReassignNFA || !selectedNewUser) return;
    setSubmittingReassignment(true);
    setMsg(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/admin/reassign-approver', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nfa_request_id: selectedReassignNFA.nfa_request_id,
          level: targetLevel,
          new_user_id: selectedNewUser.user_id,
          reason: reassignReason || 'Employee Resignation'
        }),
      });
      const data = await res.json();
      if (data.isSuccess) {
        setMsg({ text: data.message || 'Approver reassigned successfully!', isError: false });
        setSelectedReassignNFA(null);
        setSelectedNewUser(null);
        setSearchEmployeeQuery('');
        setEmployeeSearchResults([]);
        fetchReassignNFAs();
      } else {
        setMsg({ text: data.message || 'Failed reassigning approver.', isError: true });
      }
    } catch (e) {
      setMsg({ text: 'Network error executing reassignment.', isError: true });
    } finally {
      setSubmittingReassignment(false);
    }
  };

  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ text: string; isError: boolean } | null>(null);

  const fetchDepartments = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/admin/departments');
      const data = await res.json();
      if (data.isSuccess && data.departments) {
        setDepartments(data.departments);
        if (data.departments.length > 0 && !selectedDeptId) {
          setSelectedDeptId(data.departments[0].department_id);
          setApproverMode(data.departments[0].approver_mode);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchNotificationTemplates = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/admin/notification-templates');
      const data = await res.json();
      if (data.isSuccess) {
        setMasterEmailFlag(data.master_enable_email_notifications);
        if (data.master_enable_inapp_notifications !== undefined) {
          setMasterInAppFlag(data.master_enable_inapp_notifications);
        }
        setNotificationTemplates(data.templates || []);
      }
    } catch (e) {
      console.error('Failed loading notification templates', e);
    }
  };

  const fetchReturnConfig = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/admin/global-config');
      const data = await res.json();
      if (data.isSuccess && data.global_return_mode) {
        setReturnMode(data.global_return_mode);
      }
    } catch (e) {
      console.error('Failed loading global return mode config', e);
    }
  };

  useEffect(() => {
    fetchDepartments();
    fetchReturnConfig();
    fetchNotificationTemplates();
    fetchReassignNFAs();
  }, []);


  const handleToggleTemplateFlag = async (eventType: string, targetFlag: 'email' | 'inapp', currentStatus: boolean) => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/admin/notification-templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: eventType, target_flag: targetFlag, is_active: !currentStatus }),
      });
      const data = await res.json();
      if (data.isSuccess) {
        fetchNotificationTemplates();
      }
    } catch (e) {
      console.error('Failed toggling template flag', e);
    }
  };

  const handleDeptChange = (deptId: number) => {
    setSelectedDeptId(deptId);
    const deptObj = departments.find((d) => d.department_id === deptId);
    if (deptObj) {
      setApproverMode(deptObj.approver_mode);
    }
  };

  const handleSaveMode = async () => {
    setSaving(true);
    setMsg(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/admin/department-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ department_id: selectedDeptId, approver_mode: approverMode }),
      });
      const data = await res.json();
      if (data.isSuccess) {
        setMsg({ text: 'Department Approver Mode updated successfully.', isError: false });
        fetchDepartments();
      } else {
        setMsg({ text: data.message || 'Error updating mode.', isError: true });
      }
    } catch (e) {
      setMsg({ text: 'Network error updating mode.', isError: true });
    } finally {
      setSaving(false);
    }
  };

  const handleSaveReturnMode = async () => {
    setSaving(true);
    setMsg(null);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/admin/return-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ return_mode: returnMode }),
      });
      const data = await res.json();
      if (data.isSuccess) {
        setMsg({ text: 'Global Return Behavior Configuration updated.', isError: false });
      } else {
        setMsg({ text: data.message || 'Error saving return mode.', isError: true });
      }
    } catch (e) {
      setMsg({ text: 'Network error updating return mode.', isError: true });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', margin: 0, fontFamily: 'Outfit, sans-serif' }}>
          Admin Control Panel & System Configuration
        </h1>
        <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0 0' }}>
          Configure Department Approver Modes, Return Routing Policies, and Notification Settings
        </p>
      </div>

      {msg && (
        <div className={`alert-box ${msg.isError ? 'alert-error' : 'alert-success'}`} style={{ marginBottom: '20px' }}>
          <AlertCircle size={18} />
          <span>{msg.text}</span>
        </div>
      )}

      {/* Tabs Bar */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', borderBottom: '1px solid #e2e8f0', paddingBottom: '12px' }}>
        <button
          onClick={() => setActiveTab('MODE')}
          style={{
            padding: '10px 20px',
            borderRadius: '10px',
            border: 'none',
            background: activeTab === 'MODE' ? '#2563eb' : 'transparent',
            color: activeTab === 'MODE' ? 'white' : '#64748b',
            fontWeight: activeTab === 'MODE' ? 700 : 500,
            fontSize: '13px',
            cursor: 'pointer',
          }}
        >
          Department Approver Mode
        </button>

        <button
          onClick={() => setActiveTab('RETURN')}
          style={{
            padding: '10px 20px',
            borderRadius: '10px',
            border: 'none',
            background: activeTab === 'RETURN' ? '#2563eb' : 'transparent',
            color: activeTab === 'RETURN' ? 'white' : '#64748b',
            fontWeight: activeTab === 'RETURN' ? 700 : 500,
            fontSize: '13px',
            cursor: 'pointer',
          }}
        >
          Return Behavior Policy
        </button>

        <button
          onClick={() => setActiveTab('NOTIFICATIONS')}
          style={{
            padding: '10px 20px',
            borderRadius: '10px',
            border: 'none',
            background: activeTab === 'NOTIFICATIONS' ? '#2563eb' : 'transparent',
            color: activeTab === 'NOTIFICATIONS' ? 'white' : '#64748b',
            fontWeight: activeTab === 'NOTIFICATIONS' ? 700 : 500,
            fontSize: '13px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <Mail size={16} /> Notification Settings
        </button>

        <button
          onClick={() => { setActiveTab('REASSIGNMENT'); fetchReassignNFAs(); }}
          style={{
            padding: '10px 20px',
            borderRadius: '10px',
            border: 'none',
            background: activeTab === 'REASSIGNMENT' ? '#2563eb' : 'transparent',
            color: activeTab === 'REASSIGNMENT' ? 'white' : '#64748b',
            fontWeight: activeTab === 'REASSIGNMENT' ? 700 : 500,
            fontSize: '13px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <UserCheck size={16} /> Approver Reassignment
        </button>

        <button
          onClick={() => setActiveTab('STATUS_MASTER')}
          style={{
            padding: '10px 20px',
            borderRadius: '10px',
            border: 'none',
            background: activeTab === 'STATUS_MASTER' ? '#2563eb' : 'transparent',
            color: activeTab === 'STATUS_MASTER' ? 'white' : '#64748b',
            fontWeight: activeTab === 'STATUS_MASTER' ? 700 : 500,
            fontSize: '13px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <ListChecks size={16} /> Status Master (mst_status)
        </button>
      </div>

      
      {/* TAB: STATUS MASTER (mst_status) */}
      {activeTab === 'STATUS_MASTER' && (
        <div style={{ background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0', padding: '28px', boxShadow: '0 4px 12px rgba(0,0,0,0.03)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Info size={18} color="#2563eb" />
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a', margin: 0, fontFamily: 'Outfit, sans-serif' }}>
                  Status Master Table (mst_status) & Workflow Lifecycle Rules
                </h3>
              </div>
              <p style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
                Centralized master table for all NFA request states, audit action events, badge colors, and system definitions.
              </p>
            </div>
            <div style={{ padding: '6px 14px', borderRadius: '20px', background: '#eff6ff', color: '#2563eb', fontWeight: 700, fontSize: '12px', border: '1px solid #bfdbfe' }}>
              SQL Server: mst_status
            </div>
          </div>

          <div style={{ overflowX: 'auto', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  <th style={{ padding: '12px 16px', fontWeight: 700 }}>ID</th>
                  <th style={{ padding: '12px 16px', fontWeight: 700 }}>Status Code</th>
                  <th style={{ padding: '12px 16px', fontWeight: 700 }}>Category</th>
                  <th style={{ padding: '12px 16px', fontWeight: 700 }}>Display Badge Preview</th>
                  <th style={{ padding: '12px 16px', fontWeight: 700 }}>System Description & Rules</th>
                </tr>
              </thead>
              <tbody>
                {loadingStatuses ? (
                  <tr>
                    <td colSpan={5} style={{ padding: '30px', textAlign: 'center', color: '#94a3b8' }}>
                      Loading master statuses from mst_status...
                    </td>
                  </tr>
                ) : statusMasterList.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ padding: '30px', textAlign: 'center', color: '#94a3b8' }}>
                      No status entries found in mst_status table.
                    </td>
                  </tr>
                ) : (
                  statusMasterList.map((st) => (
                    <tr key={st.status_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '14px 16px', fontWeight: 700, color: '#64748b' }}>
                        #{st.status_id}
                      </td>
                      <td style={{ padding: '14px 16px', fontWeight: 800, color: '#0f172a', fontFamily: 'monospace' }}>
                        {st.status_code}
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <span style={{ fontSize: '10px', fontWeight: 700, padding: '3px 8px', borderRadius: '12px', background: st.category === 'REQUEST_STATUS' ? '#e0f2fe' : '#fef3c7', color: st.category === 'REQUEST_STATUS' ? '#0369a1' : '#b45309' }}>
                          {st.category}
                        </span>
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <span style={{ padding: '4px 12px', borderRadius: '20px', fontSize: '11px', fontWeight: 800, background: st.badge_bg_color, color: st.badge_text_color, border: '1px solid rgba(0,0,0,0.05)' }}>
                          {st.display_label}
                        </span>
                      </td>
                      <td style={{ padding: '14px 16px', color: '#475569', lineHeight: 1.4 }}>
                        {st.description}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}


      {/* TAB 1: APPROVER MODE */}
      {activeTab === 'MODE' && (
        <div style={{ background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0', padding: '28px', boxShadow: '0 4px 12px rgba(0,0,0,0.03)' }}>
          <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a', margin: '0 0 16px 0' }}>
            Configure Department Approver Mode
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '600px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#475569', marginBottom: '6px' }}>SELECT DEPARTMENT</label>
              <select
                className="form-input"
                style={{ padding: '12px', borderRadius: '10px', fontSize: '14px', width: '100%' }}
                value={selectedDeptId}
                onChange={(e) => handleDeptChange(parseInt(e.target.value))}
              >
                {departments.map((d) => (
                  <option key={d.department_id} value={d.department_id}>
                    {d.department_name} ({d.department_code}) — [{d.approver_mode === 'MANUAL' ? '🟦 MANUAL PRE-SET CHAIN' : '🟩 DYNAMIC APPROVERS'}]
                  </option>
                ))}
              </select>

              <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Active Status:</span>
                <span style={{
                  padding: '4px 12px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: 700,
                  background: approverMode === 'MANUAL' ? '#eff6ff' : '#dcfce7',
                  color: approverMode === 'MANUAL' ? '#1d4ed8' : '#15803d',
                  border: `1px solid ${approverMode === 'MANUAL' ? '#bfdbfe' : '#86efac'}`
                }}>
                  {approverMode === 'MANUAL' ? '🟦 Manual Pre-set Chain Active' : '🟩 Dynamic Approvers Active'}
                </span>
              </div>
            </div>


            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#475569', marginBottom: '8px' }}>APPROVAL MODE</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div
                  onClick={() => setApproverMode('DYNAMIC')}
                  style={{
                    padding: '16px',
                    borderRadius: '12px',
                    border: approverMode === 'DYNAMIC' ? '2px solid #2563eb' : '1px solid #cbd5e1',
                    background: approverMode === 'DYNAMIC' ? '#eff6ff' : 'white',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>Dynamic Approvers</div>
                  <p style={{ fontSize: '12px', color: '#64748b', margin: '4px 0 0 0' }}>Buyer specifies approver chain sequence at submission</p>
                </div>

                <div
                  onClick={() => setApproverMode('MANUAL')}
                  style={{
                    padding: '16px',
                    borderRadius: '12px',
                    border: approverMode === 'MANUAL' ? '2px solid #2563eb' : '1px solid #cbd5e1',
                    background: approverMode === 'MANUAL' ? '#eff6ff' : 'white',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a' }}>Manual Pre-set Chain</div>
                  <p style={{ fontSize: '12px', color: '#64748b', margin: '4px 0 0 0' }}>Admin enforces fixed approver chain for department</p>
                </div>
              </div>
            </div>

            <button
              onClick={handleSaveMode}
              disabled={saving}
              style={{
                padding: '12px 24px',
                background: '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '10px',
                fontWeight: 700,
                fontSize: '14px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                width: 'fit-content',
              }}
            >
              <Save size={16} /> {saving ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>
        </div>
      )}

      {/* TAB 2: RETURN BEHAVIOR */}
      {activeTab === 'RETURN' && (
        <div style={{ background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0', padding: '28px', boxShadow: '0 4px 12px rgba(0,0,0,0.03)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a', margin: 0, fontFamily: 'Outfit, sans-serif' }}>
                Configure Global Return Behavior
              </h3>
              <p style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
                System-wide routing policy determining where returned NFA requests go upon Buyer resubmission.
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Active Global Policy:</span>
              <span style={{
                padding: '6px 14px',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: 700,
                background: returnMode === 'RETURN_TO_INITIATOR' ? '#eff6ff' : '#f0fdf4',
                color: returnMode === 'RETURN_TO_INITIATOR' ? '#1d4ed8' : '#15803d',
                border: `1px solid ${returnMode === 'RETURN_TO_INITIATOR' ? '#bfdbfe' : '#86efac'}`
              }}>
                {returnMode === 'RETURN_TO_INITIATOR' ? '🟦 Return to Initiator (Buyer)' : '🟩 Return to Previous Level Approver'}
              </span>
            </div>
          </div>


          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '600px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div
                onClick={() => setReturnMode('RETURN_TO_INITIATOR')}
                style={{
                  padding: '18px',
                  borderRadius: '14px',
                  border: returnMode === 'RETURN_TO_INITIATOR' ? '2px solid #2563eb' : '1px solid #cbd5e1',
                  background: returnMode === 'RETURN_TO_INITIATOR' ? '#eff6ff' : 'white',
                  cursor: 'pointer',
                }}
              >
                <div style={{ fontWeight: 700, fontSize: '15px', color: '#0f172a' }}>Return to Initiator (Buyer)</div>
                <p style={{ fontSize: '12px', color: '#64748b', margin: '4px 0 0 0' }}>
                  Returned NFA goes back to Buyer. Resubmission restarts approval chain at Level 1.
                </p>
              </div>

              <div
                onClick={() => setReturnMode('RETURN_TO_PREVIOUS_APPROVER')}
                style={{
                  padding: '18px',
                  borderRadius: '14px',
                  border: returnMode === 'RETURN_TO_PREVIOUS_APPROVER' ? '2px solid #2563eb' : '1px solid #cbd5e1',
                  background: returnMode === 'RETURN_TO_PREVIOUS_APPROVER' ? '#eff6ff' : 'white',
                  cursor: 'pointer',
                }}
              >
                <div style={{ fontWeight: 700, fontSize: '15px', color: '#0f172a' }}>Return to Previous Level Approver</div>
                <p style={{ fontSize: '12px', color: '#64748b', margin: '4px 0 0 0' }}>
                  Returned NFA goes back to the returning approver level upon Buyer resubmission.
                </p>
              </div>
            </div>

            <button
              onClick={handleSaveReturnMode}
              disabled={saving}
              style={{
                padding: '12px 24px',
                background: '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '10px',
                fontWeight: 700,
                fontSize: '14px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                width: 'fit-content',
              }}
            >
              <Save size={16} /> {saving ? 'Saving...' : 'Save Return Policy'}
            </button>
          </div>
        </div>
      )}

      {/* TAB 3: NOTIFICATION SETTINGS (INDEPENDENT DUAL TOGGLES) */}
      {activeTab === 'REASSIGNMENT' && (
        <div style={{ background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0', padding: '24px' }}>
          <div style={{ marginBottom: '24px' }}>
            <div style={{ marginBottom: '16px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0, fontFamily: 'Outfit, sans-serif' }}>
                Active NFA Approver Chain Reassignment
              </h2>
              <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0 0' }}>
                Replace resigned or inactive employees in active in-progress approval chains. Past evaluated levels remain locked.
              </p>
            </div>

            {/* Search Bar & Audit Export Control Bar */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
              <div style={{ position: 'relative', flex: 1, minWidth: '280px' }}>
                <Search size={16} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
                <input
                  type="text"
                  placeholder="Search by NFA #, Buyer, Approver name, Title, or Dept..."
                  value={searchReassignInput}
                  onChange={(e) => setSearchReassignInput(e.target.value)}
                  style={{ width: '100%', padding: '10px 16px 10px 40px', borderRadius: '10px', border: '1px solid #cbd5e1', fontSize: '13px', outline: 'none' }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <button
                  onClick={handleDownloadAuditDocumentation}
                  disabled={filteredReassignNFAs.length === 0}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '10px 18px', background: reassignNFAs.length > 0 ? '#166534' : '#94a3b8', color: 'white', border: 'none', borderRadius: '10px', fontWeight: 700, fontSize: '13px', cursor: reassignNFAs.length > 0 ? 'pointer' : 'not-allowed' }}
                  title="Download full CSV Audit Documentation report of pending requests and approver reassignment logs"
                >
                  <Download size={15} /> Export Audit Documentation
                </button>

                <button
                  onClick={fetchReassignNFAs}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '10px 16px', background: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1', borderRadius: '10px', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
                >
                  <RefreshCw size={14} className={loadingReassignNFAs ? 'spin' : ''} /> Refresh List
                </button>
              </div>
            </div>
          </div>

          {loadingReassignNFAs ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Loading active NFAs...</div>
          ) : filteredReassignNFAs.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#64748b', background: '#f8fafc', borderRadius: '12px' }}>
              No active in-progress NFAs requiring approver reassignment at this time.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
                <thead>
                  <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569', fontWeight: 700 }}>
                    <th style={{ padding: '12px 16px' }}>NFA NUMBER</th>
                    <th style={{ padding: '12px 16px' }}>TITLE</th>
                    <th style={{ padding: '12px 16px' }}>BUYER</th>
                    <th style={{ padding: '12px 16px' }}>ACTIVE LEVEL</th>
                    <th style={{ padding: '12px 16px' }}>APPROVER CHAIN</th>
                    <th style={{ padding: '12px 16px', textAlign: 'right' }}>ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredReassignNFAs.map((nfa) => (
                    <tr key={nfa.nfa_request_id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: '14px 16px', fontWeight: 700, color: '#2563eb' }}>{nfa.nfa_number}</td>
                      <td style={{ padding: '14px 16px', fontWeight: 600, color: '#0f172a' }}>{nfa.title}</td>
                      <td style={{ padding: '14px 16px', color: '#475569' }}>{nfa.buyer_name}</td>
                      <td style={{ padding: '14px 16px' }}>
                        <span style={{ padding: '4px 10px', borderRadius: '10px', background: '#e0f2fe', color: '#0369a1', fontWeight: 700, fontSize: '12px' }}>
                          Level {nfa.current_level}
                        </span>
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <button
                          type="button"
                          onClick={() => setSelectedInspectChainNFA(nfa)}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '8px',
                            padding: '6px 14px',
                            background: '#eff6ff',
                            border: '1px solid #bfdbfe',
                            borderRadius: '10px',
                            color: '#1e40af',
                            fontSize: '12px',
                            fontWeight: 700,
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                          }}
                          title="Click to view full approver chain wizard & step details"
                        >
                          <span>{nfa.approver_chain.length} Steps</span>
                          <span style={{ fontSize: '10px', background: '#2563eb', color: 'white', padding: '2px 6px', borderRadius: '6px' }}>
                            ⭐ L{nfa.current_level} Active
                          </span>
                          <Eye size={14} style={{ opacity: 0.8 }} />
                        </button>
                      </td>
                      <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                        <button
                          onClick={() => {
                            setSelectedReassignNFA(nfa);
                            const activeStep = nfa.approver_chain.find((s: any) => s.level >= nfa.current_level);
                            if (activeStep) setTargetLevel(activeStep.level);
                            else setTargetLevel(nfa.current_level);
                            setSelectedNewUser(null);
                            setSearchEmployeeQuery('');
                            setEmployeeSearchResults([]);
                          }}
                          style={{ padding: '6px 14px', background: '#2563eb', color: 'white', border: 'none', borderRadius: '8px', fontWeight: 700, fontSize: '12px', cursor: 'pointer' }}
                        >
                          Reassign
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Approver Chain Wizard Modal */}
          {selectedInspectChainNFA && (
            <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '20px' }}>
              <div style={{ background: 'white', borderRadius: '24px', width: '100%', maxWidth: '780px', padding: '28px', boxShadow: '0 20px 40px rgba(0,0,0,0.2)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
                  <div>
                    <span style={{ fontSize: '11px', fontWeight: 800, padding: '3px 10px', borderRadius: '10px', background: '#e0f2fe', color: '#0369a1', textTransform: 'uppercase' }}>
                      Approver Chain Wizard
                    </span>
                    <h3 style={{ fontSize: '20px', fontWeight: 800, color: '#0f172a', margin: '6px 0 0 0', fontFamily: 'Outfit, sans-serif' }}>
                      {selectedInspectChainNFA.nfa_number} — {selectedInspectChainNFA.title}
                    </h3>
                    <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0 0' }}>
                      Initiator: <strong>{selectedInspectChainNFA.buyer_name}</strong> • Amount: <strong style={{ color: '#166534' }}>₹{parseFloat(selectedInspectChainNFA.total_amount_usd || '0').toLocaleString('en-IN', { minimumFractionDigits: 2 })}</strong>
                    </p>
                  </div>

                  <button
                    onClick={() => setSelectedInspectChainNFA(null)}
                    style={{ background: 'transparent', border: 'none', fontSize: '18px', cursor: 'pointer', color: '#94a3b8' }}
                  >
                    ✕
                  </button>
                </div>

                {/* Horizontal Connected Stepper Wizard Nodes */}
                <div style={{ marginBottom: '24px', padding: '20px', background: '#f8fafc', borderRadius: '16px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '16px' }}>
                    APPROVAL SEQUENCE WORKFLOW ({selectedInspectChainNFA.approver_chain.length} STEPS)
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflowX: 'auto', padding: '4px 0' }}>
                    {selectedInspectChainNFA.approver_chain.map((step: any, idx: number) => {
                      const isPast = step.level < selectedInspectChainNFA.current_level;
                      const isActive = step.level === selectedInspectChainNFA.current_level;
                      const isReassigned = step.is_reassigned;

                      return (
                        <React.Fragment key={step.level}>
                          <div
                            style={{
                              display: 'flex',
                              flexDirection: 'column',
                              padding: '12px 16px',
                              borderRadius: '14px',
                              fontSize: '12px',
                              minWidth: '165px',
                              background: isReassigned ? '#fffbeb' : isActive ? '#eff6ff' : isPast ? '#ffffff' : '#ffffff',
                              color: isReassigned ? '#b45309' : isActive ? '#1e40af' : isPast ? '#64748b' : '#0f172a',
                              border: isReassigned ? '1px dashed #f59e0b' : isActive ? '2px solid #2563eb' : '1px solid #cbd5e1',
                              boxShadow: isActive ? '0 4px 14px rgba(37,99,235,0.18)' : 'none',
                              transition: 'all 0.2s',
                            }}
                            title={isReassigned ? `Replaced ${step.old_approver_name || 'previous approver'}. Reason: ${step.reassignment_reason || 'Admin Reassignment'}` : ''}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '6px', marginBottom: '6px' }}>
                              <span style={{
                                fontSize: '10px',
                                fontWeight: 800,
                                padding: '2px 6px',
                                borderRadius: '6px',
                                background: isActive ? '#2563eb' : isPast ? '#e2e8f0' : '#e0f2fe',
                                color: isActive ? 'white' : isPast ? '#475569' : '#0369a1',
                              }}>
                                Level {step.level}
                              </span>

                              {isPast && <span style={{ fontSize: '10px', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '2px' }}><Lock size={10} /> Locked</span>}
                              {isActive && <span style={{ fontSize: '10px', color: '#2563eb', fontWeight: 800 }}>⭐ Active</span>}
                              {isReassigned && <span style={{ fontSize: '10px', background: '#f59e0b', color: 'white', padding: '1px 5px', borderRadius: '4px', fontWeight: 700 }}>🔄 Reassigned</span>}
                            </div>

                            <div style={{ fontWeight: 700, fontSize: '14px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '150px' }}>
                              {step.full_name}
                            </div>

                            <div style={{ fontSize: '11px', opacity: 0.8, marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {step.department_name || 'General'}
                            </div>
                          </div>

                          {idx < selectedInspectChainNFA.approver_chain.length - 1 && (
                            <span style={{ color: '#cbd5e1', fontWeight: 800, fontSize: '18px', userSelect: 'none' }}>→</span>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px' }}>
                  <button
                    onClick={() => setSelectedInspectChainNFA(null)}
                    style={{ padding: '10px 20px', background: '#f1f5f9', color: '#475569', border: 'none', borderRadius: '10px', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
                  >
                    Close Wizard
                  </button>

                  <button
                    onClick={() => {
                      const targetNFA = selectedInspectChainNFA;
                      setSelectedInspectChainNFA(null);
                      setSelectedReassignNFA(targetNFA);
                      const activeStep = targetNFA.approver_chain.find((s: any) => s.level >= targetNFA.current_level);
                      if (activeStep) setTargetLevel(activeStep.level);
                      else setTargetLevel(targetNFA.current_level);
                      setSelectedNewUser(null);
                      setSearchEmployeeQuery('');
                      setEmployeeSearchResults([]);
                    }}
                    style={{ padding: '10px 20px', background: '#2563eb', color: 'white', border: 'none', borderRadius: '10px', fontWeight: 700, fontSize: '13px', cursor: 'pointer' }}
                  >
                    Reassign Approver in Chain
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Reassignment Modal */}
          {selectedReassignNFA && (
            <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '20px' }}>
              <div style={{ background: 'white', borderRadius: '20px', width: '100%', maxWidth: '540px', padding: '28px', boxShadow: '0 20px 40px rgba(0,0,0,0.2)' }}>
                <h3 style={{ fontSize: '20px', fontWeight: 800, color: '#0f172a', margin: '0 0 4px 0', fontFamily: 'Outfit, sans-serif' }}>
                  Reassign Approver in Chain
                </h3>
                <p style={{ fontSize: '13px', color: '#64748b', margin: '0 0 20px 0' }}>
                  NFA: <strong style={{ color: '#2563eb' }}>{selectedReassignNFA.nfa_number}</strong> — {selectedReassignNFA.title}
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {/* Select Level Step */}
                  {/* Current Active Level Approver Info */}
                  <div style={{ padding: '12px 16px', background: '#eff6ff', borderRadius: '12px', border: '1px solid #bfdbfe' }}>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: '#1e40af', textTransform: 'uppercase' }}>Current Active Level Approver *</div>
                    <div style={{ fontWeight: 800, fontSize: '14px', color: '#1e3a8a', marginTop: '2px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span>Level {selectedReassignNFA.current_level}: {selectedReassignNFA.approver_chain?.find((s: any) => s.level === selectedReassignNFA.current_level)?.full_name || 'Approver'}</span>
                      <span style={{ fontSize: '11px', background: '#2563eb', color: 'white', padding: '2px 8px', borderRadius: '6px', fontWeight: 700 }}>⭐ Active</span>
                    </div>
                  </div>

                  {/* Buyer / Initiator Info */}
                  <div style={{ padding: '12px 16px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Buyer / Initiator *</div>
                    <div style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a', marginTop: '2px' }}>
                      {selectedReassignNFA.buyer_name}
                    </div>
                  </div>

                  {/* Replacement Employee Search */}
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '6px' }}>
                      Search & Select Replacement Active Employee *
                    </label>
                    <div style={{ position: 'relative' }}>
                      <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
                      <input
                        type="text"
                        placeholder="Search employee by name or code..."
                        value={searchEmployeeQuery}
                        onChange={(e) => handleSearchEmployee(e.target.value)}
                        style={{ width: '100%', padding: '10px 14px 10px 38px', borderRadius: '10px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                      />
                    </div>

                    {employeeSearchResults.length > 0 && (
                      <div style={{ marginTop: '6px', maxHeight: '160px', overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: '10px', background: 'white', boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }}>
                        {employeeSearchResults.map((emp) => (
                          <div
                            key={emp.user_id}
                            onClick={() => {
                              setSelectedNewUser(emp);
                              setSearchEmployeeQuery(emp.full_name);
                              setEmployeeSearchResults([]);
                            }}
                            style={{ padding: '10px 14px', cursor: 'pointer', borderBottom: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '13px' }}
                          >
                            <div>
                              <strong style={{ color: '#0f172a' }}>{emp.full_name}</strong>
                              <span style={{ fontSize: '11px', color: '#64748b', marginLeft: '8px' }}>({emp.employee_code} • {emp.department_name})</span>
                            </div>
                            {selectedNewUser?.user_id === emp.user_id && <CheckCircle2 size={16} color="#2563eb" />}
                          </div>
                        ))}
                      </div>
                    )}

                    {selectedNewUser && (
                      <div style={{ marginTop: '8px', padding: '10px 14px', background: '#eff6ff', borderRadius: '10px', border: '1px solid #bfdbfe', fontSize: '13px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div>
                          <span style={{ fontSize: '11px', color: '#1e40af', fontWeight: 700, textTransform: 'uppercase' }}>Selected Replacement:</span>
                          <div style={{ fontWeight: 700, color: '#1e3a8a' }}>{selectedNewUser.full_name} ({selectedNewUser.department_name})</div>
                        </div>
                        <CheckCircle2 size={18} color="#2563eb" />
                      </div>
                    )}
                  </div>

                  {/* Reassignment Reason */}
                  <div>
                    <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '6px' }}>
                      Reason for Reassignment / Replacement *
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Employee Resignation / Role Transfer"
                      value={reassignReason}
                      onChange={(e) => setReassignReason(e.target.value)}
                      style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                    />
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
                  <button
                    type="button"
                    onClick={() => setSelectedReassignNFA(null)}
                    style={{ padding: '10px 20px', background: '#f1f5f9', color: '#475569', border: 'none', borderRadius: '10px', fontWeight: 600, fontSize: '13px', cursor: 'pointer' }}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    disabled={!selectedNewUser || submittingReassignment}
                    onClick={handleExecuteReassignment}
                    style={{ padding: '10px 20px', background: selectedNewUser ? '#2563eb' : '#94a3b8', color: 'white', border: 'none', borderRadius: '10px', fontWeight: 700, fontSize: '13px', cursor: selectedNewUser ? 'pointer' : 'not-allowed' }}
                  >
                    {submittingReassignment ? 'Reassigning...' : 'Confirm Reassignment'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'NOTIFICATIONS' && (
        <div style={{ background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0', padding: '28px', boxShadow: '0 4px 12px rgba(0,0,0,0.03)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#0f172a', margin: 0 }}>
                Notification Control Matrix (Email vs In-App)
              </h3>
              <p style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                Independently toggle Email and In-App Bell notifications for each workflow step.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <div style={{ padding: '8px 14px', borderRadius: '12px', background: masterEmailFlag ? '#f0fdf4' : '#fef2f2', border: masterEmailFlag ? '1px solid #bbf7d0' : '1px solid #fecaca', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: masterEmailFlag ? '#10b981' : '#ef4444' }} />
                <span style={{ fontSize: '12px', fontWeight: 700, color: masterEmailFlag ? '#166534' : '#991b1b' }}>
                  Email System: {masterEmailFlag ? 'ON' : 'OFF'}
                </span>
              </div>

              <div style={{ padding: '8px 14px', borderRadius: '12px', background: masterInAppFlag ? '#eff6ff' : '#fef2f2', border: masterInAppFlag ? '1px solid #bfdbfe' : '1px solid #fecaca', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: masterInAppFlag ? '#2563eb' : '#ef4444' }} />
                <span style={{ fontSize: '12px', fontWeight: 700, color: masterInAppFlag ? '#1e40af' : '#991b1b' }}>
                  In-App System: {masterInAppFlag ? 'ON' : 'OFF'}
                </span>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {notificationTemplates.map((item) => (
              <div
                key={item.template_id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '16px 20px',
                  background: '#f8fafc',
                  borderRadius: '12px',
                  border: '1px solid #e2e8f0',
                }}
              >
                <div style={{ flex: 1, paddingRight: '20px' }}>
                  <div style={{ fontWeight: 700, fontSize: '14px', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>{item.event_type}</span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>{item.event_description}</div>
                </div>

                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  {/* Email Toggle Button */}
                  <button
                    type="button"
                    onClick={() => handleToggleTemplateFlag(item.event_type, 'email', item.is_email_active)}
                    style={{
                      padding: '8px 14px',
                      borderRadius: '20px',
                      border: 'none',
                      background: item.is_email_active ? '#10b981' : '#94a3b8',
                      color: 'white',
                      fontWeight: 700,
                      fontSize: '12px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      minWidth: '130px',
                      justifyContent: 'center',
                    }}
                  >
                    <Mail size={15} />
                    <span>Email: {item.is_email_active ? 'ON' : 'OFF'}</span>
                  </button>

                  {/* In-App Toggle Button */}
                  <button
                    type="button"
                    onClick={() => handleToggleTemplateFlag(item.event_type, 'inapp', item.is_inapp_active)}
                    style={{
                      padding: '8px 14px',
                      borderRadius: '20px',
                      border: 'none',
                      background: item.is_inapp_active ? '#2563eb' : '#94a3b8',
                      color: 'white',
                      fontWeight: 700,
                      fontSize: '12px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      minWidth: '130px',
                      justifyContent: 'center',
                    }}
                  >
                    <Bell size={15} />
                    <span>In-App: {item.is_inapp_active ? 'ON' : 'OFF'}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};