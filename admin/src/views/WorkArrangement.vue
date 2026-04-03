<template>
  <div class="work-arrangement-page">
    <!-- Header -->
    <div class="header-actions">
      <button v-if="currentDocument" @click="backToList" class="btn-secondary">
        ← 返回列表
      </button>
      <div v-else style="flex: 1;"></div>
      <button @click="createNewDocument" class="btn-primary">新建文档</button>
    </div>

    <!-- Loading / Error State -->
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <!-- Document Cards Grid (Default View) -->
    <div v-else-if="!currentDocument" class="documents-grid">
      <div v-if="documents.length === 0" class="empty-state">
        <p>暂无工作安排文档，点击"新建文档"开始</p>
      </div>
      <div
        v-for="doc in documents"
        :key="doc.id"
        class="document-card"
        @click="selectDocument(doc.id)"
      >
        <div class="document-card-header">
          <h2 class="document-card-title">{{ doc.title }}</h2>
          <span class="document-card-date">{{ formatDate(doc.updated_at) }}</span>
        </div>
        <div class="document-card-meta">
          <span v-if="doc.updated_by">
            更新者: {{ doc.updated_by.nickname || doc.updated_by.phone }}
          </span>
          <span v-if="doc.action_items_count !== undefined">
            任务数: {{ doc.action_items_count }}
          </span>
        </div>
        <div class="document-card-preview markdown-body" v-html="getDocumentPreview(doc.content)"></div>
      </div>
    </div>

    <!-- Document Editor (Single Document View) -->
    <div v-else class="document-editor">
      <!-- Editor Status Notification -->
      <div v-if="showEditorNotification" class="editor-notification">
        <span class="editor-indicator">🟢</span>
        {{ currentEditor }} 正在编辑此文档
      </div>

      <!-- Title -->
      <div class="title-section">
        <input
          v-if="editMode"
          v-model="editForm.title"
          type="text"
          class="title-input"
          placeholder="文档标题"
        />
        <h1 v-else class="document-title">{{ currentDocument.title }}</h1>
        <div class="document-meta">
          <span v-if="currentDocument.created_by">
            创建者: {{ currentDocument.created_by.nickname || currentDocument.created_by.phone }}
          </span>
          <span v-if="currentDocument.updated_by">
            更新者: {{ currentDocument.updated_by.nickname || currentDocument.updated_by.phone }}
          </span>
          <span>更新时间: {{ formatDateTime(currentDocument.updated_at) }}</span>
        </div>
      </div>

      <!-- Edit/Save Controls -->
      <div class="editor-controls">
        <button v-if="!editMode" @click="startEdit" class="btn-primary">编辑文档</button>
        <template v-else>
          <button @click="saveDocument" :disabled="saving" class="btn-primary">
            {{ saving ? '保存中...' : '保存' }}
          </button>
          <button @click="cancelEdit" class="btn-secondary">取消</button>
        </template>
        <button @click="deleteDocument" class="btn-danger">删除文档</button>
      </div>

      <!-- Content Editor/Viewer -->
      <div class="content-section">
        <div v-if="editMode" class="editor-container">
          <div class="editor-tabs">
            <button
              @click="editorTab = 'edit'"
              :class="['editor-tab', { active: editorTab === 'edit' }]"
            >
              编辑
            </button>
            <button
              @click="editorTab = 'preview'"
              :class="['editor-tab', { active: editorTab === 'preview' }]"
            >
              预览
            </button>
          </div>
          
          <textarea
            v-show="editorTab === 'edit'"
            v-model="editForm.content"
            class="content-textarea"
            placeholder="使用 Markdown 格式编写内容...

示例格式:
# 进度回顾
- 完成了 XXX 功能
- 解决了 YYY 问题

# 做得好的地方
- 团队协作顺畅

# 需要改进
- 文档更新不及时

# 问题
## 产品
- 需要优化用户体验

## 市场
- 推广渠道需要拓展

## 销售
- 转化率有待提升

# 任务分工
在下方「任务分工」中添加具体任务"
          ></textarea>
          
          <div v-show="editorTab === 'preview'" class="content-preview markdown-body" v-html="previewHtml"></div>
        </div>
        <div v-else class="content-display markdown-body" v-html="renderedContent"></div>
      </div>

      <!-- Action Items Section -->
      <div class="action-items-section">
        <div class="section-header">
          <h2>任务分工</h2>
          <button @click="showActionItemModal = true" class="btn-primary btn-sm">添加任务</button>
        </div>

        <div v-if="loadingActionItems" class="loading-small">加载中...</div>
        <div v-else-if="actionItems.length === 0" class="empty-state-small">
          暂无任务，点击"添加任务"创建
        </div>
        <div v-else class="action-items-list">
          <div
            v-for="item in actionItems"
            :key="item.id"
            class="action-item-card"
            :class="`status-${item.status}`"
          >
            <div class="action-item-header">
              <h3 class="action-item-title">{{ item.title }}</h3>
              <span class="status-badge" :class="`status-${item.status}`">
                {{ statusLabel(item.status) }}
              </span>
            </div>
            <p v-if="item.description" class="action-item-description">{{ item.description }}</p>
            <div class="action-item-meta">
              <span v-if="item.assigned_to">
                负责人: {{ item.assigned_to.nickname || item.assigned_to.phone }}
              </span>
              <span v-if="item.due_date">截止: {{ formatDate(item.due_date) }}</span>
              <span v-if="item.completed_at">完成: {{ formatDate(item.completed_at) }}</span>
            </div>
            <div class="action-item-actions">
              <button @click="editActionItem(item)" class="btn-link">编辑</button>
              <button @click="deleteActionItem(item)" class="btn-link btn-danger">删除</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Action Item Modal -->
    <div v-if="showActionItemModal" class="modal-overlay" @click.self="closeActionItemModal">
      <div class="modal-box">
        <div class="modal-head">
          <h2>{{ editingActionItem ? '编辑任务' : '添加任务' }}</h2>
          <button type="button" class="close-x" @click="closeActionItemModal" aria-label="关闭">×</button>
        </div>
        <div class="modal-body">
          <label class="field-label">标题 *</label>
          <input
            v-model="actionItemForm.title"
            type="text"
            class="field-input"
            placeholder="任务标题"
            required
          />

          <label class="field-label">描述</label>
          <textarea
            v-model="actionItemForm.description"
            class="field-textarea"
            rows="3"
            placeholder="详细描述（可选）"
          ></textarea>

          <label class="field-label">负责人</label>
          <select v-model="actionItemForm.assigned_to_id" class="field-input">
            <option :value="null">未分配</option>
            <option v-for="user in allUsers" :key="user.id" :value="user.id">
              {{ user.nickname || user.phone }}
            </option>
          </select>

          <label class="field-label">状态</label>
          <select v-model="actionItemForm.status" class="field-input">
            <option value="pending">待处理</option>
            <option value="in_progress">进行中</option>
            <option value="completed">已完成</option>
            <option value="cancelled">已取消</option>
          </select>

          <label class="field-label">截止日期</label>
          <input
            v-model="actionItemForm.due_date"
            type="date"
            class="field-input"
          />

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeActionItemModal">取消</button>
            <button
              type="button"
              class="btn-primary"
              :disabled="!actionItemForm.title || savingActionItem"
              @click="saveActionItem"
            >
              {{ savingActionItem ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- New Document Modal -->
    <div v-if="showNewDocModal" class="modal-overlay" @click.self="closeNewDocModal">
      <div class="modal-box">
        <div class="modal-head">
          <h2>新建文档</h2>
          <button type="button" class="close-x" @click="closeNewDocModal" aria-label="关闭">×</button>
        </div>
        <div class="modal-body">
          <label class="field-label">文档标题 *</label>
          <input
            v-model="newDocForm.title"
            type="text"
            class="field-input"
            placeholder="例如: 2026年第一季度回顾与计划"
            required
          />

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeNewDocModal">取消</button>
            <button
              type="button"
              class="btn-primary"
              :disabled="!newDocForm.title || creatingDoc"
              @click="createDocument"
            >
              {{ creatingDoc ? '创建中...' : '创建' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import apiClient from '../api/client'
import { marked } from 'marked'
import { formatDateTimeEST_CN } from '../utils/date'
import { workDocumentSocket } from '../services/workDocumentSocket'

// Configure marked to handle line breaks properly
marked.setOptions({
  breaks: true,
  gfm: true,
  pedantic: false
})

export default {
  name: 'WorkArrangement',
  data() {
    return {
      documents: [],
      selectedDocumentId: null,
      currentDocument: null,
      viewMode: 'list', // 'list' or 'detail'
      loading: false,
      error: null,
      editMode: false,
      editForm: {
        title: '',
        content: ''
      },
      saving: false,
      editorTab: 'edit',
      actionItems: [],
      loadingActionItems: false,
      allUsers: [],
      showActionItemModal: false,
      editingActionItem: null,
      actionItemForm: {
        title: '',
        description: '',
        assigned_to_id: null,
        status: 'pending',
        due_date: null
      },
      savingActionItem: false,
      showNewDocModal: false,
      newDocForm: {
        title: ''
      },
      creatingDoc: false,
      autoSaveTimer: null,
      typingTimer: null,
      currentEditor: null,
      showEditorNotification: false
    }
  },
  computed: {
    previewHtml() {
      if (!this.editForm.content) return ''
      // Preserve multiple line breaks by converting them to HTML breaks
      const processedContent = this.editForm.content.replace(/\n{3,}/g, (match) => {
        // For 3+ newlines, add extra <br> tags (n-2 breaks for n newlines)
        const numBreaks = match.length - 2
        return '\n\n' + '<br>'.repeat(numBreaks) + '\n\n'
      })
      return marked(processedContent)
    },
    renderedContent() {
      if (!this.currentDocument?.content) return ''
      // Preserve multiple line breaks by converting them to HTML breaks
      const processedContent = this.currentDocument.content.replace(/\n{3,}/g, (match) => {
        // For 3+ newlines, add extra <br> tags (n-2 breaks for n newlines)
        const numBreaks = match.length - 2
        return '\n\n' + '<br>'.repeat(numBreaks) + '\n\n'
      })
      return marked(processedContent)
    }
  },
  watch: {
    'editForm.content'() {
      if (this.editMode) {
        this.scheduleAutoSave()
        this.notifyTyping()
      }
    },
    'editForm.title'() {
      if (this.editMode) {
        this.scheduleAutoSave()
      }
    }
  },
  mounted() {
    this.loadDocuments()
    this.loadUsers()
    this.initWebSocket()
  },
  beforeUnmount() {
    this.cleanupWebSocket()
    if (this.autoSaveTimer) {
      clearTimeout(this.autoSaveTimer)
    }
    if (this.typingTimer) {
      clearTimeout(this.typingTimer)
    }
  },
  methods: {
    formatDateTime(value) {
      return formatDateTimeEST_CN(value)
    },
    formatDate(value) {
      if (!value) return ''
      const date = new Date(value)
      return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
    },
    getDocumentPreview(content) {
      if (!content) return '<p class="preview-empty">暂无内容</p>'
      // Process line breaks
      const processedContent = content.replace(/\n{3,}/g, (match) => {
        const numBreaks = match.length - 2
        return '\n\n' + '<br>'.repeat(numBreaks) + '\n\n'
      })
      // Render full markdown (not truncated text)
      const html = marked(processedContent)
      return html
    },
    backToList() {
      // Leave WebSocket room
      if (this.currentDocument?.id) {
        if (this.editMode) {
          workDocumentSocket.stopEditing(this.currentDocument.id)
        }
        workDocumentSocket.leaveDocument(this.currentDocument.id)
      }
      
      this.currentDocument = null
      this.selectedDocumentId = null
      this.editMode = false
      this.actionItems = []
      this.viewMode = 'list'
      this.currentEditor = null
      this.showEditorNotification = false
    },
    async selectDocument(docId) {
      this.selectedDocumentId = docId
      this.viewMode = 'detail'
      await this.loadDocument()
      
      // Join WebSocket room for this document
      workDocumentSocket.joinDocument(docId)
    },
    statusLabel(status) {
      const labels = {
        pending: '待处理',
        in_progress: '进行中',
        completed: '已完成',
        cancelled: '已取消'
      }
      return labels[status] || status
    },
    async loadDocuments() {
      this.loading = true
      this.error = null
      try {
        const { data } = await apiClient.get('/admin/work-documents')
        this.documents = data.documents || []
        // Don't auto-select first document - show grid instead
      } catch (e) {
        this.error = (e.response?.data?.message) || e.message || '加载失败'
      } finally {
        this.loading = false
      }
    },
    async loadDocument() {
      if (!this.selectedDocumentId) {
        this.currentDocument = null
        this.actionItems = []
        return
      }

      this.loading = true
      this.error = null
      try {
        const { data } = await apiClient.get(`/admin/work-documents/${this.selectedDocumentId}`)
        this.currentDocument = data
        this.actionItems = data.action_items || []
      } catch (e) {
        this.error = (e.response?.data?.message) || e.message || '加载失败'
      } finally {
        this.loading = false
      }
    },
    async loadUsers() {
      try {
        const { data } = await apiClient.get('/admin/users?role=admin')
        this.allUsers = data.users || []
      } catch (e) {
        console.error('Failed to load users:', e)
      }
    },
    async createNewDocument() {
      this.showNewDocModal = true
    },
    closeNewDocModal() {
      this.showNewDocModal = false
      this.newDocForm = { title: '' }
    },
    async createDocument() {
      if (!this.newDocForm.title.trim()) {
        alert('请输入文档标题')
        return
      }

      this.creatingDoc = true
      try {
        const { data } = await apiClient.post('/admin/work-documents', {
          title: this.newDocForm.title,
          content: '# 进度回顾\n\n# 做得好的地方\n\n# 需要改进\n\n# 问题\n## 产品\n\n## 市场\n\n## 销售\n\n# 任务分工\n'
        })
        this.documents.unshift(data)
        this.closeNewDocModal()
        // Navigate to the new document
        await this.selectDocument(data.id)
        this.startEdit()
      } catch (e) {
        const msg = (e.response?.data?.message) || e.message || '创建失败'
        alert(msg)
      } finally {
        this.creatingDoc = false
      }
    },
    async startEdit() {
      // Check if someone else is editing
      if (this.currentEditor) {
        alert(`${this.currentEditor} 正在编辑此文档`)
        return
      }

      // Try to acquire edit lock
      try {
        await workDocumentSocket.startEditing(this.currentDocument.id)
        this.editMode = true
        this.editForm = {
          title: this.currentDocument.title,
          content: this.currentDocument.content
        }
        this.editorTab = 'edit'
      } catch (err) {
        alert(err.message || '无法开始编辑')
      }
    },
    cancelEdit() {
      if (this.autoSaveTimer) {
        clearTimeout(this.autoSaveTimer)
      }
      
      // Release edit lock
      if (this.currentDocument?.id) {
        workDocumentSocket.stopEditing(this.currentDocument.id)
      }
      
      this.editMode = false
      this.editForm = { title: '', content: '' }
    },
    async saveDocument() {
      if (!this.editForm.title.trim()) {
        alert('请输入文档标题')
        return
      }

      this.saving = true
      try {
        const { data } = await apiClient.put(`/admin/work-documents/${this.currentDocument.id}`, {
          title: this.editForm.title,
          content: this.editForm.content
        })
        this.currentDocument = data
        
        // Release edit lock
        workDocumentSocket.stopEditing(this.currentDocument.id)
        
        this.editMode = false
        await this.loadDocuments()
      } catch (e) {
        const msg = (e.response?.data?.message) || e.message || '保存失败'
        alert(msg)
      } finally {
        this.saving = false
      }
    },
    async deleteDocument() {
      if (!confirm('确定要删除这个文档吗？所有关联的任务也会被删除。')) return

      try {
        await apiClient.delete(`/admin/work-documents/${this.currentDocument.id}`)
        await this.loadDocuments()
        this.backToList()
      } catch (e) {
        const msg = (e.response?.data?.message) || e.message || '删除失败'
        alert(msg)
      }
    },
    editActionItem(item) {
      this.editingActionItem = item
      this.actionItemForm = {
        title: item.title,
        description: item.description || '',
        assigned_to_id: item.assigned_to_id,
        status: item.status,
        due_date: item.due_date ? item.due_date.substring(0, 10) : null
      }
      this.showActionItemModal = true
    },
    async saveActionItem() {
      if (!this.actionItemForm.title.trim()) {
        alert('请输入任务标题')
        return
      }

      this.savingActionItem = true
      try {
        const payload = {
          ...this.actionItemForm,
          due_date: this.actionItemForm.due_date ? new Date(this.actionItemForm.due_date).toISOString() : null
        }

        if (this.editingActionItem) {
          const { data } = await apiClient.put(`/admin/action-items/${this.editingActionItem.id}`, payload)
          const index = this.actionItems.findIndex(i => i.id === data.id)
          if (index !== -1) {
            this.actionItems[index] = data
          }
        } else {
          payload.document_id = this.currentDocument.id
          const { data } = await apiClient.post('/admin/action-items', payload)
          this.actionItems.push(data)
        }

        this.closeActionItemModal()
      } catch (e) {
        const msg = (e.response?.data?.message) || e.message || '保存失败'
        alert(msg)
      } finally {
        this.savingActionItem = false
      }
    },
    async deleteActionItem(item) {
      if (!confirm('确定要删除这个任务吗？')) return

      try {
        await apiClient.delete(`/admin/action-items/${item.id}`)
        this.actionItems = this.actionItems.filter(i => i.id !== item.id)
      } catch (e) {
        const msg = (e.response?.data?.message) || e.message || '删除失败'
        alert(msg)
      }
    },
    closeActionItemModal() {
      this.showActionItemModal = false
      this.editingActionItem = null
      this.actionItemForm = {
        title: '',
        description: '',
        assigned_to_id: null,
        status: 'pending',
        due_date: null
      }
    },
    initWebSocket() {
      const token = localStorage.getItem('admin_auth_token')
      if (!token) {
        console.warn('No auth token found for WebSocket')
        return
      }

      workDocumentSocket.connect(token)

      workDocumentSocket.on('documentChanged', (data) => {
        console.log('Received document_changed event:', data)
        
        // If we're viewing the document that changed, reload it
        if (this.currentDocument && this.currentDocument.id === data.document_id) {
          // Don't reload if we're currently editing (we're the one making changes)
          if (!this.editMode) {
            this.loadDocument()
            this.showNotification(`文档已被 ${data.updated_by} 更新`)
          }
        }
        
        // Update document list
        this.loadDocuments()
      })

      workDocumentSocket.on('editorStarted', (data) => {
        if (this.currentDocument && this.currentDocument.id === data.document_id) {
          this.currentEditor = data.user
          this.showEditorNotification = true
        }
      })

      workDocumentSocket.on('editorStopped', (data) => {
        if (this.currentDocument && this.currentDocument.id === data.document_id) {
          this.currentEditor = null
          this.showEditorNotification = false
          // Reload document to get latest changes
          if (!this.editMode) {
            this.loadDocument()
          }
        }
      })

      workDocumentSocket.on('editorStatus', (data) => {
        if (data.is_editing) {
          this.currentEditor = data.editor
          this.showEditorNotification = true
        }
      })

      workDocumentSocket.on('editorLeft', (data) => {
        if (this.currentDocument && this.currentDocument.id === data.document_id) {
          this.currentEditor = null
          this.showEditorNotification = false
        }
      })
    },
    cleanupWebSocket() {
      if (this.currentDocument?.id) {
        workDocumentSocket.stopEditing(this.currentDocument.id)
        workDocumentSocket.leaveDocument(this.currentDocument.id)
      }
      workDocumentSocket.disconnect()
    },
    showNotification(message) {
      // Simple notification - could be enhanced with a toast library
      alert(message)
    },
    scheduleAutoSave() {
      if (this.autoSaveTimer) {
        clearTimeout(this.autoSaveTimer)
      }
      
      // Auto-save after 2 seconds of no typing
      this.autoSaveTimer = setTimeout(() => {
        this.autoSave()
      }, 2000)
    },
    async autoSave() {
      if (!this.editMode || !this.currentDocument) {
        return
      }

      if (!this.editForm.title.trim()) {
        return
      }

      try {
        const { data } = await apiClient.put(`/admin/work-documents/${this.currentDocument.id}`, {
          title: this.editForm.title,
          content: this.editForm.content
        })
        this.currentDocument = data
        console.log('Auto-saved at', new Date().toLocaleTimeString())
      } catch (e) {
        console.error('Auto-save failed:', e)
      }
    },
    notifyTyping() {
      if (this.typingTimer) {
        clearTimeout(this.typingTimer)
      }
      
      // Notify every 3 seconds while typing
      this.typingTimer = setTimeout(() => {
        if (this.editMode && this.currentDocument) {
          workDocumentSocket.notifyTyping(this.currentDocument.id)
        }
      }, 3000)
    }
  }
}
</script>

<style scoped>
.work-arrangement-page {
  width: 100%;
}

.header-actions {
  display: flex;
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-lg);
  align-items: center;
}

.page-title {
  flex: 1;
}

.page-title h1 {
  font-size: 1.75rem;
  font-weight: 600;
  margin: 0;
  color: var(--md-on-surface);
}

.documents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: var(--md-spacing-lg);
  margin-bottom: var(--md-spacing-xl);
}

.document-card {
  background: var(--md-surface);
  border: 1px solid var(--md-surface-variant);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  cursor: pointer;
  transition: var(--transition-fast);
  box-shadow: var(--md-elevation-1);
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.document-card:hover {
  box-shadow: var(--md-elevation-3);
  border-color: var(--md-primary);
  transform: translateY(-2px);
}

.document-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--md-spacing-md);
  padding-bottom: var(--md-spacing-sm);
  border-bottom: 2px solid var(--md-surface-variant);
}

.document-card-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
  color: var(--md-on-surface);
  flex: 1;
}

.document-card-date {
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  white-space: nowrap;
}

.document-card-meta {
  display: flex;
  gap: var(--md-spacing-md);
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.document-card-preview {
  flex: 1;
  overflow: hidden;
  position: relative;
  max-height: 200px;
  font-size: 0.9rem;
  line-height: 1.6;
}

.document-card-preview::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  background: linear-gradient(to bottom, transparent, var(--md-surface));
}

.document-card-preview .preview-empty {
  color: var(--md-on-surface-variant);
  font-style: italic;
  margin: 0;
}

.document-card-preview h1,
.document-card-preview h2,
.document-card-preview h3 {
  font-size: 1rem;
  margin: var(--md-spacing-xs) 0;
  font-weight: 600;
}

.document-card-preview p {
  margin: var(--md-spacing-xs) 0;
  font-size: 0.875rem;
}

.document-card-preview ul,
.document-card-preview ol {
  margin: var(--md-spacing-xs) 0;
  padding-left: 1.5rem;
}

.document-card-preview li {
  margin: 2px 0;
  font-size: 0.875rem;
}

.document-select {
  flex: 1;
  min-width: 200px;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-surface-variant);
  border-radius: var(--md-radius-md);
  background: var(--md-surface);
  color: var(--md-on-surface);
  font-size: var(--md-body-size);
  cursor: pointer;
}

.document-select:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 2px rgba(255, 140, 0, 0.2);
}

.btn-primary, .btn-secondary, .btn-danger {
  padding: var(--md-spacing-sm) var(--md-spacing-lg);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: var(--transition-fast);
}

.btn-primary {
  background: var(--md-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #e67e00;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--md-surface);
  border: 1px solid var(--md-outline);
  color: var(--md-on-surface);
}

.btn-secondary:hover {
  background: var(--md-surface-variant);
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}

.btn-sm {
  padding: var(--md-spacing-xs) var(--md-spacing-md);
  font-size: var(--md-label-size);
}

.btn-link {
  background: none;
  border: none;
  color: var(--md-primary);
  cursor: pointer;
  font-size: var(--md-label-size);
  padding: var(--md-spacing-xs);
}

.btn-link:hover {
  text-decoration: underline;
}

.btn-link.btn-danger {
  color: #dc3545;
}

.loading, .error, .empty-state {
  padding: var(--md-spacing-xl);
  text-align: center;
  color: var(--md-on-surface-variant);
}

.error {
  color: #dc3545;
}

.document-editor {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
}

.editor-notification {
  background: rgba(255, 140, 0, 0.1);
  border: 1px solid var(--md-primary);
  border-radius: var(--md-radius-md);
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  margin-bottom: var(--md-spacing-md);
  display: flex;
  align-items: center;
  gap: var(--md-spacing-sm);
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
}

.editor-indicator {
  font-size: 0.75rem;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.title-section {
  margin-bottom: var(--md-spacing-lg);
}

.title-input {
  width: 100%;
  font-size: 2rem;
  font-weight: 600;
  border: none;
  border-bottom: 2px solid var(--md-surface-variant);
  padding: var(--md-spacing-sm) 0;
  margin-bottom: var(--md-spacing-sm);
  color: var(--md-on-surface);
  background: transparent;
}

.title-input:focus {
  outline: none;
  border-bottom-color: var(--md-primary);
}

.document-title {
  font-size: 2rem;
  font-weight: 600;
  margin: 0 0 var(--md-spacing-sm);
  color: var(--md-on-surface);
}

.document-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--md-spacing-md);
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
}

.editor-controls {
  display: flex;
  gap: var(--md-spacing-sm);
  margin-bottom: var(--md-spacing-lg);
  padding-bottom: var(--md-spacing-md);
  border-bottom: 1px solid var(--md-surface-variant);
}

.content-section {
  margin-bottom: var(--md-spacing-xl);
}

.editor-container {
  border: 1px solid var(--md-surface-variant);
  border-radius: var(--md-radius-md);
  overflow: hidden;
}

.editor-tabs {
  display: flex;
  border-bottom: 1px solid var(--md-surface-variant);
  background: var(--md-surface-variant);
}

.editor-tab {
  padding: var(--md-spacing-sm) var(--md-spacing-lg);
  border: none;
  background: transparent;
  color: var(--md-on-surface-variant);
  cursor: pointer;
  font-size: var(--md-body-size);
}

.editor-tab.active {
  background: var(--md-surface);
  color: var(--md-primary);
  font-weight: 500;
}

.content-textarea {
  width: 100%;
  min-height: 500px;
  padding: var(--md-spacing-lg);
  border: none;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: var(--md-body-size);
  line-height: 1.6;
  resize: vertical;
  color: var(--md-on-surface);
  background: var(--md-surface);
}

.content-textarea:focus {
  outline: none;
}

.content-preview, .content-display {
  padding: var(--md-spacing-lg);
  min-height: 300px;
}

.markdown-body {
  line-height: 1.8;
  color: var(--md-on-surface);
}

.markdown-body h1 {
  font-size: 1.75rem;
  font-weight: 600;
  margin: calc(var(--md-spacing-xl) * 1.5) 0 var(--md-spacing-md);
  border-bottom: 2px solid var(--md-surface-variant);
  padding-bottom: var(--md-spacing-sm);
}

.markdown-body h1:first-child {
  margin-top: 0;
}

.markdown-body h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: var(--md-spacing-xl) 0 var(--md-spacing-md);
}

.markdown-body h3 {
  font-size: 1.25rem;
  font-weight: 500;
  margin: var(--md-spacing-lg) 0 var(--md-spacing-md);
}

.markdown-body ul, .markdown-body ol {
  margin: var(--md-spacing-md) 0;
  padding-left: 2rem;
}

.markdown-body li {
  margin: var(--md-spacing-sm) 0;
  line-height: 1.8;
}

.markdown-body li p {
  margin: 0;
}

.markdown-body li ul,
.markdown-body li ol {
  margin: var(--md-spacing-xs) 0;
}

.markdown-body p {
  margin: var(--md-spacing-md) 0;
  line-height: 1.8;
}

.markdown-body p:empty {
  margin: var(--md-spacing-sm) 0;
  line-height: 1;
}

.markdown-body br {
  display: block;
  margin: var(--md-spacing-md) 0;
  content: "";
  line-height: var(--md-spacing-lg);
}

.markdown-body code {
  background: var(--md-surface-variant);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-body pre {
  background: var(--md-surface-variant);
  padding: var(--md-spacing-md);
  border-radius: var(--md-radius-md);
  overflow-x: auto;
}

.markdown-body pre code {
  background: transparent;
  padding: 0;
}

.action-items-section {
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  padding: var(--md-spacing-lg);
  box-shadow: var(--md-elevation-1);
  margin-top: var(--md-spacing-xl);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--md-spacing-lg);
}

.section-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  color: var(--md-on-surface);
}

.loading-small {
  text-align: center;
  padding: var(--md-spacing-md);
  color: var(--md-on-surface-variant);
}

.empty-state-small {
  text-align: center;
  padding: var(--md-spacing-xl);
  color: var(--md-on-surface-variant);
  background: var(--md-surface-variant);
  border-radius: var(--md-radius-md);
}

.action-items-list {
  display: flex;
  flex-direction: column;
  gap: var(--md-spacing-md);
}

.action-item-card {
  padding: var(--md-spacing-md);
  border: 1px solid var(--md-surface-variant);
  border-radius: var(--md-radius-md);
  background: var(--md-surface);
  transition: var(--transition-fast);
}

.action-item-card:hover {
  box-shadow: var(--md-elevation-2);
}

.action-item-card.status-completed {
  background: rgba(46, 125, 50, 0.05);
  border-left: 3px solid #2e7d32;
}

.action-item-card.status-in_progress {
  background: rgba(255, 140, 0, 0.05);
  border-left: 3px solid var(--md-primary);
}

.action-item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--md-spacing-md);
  margin-bottom: var(--md-spacing-sm);
}

.action-item-title {
  font-size: 1.125rem;
  font-weight: 500;
  margin: 0;
  color: var(--md-on-surface);
  flex: 1;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge.status-pending {
  background: rgba(158, 158, 158, 0.2);
  color: #424242;
}

.status-badge.status-in_progress {
  background: rgba(255, 140, 0, 0.2);
  color: #e65100;
}

.status-badge.status-completed {
  background: rgba(46, 125, 50, 0.2);
  color: #1b5e20;
}

.status-badge.status-cancelled {
  background: rgba(198, 40, 40, 0.2);
  color: #c62828;
}

.action-item-description {
  margin: var(--md-spacing-sm) 0;
  color: var(--md-on-surface-variant);
  font-size: var(--md-body-size);
}

.action-item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--md-spacing-md);
  font-size: var(--md-label-size);
  color: var(--md-on-surface-variant);
  margin: var(--md-spacing-sm) 0;
}

.action-item-actions {
  display: flex;
  gap: var(--md-spacing-md);
  margin-top: var(--md-spacing-sm);
  padding-top: var(--md-spacing-sm);
  border-top: 1px solid var(--md-surface-variant);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--md-spacing-md);
}

.modal-box {
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  background: var(--md-surface);
  border-radius: var(--md-radius-lg);
  box-shadow: var(--md-elevation-4);
  display: flex;
  flex-direction: column;
}

.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--md-spacing-lg);
  border-bottom: 1px solid var(--md-surface-variant);
}

.modal-head h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--md-on-surface);
}

.close-x {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--md-on-surface-variant);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--md-radius-sm);
}

.close-x:hover {
  background: var(--md-surface-variant);
}

.modal-body {
  padding: var(--md-spacing-lg);
  overflow-y: auto;
}

.field-label {
  display: block;
  font-size: var(--md-label-size);
  font-weight: 500;
  color: var(--md-on-surface);
  margin-bottom: var(--md-spacing-xs);
  margin-top: var(--md-spacing-md);
}

.field-label:first-child {
  margin-top: 0;
}

.field-input, .field-textarea {
  width: 100%;
  padding: var(--md-spacing-sm) var(--md-spacing-md);
  border: 1px solid var(--md-surface-variant);
  border-radius: var(--md-radius-md);
  font-size: var(--md-body-size);
  color: var(--md-on-surface);
  background: var(--md-surface);
  box-sizing: border-box;
}

.field-input:focus, .field-textarea:focus {
  outline: none;
  border-color: var(--md-primary);
  box-shadow: 0 0 0 2px rgba(255, 140, 0, 0.2);
}

.field-textarea {
  resize: vertical;
  font-family: inherit;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--md-spacing-sm);
  margin-top: var(--md-spacing-lg);
  padding-top: var(--md-spacing-md);
  border-top: 1px solid var(--md-surface-variant);
}

@media (max-width: 767px) {
  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .documents-grid {
    grid-template-columns: 1fr;
  }

  .document-select {
    width: 100%;
  }

  .document-title {
    font-size: 1.5rem;
  }

  .document-editor {
    padding: var(--md-spacing-md);
  }

  .editor-controls {
    flex-wrap: wrap;
  }

  .content-textarea {
    min-height: 400px;
  }

  .modal-overlay {
    align-items: flex-end;
    padding: 0;
  }

  .modal-box {
    max-width: 100%;
    max-height: 95vh;
    border-radius: var(--md-radius-lg) var(--md-radius-lg) 0 0;
  }
}
</style>
