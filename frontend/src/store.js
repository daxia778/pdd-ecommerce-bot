import { reactive } from 'vue';
import { DEMO_SESSIONS, DEMO_CHATS, DEMO_ESCALATIONS, DEMO_ORDERS, DEMO_STATS, DEMO_KNOWLEDGE } from './demoData.js';

// 后端 API 基础地址（懒加载兼容 dev proxy 和生产环境）
const API_BASE = '/admin/api/admin';

export const store = reactive({
    // ===== Auth =====
    token: localStorage.getItem('pdd_admin_token') || '',
    isLoggedIn: !!localStorage.getItem('pdd_admin_token'),

    // ===== UI 状态 =====
    sidebarCollapsed: localStorage.getItem('pdd_sidebar_collapsed') === 'true',

    // ===== 数据 =====
    activePanel: 'monitor',
    stats: DEMO_STATS,
    sessions: DEMO_SESSIONS,
    escalations: DEMO_ESCALATIONS,
    orders: DEMO_ORDERS,
    knowledgeBase: DEMO_KNOWLEDGE,

    // ===== 对话 =====
    selectedUser: null,
    currentChat: [],

    // ===== Shadow Chat 状态 =====
    pausedSessions: {},   // { user_id: true/false }
    sendingMessage: false,

    // ===== 连接 =====
    ws: null,
    wsRetryTimer: null,
    _wsRetryCount: 0,       // P1-3: 退避计数器，重连成功后归零
    pollInterval: null,

    // ========== Auth ==========

    async login(username, password) {
        const res = await fetch('/api/v1/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        if (!res.ok) throw new Error('用户名或密码错误');
        const data = await res.json();
        this.token = data.access_token;
        localStorage.setItem('pdd_admin_token', this.token);
        this.isLoggedIn = true;
        this.connect();
    },

    logout() {
        this.token = '';
        this.isLoggedIn = false;
        localStorage.removeItem('pdd_admin_token');
        this.disconnect();
    },

    _headers() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`,
        };
    },

    // ========== 数据获取 ==========

    async fetchData() {
        try {
            const headers = this._headers();
            const [resStats, resSessions, resEsc, resOrders] = await Promise.all([
                fetch('/api/dashboard/stats', { headers }),
                fetch('/api/dashboard/sessions', { headers }),
                fetch('/api/dashboard/escalations', { headers }),
                fetch('/api/dashboard/orders', { headers }),
            ]);
            if (resStats.ok) {
                const data = await resStats.json();
                if (data.active_sessions > 0 || data.pending_escalations > 0 || data.active_orders > 0) {
                    this.stats = { ...DEMO_STATS, ...data }; // Merge so we don't lose the new mock fields if backend doesn't have them
                } else {
                    this.stats = DEMO_STATS;
                }
            }
            if (resSessions.ok) {
                const data = await resSessions.json();
                const backendIds = new Set(data.map(s => s.user_id));
                const filteredDemo = DEMO_SESSIONS.filter(s => !backendIds.has(s.user_id));
                // 合并后将 simulator 来源会话置顶
                const merged = [...data, ...filteredDemo];
                merged.sort((a, b) => {
                    const aIsSim = a.platform === 'simulator' ? 1 : 0;
                    const bIsSim = b.platform === 'simulator' ? 1 : 0;
                    return bIsSim - aIsSim; // simulator 在前
                });
                this.sessions = merged;
            }
            if (resEsc.ok) {
                const data = await resEsc.json();
                const backendIds = new Set(data.map(e => e.id));
                const filteredDemo = DEMO_ESCALATIONS.filter(e => !backendIds.has(e.id));
                this.escalations = [...data, ...filteredDemo];
            }
            if (resOrders.ok) {
                const data = await resOrders.json();
                const backendIds = new Set(data.map(o => o.id));
                const filteredDemo = DEMO_ORDERS.filter(o => !backendIds.has(o.id));
                this.orders = [...data, ...filteredDemo];
            }

            if (this.selectedUser && this.activePanel === 'monitor') {
                await this.viewChat(this.selectedUser, true);
            }
            if (this.activePanel === 'knowledge' && this.knowledgeBase.length === 0) {
                await this.loadKnowledge();
            }
        } catch (e) {
            console.error('fetchData error:', e);
        }
    },

    async loadKnowledge() {
        try {
            const res = await fetch(`${API_BASE}/knowledge`, { headers: this._headers() });
            const result = await res.json();
            if (result.status === 'success' && result.data && result.data.length > 0) {
                this.knowledgeBase = result.data;
            } else {
                this.knowledgeBase = DEMO_KNOWLEDGE;
            }
        } catch (e) {
            console.error(e);
            this.knowledgeBase = DEMO_KNOWLEDGE;
        }
    },

    async viewChat(userId, scroll = true) {
        this.selectedUser = userId;

        if (DEMO_CHATS[userId] !== undefined) {
            this.currentChat = DEMO_CHATS[userId] || [];
            if (scroll) {
                setTimeout(() => {
                    const el = document.getElementById('chat-window');
                    if (el) el.scrollTop = el.scrollHeight;
                }, 50);
            }
            return;
        }

        try {
            const res = await fetch(`/api/dashboard/messages/${userId}`, { headers: this._headers() });
            if (res.ok) this.currentChat = await res.json();
            if (scroll) {
                setTimeout(() => {
                    const el = document.getElementById('chat-window');
                    if (el) el.scrollTop = el.scrollHeight;
                }, 50);
            }
        } catch (e) { console.error(e); }
    },

    // ========== 全局搜索 ==========
    searchMatchedUserIds: [],  // 后端搜索返回的 user_id 列表
    searchLoading: false,

    async searchMessages(q) {
        if (!q || !q.trim()) {
            this.searchMatchedUserIds = [];
            return;
        }
        this.searchLoading = true;
        try {
            const res = await fetch(`/api/dashboard/search?q=${encodeURIComponent(q.trim())}`, {
                headers: this._headers(),
            });
            if (res.ok) {
                const data = await res.json();
                this.searchMatchedUserIds = data.matched_user_ids || [];
            }
        } catch (e) {
            console.error('searchMessages error:', e);
        } finally {
            this.searchLoading = false;
        }
    },

    // ========== 需求提取 ==========
    extractedRequirements: {},  // { user_id: { topic, pages, ... } }
    extractingUser: null,

    async extractRequirements(userId) {
        if (!userId) return null;
        this.extractingUser = userId;
        try {
            const res = await fetch(`/api/dashboard/messages/${userId}/extract_requirements`, {
                headers: this._headers(),
            });
            if (res.ok) {
                const data = await res.json();
                this.extractedRequirements[userId] = data;
                return data;
            }
        } catch (e) {
            console.error('extractRequirements error:', e);
        } finally {
            this.extractingUser = null;
        }
        return null;
    },

    // ========== Shadow Chat ==========

    async togglePause(userId) {
        try {
            const res = await fetch(`${API_BASE}/sessions/${userId}/pause`, {
                method: 'POST',
                headers: this._headers(),
                body: JSON.stringify({}),  // 空 body = toggle
            });
            const data = await res.json();
            this.pausedSessions[userId] = data.is_paused;
            return data;
        } catch (e) {
            console.error('togglePause error:', e);
        }
    },

    async checkPauseState(userId) {
        // 初始化/刷新某用户的暂停状态（通过 WS 事件自动更新，这里备用）
        // 注意：当前无单独 GET 接口，状态由 WS 推送维护
        return this.pausedSessions[userId] || false;
    },

    async sendManualMessage(userId, content, operatorName = '人工客服') {
        if (!content.trim()) return;
        this.sendingMessage = true;
        try {
            const res = await fetch(`${API_BASE}/sessions/${userId}/send_message`, {
                method: 'POST',
                headers: this._headers(),
                body: JSON.stringify({ content, operator_name: operatorName }),
            });
            const data = await res.json();
            // 立即刷新对话记录
            await this.viewChat(userId, true);
            return data;
        } catch (e) {
            console.error('sendManualMessage error:', e);
        } finally {
            this.sendingMessage = false;
        }
    },

    // ========== PPT 工单操作 ==========

    async claimOrder(id) {
        try {
            const res = await fetch(`/api/dashboard/orders/${id}/claim`, {
                method: 'POST',
                headers: this._headers(),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            this.fetchData();
        } catch (e) {
            console.error('claimOrder error:', e);
        }
    },

    async deliverOrder(id) {
        try {
            const res = await fetch(`/api/dashboard/orders/${id}/deliver`, {
                method: 'POST',
                headers: this._headers(),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            this.fetchData();
        } catch (e) {
            console.error('deliverOrder error:', e);
        }
    },

    // Bug修复: 增加统一的 resolveEscalation 方法，复用 _headers()
    async resolveEscalation(id) {
        try {
            const res = await fetch(`/api/dashboard/escalations/${id}/resolve`, {
                method: 'POST',
                headers: this._headers(),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            this.fetchData();
        } catch (e) {
            console.error('resolveEscalation error:', e);
        }
    },

    // ========== WebSocket ==========

    connect() {
        if (!this.isLoggedIn) return;
        this.fetchData();  // 立即拉一次

        // WebSocket 实时推送
        const wsUrl = `ws://${location.host}/ws?token=${this.token}`;
        this._connectWS(wsUrl);

        // 兜底轮询（30s），WS 正常时也保持数据新鲜
        this.pollInterval = setInterval(() => this.fetchData(), 30000);
    },

    _connectWS(wsUrl) {
        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('✅ WebSocket 已连接');
                // P1-3: 重连成功，清零退避计数器
                this._wsRetryCount = 0;
                if (this.wsRetryTimer) {
                    clearTimeout(this.wsRetryTimer);
                    this.wsRetryTimer = null;
                }
                this.wsHeartbeat = setInterval(() => {
                    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                        this.ws.send(JSON.stringify({ type: "ping" }));
                    }
                }, 30000);
            };

            this.ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    this._handleWSEvent(msg);
                } catch (e) { /* ignore */ }
            };

            this.ws.onclose = () => {
                if (this.wsHeartbeat) clearInterval(this.wsHeartbeat);
                // P1-3: 指数退避 + Jitter，防止服务恢复时所有客户端同时重连形成雪崩
                // delay = min(2^attempt × 1000 + 随机抖动[0~1000ms], 30000ms)
                const attempt = this._wsRetryCount++;
                const baseDelay = Math.min(Math.pow(2, attempt) * 1000, 30000);
                const jitter = Math.random() * 1000;
                const delay = Math.floor(baseDelay + jitter);
                console.warn(`⚠️ WebSocket 断开，${(delay / 1000).toFixed(1)}s 后重试（第 ${attempt + 1} 次）...`);
                this.wsRetryTimer = setTimeout(() => this._connectWS(wsUrl), delay);
            };

            this.ws.onerror = () => {
                this.ws?.close();
            };
        } catch (e) {
            console.error('WS 连接失败，使用轮询模式', e);
        }
    },

    _handleWSEvent(msg) {
        const { event, user_id } = msg;
        switch (event) {
            case 'update':
                this.fetchData();
                break;
            case 'new_escalation':
                this.fetchData();
                // P2: 转人工请求时触发浏览器框查阅通知
                this._notify(
                    '⚠️ 新转人工请求',
                    `买家 ${user_id || ''} 需要人工客服介入`
                );
                break;
            case 'ai_pause_toggled':
                this.pausedSessions[user_id] = msg.is_paused;
                break;
            case 'manual_message_sent':
                if (this.selectedUser === user_id) {
                    this.viewChat(user_id, true);
                }
                break;
            case 'escalation_claimed':
            case 'escalation_resolved':
                this.fetchData();
                break;
        }
    },

    // P2: 封装 Web Notification API
    _notify(title, body) {
        if (!('Notification' in window)) return;
        const send = () => new Notification(title, {
            body,
            icon: '/favicon.ico',
            tag: 'pdd-escalation'
        });
        if (Notification.permission === 'granted') {
            send();
        }
    },

    disconnect() {
        if (this.ws) { this.ws.close(); this.ws = null; }
        if (this.pollInterval) { clearInterval(this.pollInterval); this.pollInterval = null; }
        if (this.wsRetryTimer) { clearTimeout(this.wsRetryTimer); this.wsRetryTimer = null; }
        if (this.wsHeartbeat) { clearInterval(this.wsHeartbeat); this.wsHeartbeat = null; }
    },

    // 兼容旧版轮询接口
    startPolling() { this.connect(); },
    stopPolling() { this.disconnect(); },

    // ========== DLQ 监控 ==========

    dlqStatus: { retry_queue_size: 0, dead_letter_queue_size: 0, dead_letters: [] },

    async fetchDLQ() {
        try {
            const res = await fetch('/api/dashboard/dlq', { headers: this._headers() });
            if (res.ok) this.dlqStatus = await res.json();
        } catch (e) { console.error('fetchDLQ error:', e); }
    },

    async retryAllDLQ() {
        try {
            const res = await fetch('/api/dashboard/dlq/retry-all', {
                method: 'POST',
                headers: this._headers(),
            });
            const data = await res.json();
            alert(data.msg || '操作完成');
            await this.fetchDLQ();
        } catch (e) { console.error('retryAllDLQ error:', e); }
    },

    // ========== Prompt 话术管理 ==========

    promptContent: '',
    promptLoading: false,
    promptSaving: false,

    async loadPrompt(name = 'ppt_consultant') {
        this.promptLoading = true;
        try {
            const res = await fetch(`/api/dashboard/prompts/${name}`, { headers: this._headers() });
            if (res.ok) {
                const data = await res.json();
                this.promptContent = data.content;
            }
        } catch (e) { console.error('loadPrompt error:', e); }
        finally { this.promptLoading = false; }
    },

    async savePrompt(name = 'ppt_consultant') {
        this.promptSaving = true;
        try {
            const res = await fetch(`/api/dashboard/prompts/${name}`, {
                method: 'PUT',
                headers: this._headers(),
                body: JSON.stringify({ content: this.promptContent }),
            });
            const data = await res.json();
            if (data.status === 'ok') {
                alert('✅ ' + data.msg);
            } else {
                alert('❌ 保存失败: ' + (data.detail || data.msg || '未知错误'));
            }
        } catch (e) {
            console.error('savePrompt error:', e);
            alert('❌ 保存失败: ' + e.message);
        }
        finally { this.promptSaving = false; }
    },

    // ========== 系统健康度 ==========

    systemHealth: { overall: 'healthy', components: [] },
    healthLoading: false,

    async fetchSystemHealth() {
        this.healthLoading = true;
        try {
            const res = await fetch('/api/dashboard/system-health', { headers: this._headers() });
            if (res.ok) this.systemHealth = await res.json();
        } catch (e) { console.error('fetchSystemHealth error:', e); }
        finally { this.healthLoading = false; }
    },

    // ========== 知识库批量导入 ==========

    async importKnowledgeFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        try {
            const res = await fetch('/api/admin/knowledge/import', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${this.token}` },
                body: formData,
            });
            const data = await res.json();
            if (data.status === 'success') {
                alert(`✅ ${data.msg}`);
                await this.loadKnowledge();
            } else {
                alert('❌ 导入失败: ' + (data.detail || data.msg || '未知错误'));
            }
            return data;
        } catch (e) {
            console.error('importKnowledge error:', e);
            alert('❌ 导入失败: ' + e.message);
        }
    },
});
