import { io } from 'socket.io-client'

class WorkDocumentSocket {
  constructor() {
    this.socket = null
    this.token = null
    this.currentDocumentId = null
    this.listeners = {}
  }

  connect(token) {
    // Always update token even if already connected
    this.token = token
    
    if (this.socket?.connected) {
      return
    }
    // Use the same base URL as API client, but remove '/api' suffix for WebSocket
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5015/api'
    const apiUrl = baseUrl.replace('/api', '')
    
    this.socket = io(apiUrl, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity
    })

    this.socket.on('connect', () => {
      console.log('WebSocket connected')
      if (this.listeners.connected) {
        this.listeners.connected()
      }
    })

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected')
      if (this.listeners.disconnected) {
        this.listeners.disconnected()
      }
    })

    this.socket.on('connected', (data) => {
      console.log('Server confirmed connection:', data)
    })

    this.socket.on('document_changed', (data) => {
      console.log('Document changed:', data)
      if (this.listeners.documentChanged) {
        this.listeners.documentChanged(data)
      }
    })

    this.socket.on('editor_started', (data) => {
      console.log('Editor started:', data)
      if (this.listeners.editorStarted) {
        this.listeners.editorStarted(data)
      }
    })

    this.socket.on('editor_stopped', (data) => {
      console.log('Editor stopped:', data)
      if (this.listeners.editorStopped) {
        this.listeners.editorStopped(data)
      }
    })

    this.socket.on('user_typing', (data) => {
      if (this.listeners.userTyping) {
        this.listeners.userTyping(data)
      }
    })

    this.socket.on('user_joined', (data) => {
      console.log('User joined:', data)
    })

    this.socket.on('editor_status', (data) => {
      console.log('Editor status:', data)
      if (this.listeners.editorStatus) {
        this.listeners.editorStatus(data)
      }
    })

    this.socket.on('editor_left', (data) => {
      console.log('Editor left:', data)
      if (this.listeners.editorLeft) {
        this.listeners.editorLeft(data)
      }
    })
  }

  disconnect() {
    if (this.socket) {
      if (this.currentDocumentId) {
        this.leaveDocument(this.currentDocumentId)
      }
      this.socket.disconnect()
      this.socket = null
    }
  }

  joinDocument(documentId) {
    if (!this.socket?.connected) {
      console.warn('Socket not connected')
      return
    }

    this.currentDocumentId = documentId
    this.socket.emit('join_document', {
      document_id: documentId,
      token: this.token
    })
  }

  leaveDocument(documentId) {
    if (!this.socket?.connected) {
      return
    }

    if (this.currentDocumentId === documentId) {
      this.currentDocumentId = null
    }

    this.socket.emit('leave_document', {
      document_id: documentId
    })
  }

  startEditing(documentId) {
    if (!this.socket?.connected) {
      console.warn('Socket not connected')
      return Promise.reject(new Error('Socket not connected'))
    }

    return new Promise((resolve, reject) => {
      this.socket.emit('start_editing', {
        document_id: documentId,
        token: this.token
      }, (response) => {
        if (response?.success) {
          resolve(response)
        } else {
          reject(new Error(response?.error || 'Failed to start editing'))
        }
      })
    })
  }

  stopEditing(documentId) {
    if (!this.socket?.connected) {
      return
    }

    this.socket.emit('stop_editing', {
      document_id: documentId,
      token: this.token
    })
  }

  notifyTyping(documentId) {
    if (!this.socket?.connected) {
      return
    }

    this.socket.emit('typing', {
      document_id: documentId,
      token: this.token
    })
  }

  notifyDocumentUpdated(documentId) {
    if (!this.socket?.connected) {
      return
    }

    this.socket.emit('document_updated', {
      document_id: documentId,
      token: this.token
    })
  }

  on(event, callback) {
    this.listeners[event] = callback
  }

  off(event) {
    delete this.listeners[event]
  }
}

export const workDocumentSocket = new WorkDocumentSocket()
