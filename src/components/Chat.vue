<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="header-title">
        <span class="icon">🛩️</span>
        <h2>UAV Log Assistant</h2>
      </div>
      <span class="status-indicator">{{ state.chatMessages.length > 0 ? 'Active' : 'Ready' }}</span>
    </div>
    <div class="messages-container" ref="messagesContainer">
      <div v-if="state.chatMessages.length === 0" class="empty-state">
        <div class="empty-icon">💬</div>
        <p>Ask questions about your flight data.</p>
        <p class="hint">Try asking about altitude, speed, or flight patterns.</p>
      </div>
      <div v-else class="messages-list">
        <div 
          v-for="(message, index) in state.chatMessages" 
          :key="index" 
          :class="['message-wrapper', message.from]"
        >
          <div class="avatar" v-if="message.from === 'assistant'">🤖</div>
          <div class="message-bubble">
            <div class="message-content">{{ message.text }}</div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
          <div class="avatar" v-if="message.from === 'user'">👤</div>
        </div>
      </div>
    </div>
    <div class="input-container">
      <input
        v-model="question"
        @keyup.enter="send"
        :disabled="loading"
        placeholder="Ask about your flight data..."
        class="message-input"
      />
      <button 
        @click="send" 
        :disabled="loading || !question.trim()" 
        class="send-button"
      >
        <span v-if="!loading">Send</span>
        <span v-else class="loading-indicator">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </span>
      </button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { store } from './Globals.js'

export default {
  name: 'Chat',
  data() {
    return {
      question: '',
      loading: false,
      state: store
    }
  },
  methods: {
    async send() {
      if (!this.question.trim()) {
        return
      }
      const q = this.question
      
      // Add user message to global state
      this.state.chatMessages.push({ 
        from: 'user', 
        text: q,
        timestamp: new Date()
      })
      
      this.question = ''
      this.loading = true
      
      // Scroll to bottom immediately after user message
      this.$nextTick(() => {
        this.scrollToBottom()
      })
      
      try {
        const response = await axios.post('http://localhost:8000/ask', {
          question: q
        })
        
        if (response.data.error) {
          // Add error message to global state
          this.state.chatMessages.push({
            from: 'assistant',
            text: `Error: ${response.data.error}`,
            timestamp: new Date()
          })
        } else {
          // Add response to global state
          this.state.chatMessages.push({
            from: 'assistant',
            text: response.data.answer,
            timestamp: new Date()
          })
        }
      } catch (error) {
        // Add error message to global state
        this.state.chatMessages.push({
          from: 'assistant',
          text: 'Request failed. Please try again later.',
          timestamp: new Date()
        })
      } finally {
        this.loading = false
        // Scroll to bottom after receiving response
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      }
    },
    scrollToBottom() {
      if (this.$refs.messagesContainer) {
        this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight
      }
    },
    formatTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  },
  mounted() {
    // Initialize with welcome message if no messages exist
    if (this.state.chatMessages.length === 0) {
      this.state.chatMessages.push({
        from: 'assistant',
        text: 'Hello! I can help you analyze your UAV flight data. What would you like to know?',
        timestamp: new Date()
      })
    }
    this.scrollToBottom()
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex: 1 1 auto; 
  flex-direction: column;
  background-color: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  height: 90%; 
  overflow: relative;
  position: absolute;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #24344d;
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  min-height: 50px;
  width: 100%;
  box-sizing: border-box;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 15;
}

/* Responsive adjustments */
@media (max-width: 992px) {
  .chat-container {
    width: 100%;
    max-height: 800px;
    margin: 0;
    border-radius: 0;
  }
  
  .header-title h2 {
    font-size: 1em;
  }
}

@media (max-width: 576px) {
  .chat-container {
    position: fixed;
    top: 56px;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    height: auto;
    max-height: calc(100vh - 56px);
    margin: 0;
    z-index: 2000;
  }
  
  .chat-header {
    padding: 12px;
  }
  
  .header-title .icon {
    font-size: 1.2em;
  }
  
  .messages-container {
    bottom: 60px;
  }
  
  .input-container {
    min-height: 60px;
  }
}

.header-title {
  display: flex;
  align-items: center;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-title .icon {
  margin-right: 8px;
  font-size: 1.5em;
  flex-shrink: 0;
}

.header-title h2 {
  margin: 0;
  font-size: 1.2em;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-indicator {
  padding: 4px 10px;
  background-color: rgba(0, 255, 0, 0.2);
  border-radius: 12px;
  font-size: 0.8em;
  flex-shrink: 0;
  margin-left: 8px;
}

.messages-container {
  flex: 1 1 auto;  
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  top: 60px;
  bottom: 65px;
  left: 0;
  right: 0;
  height: 90%;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #666;
  padding: 24px;
  text-align: center;
}

.empty-icon {
  font-size: 3em;
  margin-bottom: 16px;
  opacity: 0.6;
}

.hint {
  font-size: 0.9em;
  opacity: 0.7;
  margin-top: 8px;
}

.messages-list {
  display: flex;
  flex-direction: column;
  width: 100%; /* Full width */
}

.message-wrapper {
  display: flex;
  margin-bottom: 16px;
  align-items: flex-end;
  width: 100%; /* Full width */
}

.message-wrapper.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 8px;
  font-size: 1.2em;
  flex-shrink: 0; /* Prevent avatar from shrinking */
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 18px;
  position: relative;
  word-break: break-word;
}

.user .message-bubble {
  background-color: #1a73e8;
  color: white;
  border-bottom-right-radius: 4px;
}

.assistant .message-bubble {
  background-color: white;
  color: black;
  border-bottom-left-radius: 4px;
}

.message-content {
  line-height: 1.4;
}

.message-time {
  font-size: 0.7em;
  opacity: 0.7;
  text-align: right;
  margin-top: 4px;
}

.input-container {
  display: flex;
  padding: 10px 12px;
  background-color: white;
  border-top: 1px solid #e0e0e0;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 10;
  min-height: 60px;
  box-sizing: border-box;
  flex-shrink: 0;
  box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.05);
}

.message-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 24px;
  outline: none;
  font-size: 14px;
  transition: border-color 0.2s;
  max-height: 40px; 
}

.message-input:focus {
  border-color: #1a73e8;
  box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
}

.send-button {
  margin-left: 8px;
  padding: 6px 14px;
  background-color: #1a73e8;
  color: white;
  border: none;
  border-radius: 24px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
  flex-shrink: 0;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-button:hover:not(:disabled) {
  background-color: #0d62cb;
}

.send-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.loading-indicator {
  display: flex;
  justify-content: center;
  align-items: center;
}

.dot {
  width: 6px;
  height: 6px;
  background-color: white;
  border-radius: 50%;
  margin: 0 2px;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}
</style>