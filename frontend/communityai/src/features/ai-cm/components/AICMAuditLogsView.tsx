import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../../auth/hooks/useAuth'
import { getAICMAuditLogs } from '../services/aiCmApi'
import type { AICMAuditLog } from '../types'

export function AICMAuditLogsView() {
  const { accessToken } = useAuth()
  const [logs, setLogs] = useState<AICMAuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [actionFilter, setActionFilter] = useState<string>('ALL')

  const fetchLogs = useCallback(async () => {
    if (!accessToken) return
    setLoading(true)
    try {
      const data = await getAICMAuditLogs(
        accessToken,
        50,
        0,
        actionFilter === 'ALL' ? undefined : actionFilter,
      )
      setLogs(data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }, [accessToken, actionFilter])

  useEffect(() => {
    fetchLogs()
  }, [fetchLogs])

  const formatDateTime = (dateStr: string) => {
    try {
      const d = new Date(dateStr)
      return d.toLocaleString('fr-FR', {
        dateStyle: 'short',
        timeStyle: 'medium',
      })
    } catch {
      return dateStr
    }
  }

  const getActionBadge = (action: string) => {
    switch (action) {
      case 'AUTO_SEND':
        return <span className="audit-badge badge-success">🤖 Envoi automatique</span>
      case 'SEND_REPLY':
        return <span className="audit-badge badge-primary">📤 Envoi manuel</span>
      case 'APPROVE_DRAFT':
        return <span className="audit-badge badge-info">✅ Brouillon approuvé</span>
      case 'REJECT_DRAFT':
        return <span className="audit-badge badge-secondary">❌ Brouillon rejeté</span>
      case 'BLOCKED_AUTO_SEND':
        return <span className="audit-badge badge-warning">🛑 Envoi auto bloqué</span>
      case 'ESCALATE':
        return <span className="audit-badge badge-danger">🚨 Escalade humain</span>
      case 'ANALYZE':
        return <span className="audit-badge badge-neutral">🔍 Analyse sémantique</span>
      default:
        return <span className="audit-badge badge-neutral">{action}</span>
    }
  }

  return (
    <div className="aicm-audit-view">
      <div className="audit-header-row">
        <div>
          <h3>📜 Journal d'Audit & Historique d'Exécution</h3>
          <p className="text-muted">
            Traçabilité exhaustive et horodatée de toutes les décisions de l'IA et validations humaines.
          </p>
        </div>

        <div className="audit-filters">
          <select
            className="aicm-select"
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
          >
            <option value="ALL">Toutes les actions</option>
            <option value="AUTO_SEND">Envois automatiques</option>
            <option value="APPROVE_DRAFT">Brouillons approuvés</option>
            <option value="BLOCKED_AUTO_SEND">Envois auto bloqués</option>
            <option value="ESCALATE">Escalades</option>
            <option value="ANALYZE">Analyses</option>
          </select>
          <button type="button" className="btn btn-secondary btn-sm" onClick={fetchLogs}>
            🔄 Actualiser
          </button>
        </div>
      </div>

      {loading && logs.length === 0 ? (
        <div className="aicm-loading-container">
          <div className="aicm-spinner" />
          <p>Chargement du journal d'audit...</p>
        </div>
      ) : logs.length === 0 ? (
        <div className="aicm-empty-state">
          <p>Aucune action enregistrée dans l'historique d'audit.</p>
        </div>
      ) : (
        <div className="audit-table-wrapper">
          <table className="audit-table">
            <thead>
              <tr>
                <th>Date & Heure</th>
                <th>Action</th>
                <th>Message ID</th>
                <th>Détails & Justification</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td className="audit-time">{formatDateTime(log.created_at)}</td>
                  <td>{getActionBadge(log.action)}</td>
                  <td className="audit-msg-id">
                    {log.inbox_message_id ? `#${log.inbox_message_id}` : '—'}
                  </td>
                  <td className="audit-details">
                    <code>{JSON.stringify(log.details)}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
