import React, { useState, useEffect } from 'react';
import { ShieldCheck, Eye, UserCheck, Download, Paperclip, ChevronLeft, ChevronRight, Filter } from 'lucide-react';

interface NFARequest {
  nfa_request_id: string;
  nfa_number: string;
  title: string;
  department_name: string;
  project_name?: string;
  total_amount_usd: string;
  current_status: string;
  current_level: number;
  version_number: number;
  buyer_full_name: string;
  approved_at: string;
}

export const AuditorPortalView: React.FC = () => {
  const [requests, setRequests] = useState<NFARequest[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [selectedDept, setSelectedDept] = useState<string>('ALL');
  const [loading, setLoading] = useState<boolean>(true);
  
  // 10-Item Pagination State
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalCount, setTotalCount] = useState<number>(0);
  const pageSize = 10;

  const [selectedNFA, setSelectedNFA] = useState<any | null>(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/admin/departments')
      .then((res) => res.json())
      .then((data) => {
        if (data.isSuccess && data.departments) {
          setDepartments(data.departments);
        }
      });
  }, []);

  const fetchAuditorRequests = async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/auditor/nfas?department_id=${selectedDept}&page=${currentPage}&page_size=${pageSize}`);
      const data = await res.json();
      if (data.isSuccess && data.nfa_requests) {
        setRequests(data.nfa_requests);
        setTotalCount(data.total_count || 0);
        setTotalPages(data.total_pages || 1);
      }
    } catch (e) {
      console.error('Failed fetching auditor compliance list', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditorRequests();
  }, [selectedDept, currentPage]);

  const handleOpenDetail = async (nfaId: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/nfa/${nfaId}`);
      const data = await res.json();
      if (data.isSuccess && data.nfa) {
        setSelectedNFA(data.nfa);
      }
    } catch (e) {
      console.error('Failed loading NFA details', e);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Banner */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ShieldCheck size={28} color="#10b981" />
          <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#0f172a', margin: 0, fontFamily: 'Outfit, sans-serif' }}>
            Auditor Compliance Portal
          </h1>
        </div>
        <p style={{ fontSize: '13px', color: '#64748b', margin: '4px 0 0 0' }}>
          Read-Only Compliance Inspection & Audit Trail for Final Approved NFA Requests (₹ INR)
        </p>
      </div>

      {/* Department Filter Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', background: 'white', padding: '16px 20px', borderRadius: '14px', border: '1px solid #e2e8f0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Filter size={18} color="#64748b" />
          <span style={{ fontSize: '13px', fontWeight: 700, color: '#475569' }}>Filter by Department:</span>
          <select
            value={selectedDept}
            onChange={(e) => { setSelectedDept(e.target.value); setCurrentPage(1); }}
            style={{ padding: '8px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '13px', fontWeight: 600, color: '#0f172a' }}
          >
            <option value="ALL">All Departments</option>
            {departments.map((d) => (
              <option key={d.department_id} value={d.department_id}>
                {d.department_name}
              </option>
            ))}
          </select>
        </div>

        <div style={{ fontSize: '13px', color: '#64748b', fontWeight: 600 }}>
          Total Approved Records: <strong style={{ color: '#10b981' }}>{totalCount}</strong>
        </div>
      </div>

      {/* Data Table */}
      <div style={{ background: 'white', borderRadius: '16px', border: '1px solid #e2e8f0', boxShadow: '0 4px 12px rgba(0,0,0,0.03)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569', fontWeight: 700 }}>
              <th style={{ padding: '14px 18px' }}>NFA REFERENCE</th>
              <th style={{ padding: '14px 18px' }}>TITLE & PROJECT</th>
              <th style={{ padding: '14px 18px' }}>DEPARTMENT</th>
              <th style={{ padding: '14px 18px' }}>TOTAL AMOUNT (₹ INR)</th>
              <th style={{ padding: '14px 18px' }}>STATUS</th>
              <th style={{ padding: '14px 18px' }}>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: '#64748b' }}>
                  Loading Auditor Records...
                </td>
              </tr>
            ) : requests.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
                  No final approved NFAs found for department filter.
                </td>
              </tr>
            ) : (
              requests.map((item) => (
                <tr key={item.nfa_request_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '14px 18px' }}>
                    <div style={{ fontWeight: 700, color: '#2563eb' }}>{item.nfa_number}</div>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>Initiated by {item.buyer_full_name}</div>
                  </td>
                  <td style={{ padding: '14px 18px' }}>
                    <div style={{ fontWeight: 700, color: '#0f172a' }}>{item.title}</div>
                    <div style={{ fontSize: '12px', color: '#64748b' }}>{item.project_name || 'General Project'}</div>
                  </td>
                  <td style={{ padding: '14px 18px', color: '#334155', fontWeight: 500 }}>
                    {item.department_name}
                  </td>
                  <td style={{ padding: '14px 18px', fontWeight: 700, color: '#166534' }}>
                    ₹{parseFloat(item.total_amount_usd || '0').toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td style={{ padding: '14px 18px' }}>
                    <span className="status-badge status-approved">Approved</span>
                  </td>
                  <td style={{ padding: '14px 18px' }}>
                    <button
                      onClick={() => handleOpenDetail(item.nfa_request_id)}
                      style={{
                        padding: '6px 14px',
                        background: '#f1f5f9',
                        border: '1px solid #cbd5e1',
                        borderRadius: '8px',
                        fontWeight: 600,
                        fontSize: '12px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        color: '#334155',
                      }}
                    >
                      <Eye size={14} /> Audit Details
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* 10-Item Container Pagination Controls */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', background: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
          <div style={{ fontSize: '12px', color: '#64748b' }}>
            Showing Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong> ({totalCount} total items)
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              style={{
                padding: '6px 12px',
                borderRadius: '8px',
                border: '1px solid #cbd5e1',
                background: currentPage === 1 ? '#f1f5f9' : 'white',
                color: currentPage === 1 ? '#94a3b8' : '#334155',
                cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                fontSize: '12px',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <ChevronLeft size={14} /> Previous
            </button>

            <span style={{ fontSize: '12px', fontWeight: 700, padding: '0 8px' }}>
              {currentPage} / {totalPages}
            </span>

            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages || totalPages === 0}
              style={{
                padding: '6px 12px',
                borderRadius: '8px',
                border: '1px solid #cbd5e1',
                background: currentPage === totalPages || totalPages === 0 ? '#f1f5f9' : 'white',
                color: currentPage === totalPages || totalPages === 0 ? '#94a3b8' : '#334155',
                cursor: currentPage === totalPages || totalPages === 0 ? 'not-allowed' : 'pointer',
                fontSize: '12px',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              Next <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Compliance Detail Drawer Modal */}
      {selectedNFA && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15,23,42,0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}>
          <div style={{ background: 'white', width: '100%', maxWidth: '720px', borderRadius: '20px', padding: '28px', maxHeight: '85vh', overflowY: 'auto', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
              <div>
                <span style={{ fontSize: '12px', background: '#ecfdf5', color: '#047857', padding: '2px 8px', borderRadius: '12px', fontWeight: 700 }}>
                  READ-ONLY AUDIT • {selectedNFA.nfa_number}
                </span>
                <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#0f172a', marginTop: '6px', margin: 0 }}>
                  {selectedNFA.title}
                </h2>
              </div>
              <button onClick={() => setSelectedNFA(null)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: '18px' }}>
                ✕
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px', padding: '16px', background: '#f8fafc', borderRadius: '12px' }}>
              <div>
                <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700 }}>DEPARTMENT</div>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a' }}>{selectedNFA.department_name}</div>
              </div>

              <div>
                <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700 }}>AMOUNT (₹ INR)</div>
                <div style={{ fontSize: '16px', fontWeight: 800, color: '#166534' }}>
                  ₹{parseFloat(selectedNFA.total_amount_usd || '0').toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700 }}>VENDOR</div>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#334155' }}>{selectedNFA.vendor_name || 'N/A'}</div>
              </div>

              <div>
                <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700 }}>BUYER INITIATOR</div>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#334155' }}>{selectedNFA.buyer_full_name}</div>
              </div>
            </div>

            {/* Assigned Approver Chain & Reassignment Badges */}
            {selectedNFA.approver_chain && selectedNFA.approver_chain.length > 0 && (
              <div style={{ marginBottom: '20px', padding: '16px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <UserCheck size={14} color="#2563eb" />
                  <span>ASSIGNED APPROVAL CHAIN ({selectedNFA.approver_chain.length} STEPS)</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {selectedNFA.approver_chain.map((step: any, idx: number) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'white', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ padding: '2px 8px', borderRadius: '6px', background: '#eff6ff', color: '#2563eb', fontWeight: 700, fontSize: '11px' }}>
                          Level {step.level}
                        </span>
                        <span style={{ fontWeight: 700, color: '#0f172a' }}>{step.full_name || step.username}</span>
                        <span style={{ color: '#64748b' }}>({step.department_name || 'General'})</span>
                      </div>

                      {step.is_reassigned && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }} title={`Replaced ${step.old_approver_name || 'previous approver'}. Reason: ${step.reassignment_reason || 'Admin Reassignment'}`}>
                          <span style={{ padding: '2px 8px', borderRadius: '10px', background: '#fef3c7', color: '#b45309', fontWeight: 700, fontSize: '11px', border: '1px solid #fde68a' }}>
                            🔄 Reassigned by Admin
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Version-Grouped Attached Documents & Files (Option A) */}
            {selectedNFA.attachments && selectedNFA.attachments.length > 0 && (
              <div style={{ marginBottom: '20px', padding: '16px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Paperclip size={14} color="#2563eb" />
                  <span>ATTACHED DOCUMENTS & REVISION FILES ({selectedNFA.attachments.length})</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {selectedNFA.attachments.map((att: any, idx: number) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', background: 'white', borderRadius: '10px', border: '1px solid #cbd5e1' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0, flex: 1, marginRight: '16px' }}>
                        <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, flexShrink: 0 }}>
                          <Paperclip size={18} />
                        </div>
                        <div style={{ minWidth: 0, flex: 1 }}>
                          <div style={{ fontWeight: 700, fontSize: '13px', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '340px' }} title={att.file_name}>{att.file_name}</span>
                            <span style={{ flexShrink: 0, fontSize: '10px', padding: '2px 8px', borderRadius: '10px', background: '#e0f2fe', color: '#0369a1', fontWeight: 700 }}>
                              v{att.version_number || 1}
                            </span>
                          </div>
                          <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                            {Math.round((att.file_size || 0) / 1024)} KB
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <button
                          type="button"
                          onClick={() => window.open(att.file_url || `http://127.0.0.1:8000/${att.file_path}`, '_blank')}
                          style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '6px 12px', background: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}
                        >
                          <Eye size={14} /> Preview
                        </button>
                        <a
                          href={att.file_url || `http://127.0.0.1:8000/${att.file_path}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          download={att.file_name}
                          style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '6px 12px', background: '#2563eb', color: 'white', border: 'none', borderRadius: '8px', fontSize: '12px', fontWeight: 600, cursor: 'pointer', textDecoration: 'none' }}
                        >
                          <Download size={14} /> Download
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Audit Trail Logs */}
            {selectedNFA.audit_history && selectedNFA.audit_history.filter((h: any) => !h.action_type?.toUpperCase().includes('DRAFT')).length > 0 && (
              <div style={{ marginBottom: '20px', padding: '16px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '10px' }}>
                  AUDIT TRAIL LOGS & DECISIONS
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {selectedNFA.audit_history.filter((h: any) => !h.action_type?.toUpperCase().includes('DRAFT')).map((h: any) => ({ ...h, comments: h.action_type?.toUpperCase() === 'SUBMITTED' ? 'Submitted' : h.comments })).map((h: any, idx: number) => (
                    <div key={idx} style={{ fontSize: '12px', color: '#334155', padding: '8px', background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                      <strong style={{ color: '#0f172a' }}>{h.action_by_name || h.action_by}:</strong> {h.action_type} — <em>"{h.comments}"</em>
                      <span style={{ fontSize: '10px', color: '#94a3b8', marginLeft: '8px' }}>{new Date(h.action_at).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
