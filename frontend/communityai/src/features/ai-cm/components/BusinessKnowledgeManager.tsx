import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../../auth/hooks/useAuth'
import {
  createKnowledgeFAQ,
  createKnowledgeProduct,
  deleteKnowledgeFAQ,
  deleteKnowledgeProduct,
  getBusinessKnowledge,
  listKnowledgeFAQs,
  listKnowledgeProducts,
  seedDefaultKnowledge,
  updateBusinessKnowledge,
  updateKnowledgeFAQ,
  updateKnowledgeProduct,
} from '../services/aiCmApi'
import type { BusinessKnowledge, KnowledgeFAQ, KnowledgeProduct } from '../types'

type SubTab = 'identity' | 'products' | 'customer_service' | 'editorial'

export function BusinessKnowledgeManager() {
  const { accessToken } = useAuth()
  const [activeTab, setActiveTab] = useState<SubTab>('identity')
  const [knowledge, setKnowledge] = useState<BusinessKnowledge | null>(null)
  const [products, setProducts] = useState<KnowledgeProduct[]>([])
  const [faqs, setFaqs] = useState<KnowledgeFAQ[]>([])

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  // Modals state
  const [showProductModal, setShowProductModal] = useState(false)
  const [editingProduct, setEditingProduct] = useState<KnowledgeProduct | null>(null)
  const [productForm, setProductForm] = useState({
    name: '',
    description: '',
    price: '',
    availability: 'in_stock',
    features: '',
    promotions: '',
    delivery_terms: '',
  })

  const [showFaqModal, setShowFaqModal] = useState(false)
  const [editingFaq, setEditingFaq] = useState<KnowledgeFAQ | null>(null)
  const [faqForm, setFaqForm] = useState({
    category: 'Général',
    question: '',
    answer: '',
    keywords: '',
  })

  const loadAll = useCallback(async () => {
    if (!accessToken) return
    setLoading(true)
    try {
      const [kData, pData, fData] = await Promise.all([
        getBusinessKnowledge(accessToken),
        listKnowledgeProducts(accessToken),
        listKnowledgeFAQs(accessToken),
      ])
      setKnowledge(kData)
      setProducts(pData)
      setFaqs(fData)
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Erreur lors du chargement des données.' })
    } finally {
      setLoading(false)
    }
  }, [accessToken])

  useEffect(() => {
    loadAll()
  }, [loadAll])

  const showToast = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message })
    setTimeout(() => setNotification(null), 4000)
  }

  // Handle Knowledge Base Form Save
  const handleSaveKnowledge = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!accessToken || !knowledge) return
    setSaving(true)
    try {
      const updated = await updateBusinessKnowledge(accessToken, knowledge)
      setKnowledge(updated)
      showToast('success', 'Base de connaissances mise à jour avec succès !')
    } catch (err: any) {
      showToast('error', err.message || 'Erreur lors de la sauvegarde.')
    } finally {
      setSaving(false)
    }
  }

  // Handle Seed Default
  const handleSeed = async () => {
    if (!accessToken) return
    setSaving(true)
    try {
      await seedDefaultKnowledge(accessToken)
      await loadAll()
      showToast('success', 'Données de démonstration chargées avec succès !')
    } catch (err: any) {
      showToast('error', err.message || 'Erreur lors du pré-remplissage.')
    } finally {
      setSaving(false)
    }
  }

  // Product actions
  const openNewProductModal = () => {
    setEditingProduct(null)
    setProductForm({
      name: '',
      description: '',
      price: '',
      availability: 'in_stock',
      features: '',
      promotions: '',
      delivery_terms: '',
    })
    setShowProductModal(true)
  }

  const openEditProductModal = (prod: KnowledgeProduct) => {
    setEditingProduct(prod)
    setProductForm({
      name: prod.name,
      description: prod.description,
      price: prod.price,
      availability: prod.availability,
      features: (prod.features || []).join('\n'),
      promotions: prod.promotions || '',
      delivery_terms: prod.delivery_terms || '',
    })
    setShowProductModal(true)
  }

  const handleSaveProduct = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!accessToken) return
    try {
      const featuresList = productForm.features
        .split('\n')
        .map((f) => f.trim())
        .filter(Boolean)

      if (editingProduct) {
        await updateKnowledgeProduct(accessToken, editingProduct.id, {
          name: productForm.name,
          description: productForm.description,
          price: productForm.price,
          availability: productForm.availability,
          features: featuresList,
          promotions: productForm.promotions || null,
          delivery_terms: productForm.delivery_terms || null,
        })
        showToast('success', 'Produit modifié avec succès.')
      } else {
        await createKnowledgeProduct(accessToken, {
          name: productForm.name,
          description: productForm.description,
          price: productForm.price,
          availability: productForm.availability,
          features: featuresList,
          promotions: productForm.promotions || null,
          delivery_terms: productForm.delivery_terms || null,
        })
        showToast('success', 'Produit ajouté avec succès.')
      }
      setShowProductModal(false)
      const pList = await listKnowledgeProducts(accessToken)
      setProducts(pList)
    } catch (err: any) {
      showToast('error', err.message || 'Erreur lors de la sauvegarde du produit.')
    }
  }

  const handleDeleteProduct = async (id: number) => {
    if (!accessToken || !window.confirm('Voulez-vous vraiment supprimer ce produit ?')) return
    try {
      await deleteKnowledgeProduct(accessToken, id)
      setProducts(products.filter((p) => p.id !== id))
      showToast('success', 'Produit supprimé.')
    } catch (err: any) {
      showToast('error', err.message || 'Erreur de suppression.')
    }
  }

  // FAQ actions
  const openNewFaqModal = () => {
    setEditingFaq(null)
    setFaqForm({ category: 'Général', question: '', answer: '', keywords: '' })
    setShowFaqModal(true)
  }

  const openEditFaqModal = (faq: KnowledgeFAQ) => {
    setEditingFaq(faq)
    setFaqForm({
      category: faq.category,
      question: faq.question,
      answer: faq.answer,
      keywords: (faq.keywords || []).join(', '),
    })
    setShowFaqModal(true)
  }

  const handleSaveFaq = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!accessToken) return
    try {
      const keywordsList = faqForm.keywords
        .split(',')
        .map((k) => k.trim())
        .filter(Boolean)

      if (editingFaq) {
        await updateKnowledgeFAQ(accessToken, editingFaq.id, {
          category: faqForm.category,
          question: faqForm.question,
          answer: faqForm.answer,
          keywords: keywordsList,
        })
        showToast('success', 'FAQ mise à jour.')
      } else {
        await createKnowledgeFAQ(accessToken, {
          category: faqForm.category,
          question: faqForm.question,
          answer: faqForm.answer,
          keywords: keywordsList,
          is_active: true,
        })
        showToast('success', 'FAQ créée avec succès.')
      }
      setShowFaqModal(false)
      const fList = await listKnowledgeFAQs(accessToken)
      setFaqs(fList)
    } catch (err: any) {
      showToast('error', err.message || 'Erreur lors de la sauvegarde de la FAQ.')
    }
  }

  const handleDeleteFaq = async (id: number) => {
    if (!accessToken || !window.confirm('Supprimer cette question/réponse ?')) return
    try {
      await deleteKnowledgeFAQ(accessToken, id)
      setFaqs(faqs.filter((f) => f.id !== id))
      showToast('success', 'FAQ supprimée.')
    } catch (err: any) {
      showToast('error', err.message || 'Erreur de suppression.')
    }
  }

  if (loading && !knowledge) {
    return (
      <div className="aicm-loading-container">
        <div className="aicm-spinner" />
        <p>Chargement de la base de connaissances...</p>
      </div>
    )
  }

  if (!knowledge) return null

  return (
    <div className="bk-manager-container">
      {/* Toast Notification */}
      {notification && (
        <div className={`aicm-alert alert-${notification.type}`}>
          {notification.type === 'success' ? '✅' : '⚠️'} {notification.message}
        </div>
      )}

      {/* Top Banner and Quick Seed Action */}
      <div className="bk-header-row">
        <div>
          <h2>🧠 Base de Connaissances Entreprise</h2>
          <p className="bk-subtitle">
            Toutes les informations vérifiées utilisées par l'IA pour répondre avec précision à vos clients sans jamais inventer.
          </p>
        </div>
        <button type="button" className="btn btn-outline" onClick={handleSeed} disabled={saving}>
          🧪 Données types recommandées
        </button>
      </div>

      {/* Sub Tabs Navigation */}
      <div className="bk-tabs-nav">
        <button
          type="button"
          className={`bk-tab-btn ${activeTab === 'identity' ? 'active' : ''}`}
          onClick={() => setActiveTab('identity')}
        >
          🏢 Identité de l'entreprise
        </button>
        <button
          type="button"
          className={`bk-tab-btn ${activeTab === 'products' ? 'active' : ''}`}
          onClick={() => setActiveTab('products')}
        >
          📦 Produits & Services ({products.length})
        </button>
        <button
          type="button"
          className={`bk-tab-btn ${activeTab === 'customer_service' ? 'active' : ''}`}
          onClick={() => setActiveTab('customer_service')}
        >
          🛡️ Service Client & Politiques ({faqs.length} FAQ)
        </button>
        <button
          type="button"
          className={`bk-tab-btn ${activeTab === 'editorial' ? 'active' : ''}`}
          onClick={() => setActiveTab('editorial')}
        >
          ✍️ Identité Éditoriale & Ton
        </button>
      </div>

      {/* TAB 1: IDENTITÉ DE L'ENTREPRISE */}
      {activeTab === 'identity' && (
        <form onSubmit={handleSaveKnowledge} className="bk-form-section">
          <div className="bk-grid-two">
            <div className="form-group">
              <label>Nom de l'entreprise *</label>
              <input
                type="text"
                className="form-control"
                value={knowledge.company_name}
                onChange={(e) => setKnowledge({ ...knowledge, company_name: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Secteur d'activité</label>
              <input
                type="text"
                className="form-control"
                value={knowledge.industry}
                onChange={(e) => setKnowledge({ ...knowledge, industry: e.target.value })}
                placeholder="Ex: E-commerce, SaaS, Agence marketing..."
              />
            </div>
          </div>

          <div className="form-group">
            <label>Description de l'activité</label>
            <textarea
              className="form-control"
              rows={3}
              value={knowledge.description}
              onChange={(e) => setKnowledge({ ...knowledge, description: e.target.value })}
              placeholder="Présentation claire et synthétique de votre mission et de vos offres..."
            />
          </div>

          <div className="bk-grid-three">
            <div className="form-group">
              <label>Site web</label>
              <input
                type="url"
                className="form-control"
                value={knowledge.website || ''}
                onChange={(e) => setKnowledge({ ...knowledge, website: e.target.value })}
                placeholder="https://..."
              />
            </div>
            <div className="form-group">
              <label>Email de contact public</label>
              <input
                type="email"
                className="form-control"
                value={knowledge.contact_email || ''}
                onChange={(e) => setKnowledge({ ...knowledge, contact_email: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Téléphone d'assistance</label>
              <input
                type="text"
                className="form-control"
                value={knowledge.contact_phone || ''}
                onChange={(e) => setKnowledge({ ...knowledge, contact_phone: e.target.value })}
              />
            </div>
          </div>

          <div className="bk-grid-two">
            <div className="form-group">
              <label>Adresse postale</label>
              <input
                type="text"
                className="form-control"
                value={knowledge.address || ''}
                onChange={(e) => setKnowledge({ ...knowledge, address: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Horaires d'ouverture / fonctionnement</label>
              <input
                type="text"
                className="form-control"
                value={knowledge.operating_hours || ''}
                onChange={(e) => setKnowledge({ ...knowledge, operating_hours: e.target.value })}
                placeholder="Ex: Lundi au Vendredi de 9h à 18h CET"
              />
            </div>
          </div>

          <div className="bk-form-footer">
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Enregistrement...' : '💾 Sauvegarder l’Identité'}
            </button>
          </div>
        </form>
      )}

      {/* TAB 2: PRODUITS ET SERVICES */}
      {activeTab === 'products' && (
        <div className="bk-products-section">
          <div className="bk-section-actions">
            <p className="text-muted">
              L'IA cite uniquement les prix, caractéristiques et disponibilités enregistrés ci-dessous.
            </p>
            <button type="button" className="btn btn-primary btn-sm" onClick={openNewProductModal}>
              ➕ Ajouter un Produit / Service
            </button>
          </div>

          {products.length === 0 ? (
            <div className="bk-empty-state">
              <p>Aucun produit enregistré. Ajoutez vos offres pour permettre à l'IA de répondre aux demandes de tarifs.</p>
              <button type="button" className="btn btn-secondary" onClick={openNewProductModal}>
                Créer un produit
              </button>
            </div>
          ) : (
            <div className="bk-cards-grid">
              {products.map((p) => (
                <div key={p.id} className="bk-product-card">
                  <div className="product-card-top">
                    <h4>{p.name}</h4>
                    <span className="product-price-badge">{p.price || 'Sur devis'}</span>
                  </div>
                  <p className="product-desc">{p.description}</p>
                  <div className="product-meta">
                    <span className={`status-pill ${p.availability}`}>
                      {p.availability === 'in_stock'
                        ? 'En stock'
                        : p.availability === 'out_of_stock'
                        ? 'Rupture'
                        : p.availability === 'preorder'
                        ? 'Précommande'
                        : 'Sur demande'}
                    </span>
                    {p.promotions && <span className="promo-tag">🔥 {p.promotions}</span>}
                  </div>
                  {p.features && p.features.length > 0 && (
                    <ul className="product-features-list">
                      {p.features.map((f, i) => (
                        <li key={i}>• {f}</li>
                      ))}
                    </ul>
                  )}
                  <div className="card-actions-bar">
                    <button type="button" className="btn-link" onClick={() => openEditProductModal(p)}>
                      ✏️ Modifier
                    </button>
                    <button type="button" className="btn-link text-danger" onClick={() => handleDeleteProduct(p.id)}>
                      🗑️ Supprimer
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: SERVICE CLIENT & FAQS */}
      {activeTab === 'customer_service' && (
        <div className="bk-customer-service-section">
          <form onSubmit={handleSaveKnowledge} className="bk-form-section">
            <h3>🛡️ Politiques Officielles</h3>
            <div className="bk-grid-two">
              <div className="form-group">
                <label>Politique de remboursement</label>
                <textarea
                  className="form-control"
                  rows={2}
                  value={knowledge.refund_policy || ''}
                  onChange={(e) => setKnowledge({ ...knowledge, refund_policy: e.target.value })}
                  placeholder="Ex: Remboursement sous 14 jours si le produit n'a pas été ouvert..."
                />
              </div>
              <div className="form-group">
                <label>Politique de retour</label>
                <textarea
                  className="form-control"
                  rows={2}
                  value={knowledge.return_policy || ''}
                  onChange={(e) => setKnowledge({ ...knowledge, return_policy: e.target.value })}
                  placeholder="Ex: Retours gratuits via étiquette prépayée..."
                />
              </div>
            </div>

            <div className="bk-grid-two">
              <div className="form-group">
                <label>Garanties</label>
                <textarea
                  className="form-control"
                  rows={2}
                  value={knowledge.warranty_policy || ''}
                  onChange={(e) => setKnowledge({ ...knowledge, warranty_policy: e.target.value })}
                  placeholder="Ex: Garantie de 2 ans constructeur pièces et main d'œuvre..."
                />
              </div>
              <div className="form-group">
                <label>Conditions de livraison</label>
                <textarea
                  className="form-control"
                  rows={2}
                  value={knowledge.shipping_policy || ''}
                  onChange={(e) => setKnowledge({ ...knowledge, shipping_policy: e.target.value })}
                  placeholder="Ex: 48h-72h en France métropolitaine, offert dès 50€ d'achat..."
                />
              </div>
            </div>

            <div className="bk-grid-two">
              <div className="form-group">
                <label>Procédure de réclamation</label>
                <textarea
                  className="form-control"
                  rows={2}
                  value={knowledge.complaint_procedure || ''}
                  onChange={(e) => setKnowledge({ ...knowledge, complaint_procedure: e.target.value })}
                  placeholder="Ex: Contact support@... avec numéro de commande sous 48h..."
                />
              </div>
              <div className="form-group">
                <label>Coordonnées du support client</label>
                <textarea
                  className="form-control"
                  rows={2}
                  value={knowledge.support_contact || ''}
                  onChange={(e) => setKnowledge({ ...knowledge, support_contact: e.target.value })}
                  placeholder="Ex: support@... ou chat en direct sur le site..."
                />
              </div>
            </div>

            <div className="bk-form-footer">
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? 'Enregistrement...' : '💾 Sauvegarder les Politiques'}
              </button>
            </div>
          </form>

          {/* FAQs List & Actions */}
          <div className="bk-faqs-container">
            <div className="bk-section-actions">
              <h3>❓ Questions Fréquentes (FAQ)</h3>
              <button type="button" className="btn btn-primary btn-sm" onClick={openNewFaqModal}>
                ➕ Ajouter une FAQ
              </button>
            </div>

            {faqs.length === 0 ? (
              <p className="text-muted">Aucune FAQ enregistrée.</p>
            ) : (
              <div className="bk-faq-list">
                {faqs.map((f) => (
                  <div key={f.id} className="bk-faq-item">
                    <div className="faq-top-row">
                      <span className="faq-cat-badge">{f.category}</span>
                      <div className="faq-actions">
                        <button type="button" className="btn-link" onClick={() => openEditFaqModal(f)}>
                          ✏️ Modifier
                        </button>
                        <button type="button" className="btn-link text-danger" onClick={() => handleDeleteFaq(f.id)}>
                          🗑️
                        </button>
                      </div>
                    </div>
                    <div className="faq-question">Q : {f.question}</div>
                    <div className="faq-answer">R : {f.answer}</div>
                    {f.keywords && f.keywords.length > 0 && (
                      <div className="faq-keywords">Mots-clés : {f.keywords.join(', ')}</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: IDENTITÉ ÉDITORIALE & TON */}
      {activeTab === 'editorial' && (
        <form onSubmit={handleSaveKnowledge} className="bk-form-section">
          <div className="form-group">
            <label>Ton de communication de la marque *</label>
            <input
              type="text"
              className="form-control"
              value={knowledge.brand_tone}
              onChange={(e) => setKnowledge({ ...knowledge, brand_tone: e.target.value })}
              placeholder="Ex: professionnel, bienveillant, enthousiaste et réactif"
              required
            />
          </div>

          <div className="form-group">
            <label>Style de rédaction & directives</label>
            <textarea
              className="form-control"
              rows={3}
              value={knowledge.writing_style || ''}
              onChange={(e) => setKnowledge({ ...knowledge, writing_style: e.target.value })}
              placeholder="Ex: Privilégier le vouvoiement, faire des phrases courtes, être positif et proposer une action concrète."
            />
          </div>

          <div className="bk-grid-two">
            <div className="form-group">
              <label>Expressions recommandées (séparées par une virgule)</label>
              <textarea
                className="form-control"
                rows={3}
                value={(knowledge.preferred_expressions || []).join(', ')}
                onChange={(e) =>
                  setKnowledge({
                    ...knowledge,
                    preferred_expressions: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                  })
                }
                placeholder="Ravi de vous aider, Merci pour votre confiance, À très vite..."
              />
            </div>

            <div className="form-group">
              <label>Expressions strictement INTERDITES (séparées par une virgule)</label>
              <textarea
                className="form-control"
                rows={3}
                value={(knowledge.forbidden_expressions || []).join(', ')}
                onChange={(e) =>
                  setKnowledge({
                    ...knowledge,
                    forbidden_expressions: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                  })
                }
                placeholder="Débrouillez-vous, C'est pas notre faute, Impossible..."
              />
            </div>
          </div>

          <div className="form-group">
            <label>Emojis autorisés (séparés par un espace)</label>
            <input
              type="text"
              className="form-control"
              value={(knowledge.allowed_emojis || []).join(' ')}
              onChange={(e) =>
                setKnowledge({
                  ...knowledge,
                  allowed_emojis: e.target.value.split(' ').map((s) => s.trim()).filter(Boolean),
                })
              }
              placeholder="✨ 👋 ✅ 📦 💡"
            />
          </div>

          <div className="bk-form-footer">
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Enregistrement...' : '💾 Sauvegarder l’Identité Éditoriale'}
            </button>
          </div>
        </form>
      )}

      {/* Product Modal */}
      {showProductModal && (
        <div className="modal-backdrop">
          <div className="modal-dialog">
            <div className="modal-header">
              <h3>{editingProduct ? 'Modifier le produit' : 'Nouveau Produit / Service'}</h3>
              <button type="button" className="btn-close" onClick={() => setShowProductModal(false)}>
                ✕
              </button>
            </div>
            <form onSubmit={handleSaveProduct}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Nom du produit *</label>
                  <input
                    type="text"
                    className="form-control"
                    value={productForm.name}
                    onChange={(e) => setProductForm({ ...productForm, name: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Description</label>
                  <textarea
                    className="form-control"
                    rows={2}
                    value={productForm.description}
                    onChange={(e) => setProductForm({ ...productForm, description: e.target.value })}
                  />
                </div>
                <div className="bk-grid-two">
                  <div className="form-group">
                    <label>Prix</label>
                    <input
                      type="text"
                      className="form-control"
                      value={productForm.price}
                      onChange={(e) => setProductForm({ ...productForm, price: e.target.value })}
                      placeholder="Ex: 49€ TTC"
                    />
                  </div>
                  <div className="form-group">
                    <label>Disponibilité</label>
                    <select
                      className="form-control"
                      value={productForm.availability}
                      onChange={(e) => setProductForm({ ...productForm, availability: e.target.value })}
                    >
                      <option value="in_stock">En stock</option>
                      <option value="out_of_stock">Rupture</option>
                      <option value="preorder">Précommande</option>
                      <option value="on_demand">Sur demande</option>
                    </select>
                  </div>
                </div>
                <div className="form-group">
                  <label>Caractéristiques (1 par ligne)</label>
                  <textarea
                    className="form-control"
                    rows={2}
                    value={productForm.features}
                    onChange={(e) => setProductForm({ ...productForm, features: e.target.value })}
                    placeholder="Étanche 50m&#10;Garantie 2 ans&#10;Livraison 24h"
                  />
                </div>
                <div className="form-group">
                  <label>Promotions en cours (le cas échéant)</label>
                  <input
                    type="text"
                    className="form-control"
                    value={productForm.promotions}
                    onChange={(e) => setProductForm({ ...productForm, promotions: e.target.value })}
                    placeholder="Ex: -20% avec le code WELCOME"
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowProductModal(false)}>
                  Annuler
                </button>
                <button type="submit" className="btn btn-primary">
                  Enregistrer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* FAQ Modal */}
      {showFaqModal && (
        <div className="modal-backdrop">
          <div className="modal-dialog">
            <div className="modal-header">
              <h3>{editingFaq ? 'Modifier la FAQ' : 'Nouvelle FAQ'}</h3>
              <button type="button" className="btn-close" onClick={() => setShowFaqModal(false)}>
                ✕
              </button>
            </div>
            <form onSubmit={handleSaveFaq}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Catégorie</label>
                  <input
                    type="text"
                    className="form-control"
                    value={faqForm.category}
                    onChange={(e) => setFaqForm({ ...faqForm, category: e.target.value })}
                    placeholder="Ex: Livraison, Tarifs, Garantie, Compte..."
                  />
                </div>
                <div className="form-group">
                  <label>Question du client *</label>
                  <input
                    type="text"
                    className="form-control"
                    value={faqForm.question}
                    onChange={(e) => setFaqForm({ ...faqForm, question: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Réponse officielle vérifiée *</label>
                  <textarea
                    className="form-control"
                    rows={3}
                    value={faqForm.answer}
                    onChange={(e) => setFaqForm({ ...faqForm, answer: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Mots-clés associés (séparés par virgule)</label>
                  <input
                    type="text"
                    className="form-control"
                    value={faqForm.keywords}
                    onChange={(e) => setFaqForm({ ...faqForm, keywords: e.target.value })}
                    placeholder="délai, transport, colissimo, temps"
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowFaqModal(false)}>
                  Annuler
                </button>
                <button type="submit" className="btn btn-primary">
                  Enregistrer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
