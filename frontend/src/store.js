import { reactive } from 'vue';

// 后端 API 基础地址（懒加载兼容 dev proxy 和生产环境）
const API_BASE = '/admin/api/admin';

export const store = reactive({
    // ===== Auth =====
    token: localStorage.getItem('pdd_admin_token') || '',
    isLoggedIn: !!localStorage.getItem('pdd_admin_token'),

    // ===== 数据 =====
    activePanel: 'monitor',
    stats: { active_sessions: 0, pending_escalations: 0, active_orders: 0 },
    sessions: [],
    escalations: [],
    orders: [],
    knowledgeBase: [],

    // ===== 对话 =====
    selectedUser: null,
    currentChat: [],

    // ===== Shadow Chat 状态 =====
    pausedSessions: {},   // { user_id: true/false }
    sendingMessage: false,

    // ===== 连接 =====
    ws: null,
    wsRetryTimer: null,
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
            if (resStats.ok) this.stats = await resStats.json();
            if (resSessions.ok) this.sessions = await resSessions.json();
            if (resEsc.ok) this.escalations = await resEsc.json();
            if (resOrders.ok) this.orders = await resOrders.json();

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
            if (result.status === 'success') this.knowledgeBase = result.data;
        } catch (e) { console.error(e); }
    },

    async viewChat(userId, scroll = true) {
        this.selectedUser = userId;
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
                console.warn('⚠️ WebSocket 断开，5s 后重试...');
                this.wsRetryTimer = setTimeout(() => this._connectWS(wsUrl), 5000);
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
});
