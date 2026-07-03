<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  ArrowRight, Search, Bot, FileText, Users,
  ShieldCheck, FileSearch, Zap, GraduationCap, Landmark, Factory,
  ChevronRight, Star, Sparkles,
} from 'lucide-vue-next'
import LoginModal from '@/components/LoginModal.vue'

const router = useRouter()
const authStore = useAuthStore()
const showLoginModal = ref(false)

function navigateToApp() {
  if (authStore.isAuthenticated) {
    router.push(authStore.homePath)
  } else {
    showLoginModal.value = true
  }
}

function scrollToSection(id: string) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// ── Scroll reveal ──
onMounted(() => {
  const obs = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible')
          obs.unobserve(entry.target)
        }
      })
    },
    { threshold: 0.12 }
  )
  document.querySelectorAll('.scroll-reveal').forEach((el) => obs.observe(el))
})

// ── Features ──
const features = [
  { icon: FileText, title: '文档知识管理', desc: '多格式文档上传，自动切片、向量化、索引入库，断点续传与秒传。' },
  { icon: Search, title: '智能知识问答', desc: '混合检索驱动 LLM 生成可溯源回答，无法回答时主动拒答。' },
  { icon: Bot, title: 'AI Agent 助手', desc: '多轮对话 Agent，SSE 流式输出、工具编排与三级记忆管理。' },
  { icon: Users, title: '团队协作空间', desc: '创建知识库群组，邀请成员，审批申请，群组间数据完全隔离。' },
  { icon: FileSearch, title: '精准答案溯源', desc: '每条回答附带引用片段与相关度评分，让 AI 回答有据可查。' },
  { icon: ShieldCheck, title: '企业级安全', desc: 'JWT 双令牌认证，BCrypt 加密，三级权限体系，全链路保护。' },
]

const steps = [
  { num: '01', title: '创建群组，组建团队', desc: '一键创建知识库群组，生成邀请码，团队成员即可加入协作。' },
  { num: '02', title: '上传文档，自动入库', desc: '拖拽上传文档，系统自动解析、切片、向量化并建立全文索引。' },
  { num: '03', title: '提问检索，获取答案', desc: '群组内自然语言提问，混合检索 + RRF 融合，LLM 生成可溯源回答。' },
  { num: '04', title: 'AI 助手，持续对话', desc: 'Agent 自主编排工具调用，流式输出，三级记忆管理长对话。' },
]

const cases = [
  { icon: Zap, title: '电力能源', desc: '巡检手册、安全规程、故障排除智能问答' },
  { icon: Landmark, title: '金融服务', desc: '合规检索、风控政策、产品知识库管理' },
  { icon: GraduationCap, title: '教育培训', desc: '课程知识库、学员自助答疑、教学辅助' },
  { icon: Factory, title: '智能制造', desc: '技术文档、设备 SOP、供应商资料管理' },
]
</script>

<template>
  <div class="landing">
    <LoginModal v-model:visible="showLoginModal" />

    <!-- ════════════ Navbar ════════════ -->
    <header class="navbar">
      <div class="nav-inner">
        <div class="nav-left">
          <a class="nav-brand" @click.prevent="scrollToTop">
            <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
              <defs>
                <linearGradient id="lg" x1="2" y1="2" x2="30" y2="30">
                  <stop offset="0" stop-color="#1d4ed8" />
                  <stop offset="1" stop-color="#0284c7" />
                </linearGradient>
              </defs>
              <circle cx="16" cy="16" r="14" fill="none" stroke="url(#lg)" stroke-width="1.8" />
              <circle cx="16" cy="15" r="4" fill="url(#lg)" opacity="0.9" />
              <circle cx="16" cy="14" r="1.8" fill="#fff" opacity="0.9" />
            </svg>
            <span class="nav-brand__text">KnowOcean</span>
          </a>
          <nav class="nav-links">
            <a @click.prevent="scrollToSection('features')">功能</a>
            <a @click.prevent="scrollToSection('workflow')">流程</a>
            <a @click.prevent="scrollToSection('cases')">场景</a>
          </nav>
        </div>
        <div class="nav-right">
          <button class="nav-btn-ghost" @click="navigateToApp()">登录</button>
          <button class="nav-btn-primary" @click="navigateToApp()">
            进入平台
            <ChevronRight :size="16" />
          </button>
        </div>
      </div>
    </header>

    <!-- ════════════ Hero ════════════ -->
    <section class="hero">
      <div class="hero-content">
        <div class="hero-badge">
          <Sparkles :size="14" />
          RAG + Agent · 企业级智能知识平台
        </div>
        <h1 class="hero-title">
          让每一次提问<br />
          <span class="text-brand">都有据可查</span>
        </h1>
        <p class="hero-desc">
          基于检索增强生成与 AI Agent 技术，将企业私有知识库与大语言模型深度融合，
          实现精准溯源、自主编排的可信智能知识服务。
        </p>
        <div class="hero-actions">
          <button class="hero-btn-primary" @click="navigateToApp()">
            开始使用
            <ArrowRight :size="18" />
          </button>
          <button class="hero-btn-outline" @click="scrollToSection('features')">
            了解更多
          </button>
        </div>
      </div>

      <!-- Key metrics -->
      <div class="hero-metrics">
        <div class="metric-item">
          <span class="metric-value">98<em>%</em></span>
          <span class="metric-label">检索准确率</span>
        </div>
        <div class="metric-divider" />
        <div class="metric-item">
          <span class="metric-value">&lt;200<em>ms</em></span>
          <span class="metric-label">平均响应</span>
        </div>
        <div class="metric-divider" />
        <div class="metric-item">
          <span class="metric-value">20<em>+</em></span>
          <span class="metric-label">文件格式</span>
        </div>
      </div>
    </section>

    <!-- ════════════ Features ════════════ -->
    <section id="features" class="section features">
      <div class="container">
        <div class="section-header scroll-reveal">
          <span class="section-tag">Core Capabilities</span>
          <h2 class="section-title">覆盖知识管理 <i>全链路</i></h2>
          <p class="section-desc">从文档入库到 AI 对话，一站式构建企业智能知识服务体系</p>
        </div>
        <div class="features-grid">
          <div
            v-for="(feat, i) in features"
            :key="i"
            class="feature-card scroll-reveal"
            :style="{ transitionDelay: `${i * 0.06}s` }"
          >
            <div class="feature-icon-wrap">
              <component :is="feat.icon" :size="20" />
            </div>
            <h3>{{ feat.title }}</h3>
            <p>{{ feat.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ════════════ Workflow ════════════ -->
    <section id="workflow" class="section workflow">
      <div class="container-narrow">
        <div class="section-header scroll-reveal">
          <span class="section-tag">Workflow</span>
          <h2 class="section-title">四步开启智能 <i>知识服务</i></h2>
          <p class="section-desc">从零到一，快速构建企业级 RAG 应用</p>
        </div>
        <div class="steps-list scroll-reveal">
          <div v-for="(step, i) in steps" :key="i" class="step-row">
            <div class="step-num">{{ step.num }}</div>
            <div v-if="i < steps.length" class="step-line" />
            <div class="step-card">
              <h3>{{ step.title }}</h3>
              <p>{{ step.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ════════════ Cases ════════════ -->
    <section id="cases" class="section cases">
      <div class="container">
        <div class="section-header scroll-reveal">
          <span class="section-tag">Use Cases</span>
          <h2 class="section-title">赋能 <i>各行各业</i></h2>
          <p class="section-desc">灵活适配不同业务场景，释放企业知识资产价值</p>
        </div>
        <div class="cases-grid scroll-reveal">
          <div v-for="(cs, i) in cases" :key="i" class="case-card">
            <div class="case-icon-wrap">
              <component :is="cs.icon" :size="22" />
            </div>
            <h3>{{ cs.title }}</h3>
            <p>{{ cs.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ════════════ CTA ════════════ -->
    <section class="section cta">
      <div class="container">
        <div class="cta-card scroll-reveal">
          <div class="cta-star">
            <Star :size="20" />
          </div>
          <h2>准备好构建您的<br />智能知识平台了吗？</h2>
          <p>立即体验企业级 RAG + Agent 解决方案，让每一次提问都有据可查。</p>
          <div class="cta-buttons">
            <button class="btn btn--primary btn--lg" @click="navigateToApp()">免费试用</button>
            <button class="btn btn--outline btn--lg" @click="navigateToApp()">查看演示</button>
          </div>
        </div>
      </div>
    </section>

    <!-- ════════════ Footer ════════════ -->
    <footer class="footer">
      <div class="container">
        <div class="footer-grid">
          <div class="footer-brand">
            <div class="footer-logo">
              <svg width="24" height="24" viewBox="0 0 32 32" fill="none">
                <circle cx="16" cy="16" r="14" fill="none" stroke="url(#lg)" stroke-width="1.8" />
                <circle cx="16" cy="15" r="4" fill="url(#lg)" opacity="0.9" />
              </svg>
              KnowOcean
            </div>
            <p>企业级智能知识管理平台<br />融合 RAG 与 AI Agent 技术</p>
          </div>
          <div class="footer-col">
            <h4>产品</h4>
            <a @click.prevent="scrollToSection('features')">核心功能</a>
            <a @click.prevent="scrollToSection('workflow')">工作流程</a>
            <a @click.prevent="scrollToSection('cases')">应用场景</a>
          </div>
          <div class="footer-col">
            <h4>关于</h4>
            <a href="#">项目文档</a>
            <a href="#">架构设计</a>
            <a href="#">更新日志</a>
          </div>
          <div class="footer-col">
            <h4>联系</h4>
            <a href="#">GitHub</a>
            <a href="#">技术支持</a>
            <a href="#">反馈建议</a>
          </div>
        </div>
        <div class="footer-bottom">
          <span>© 2026 KnowOcean Platform. All rights reserved.</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* ════════════ Layout ════════════ */
.landing {
  position: relative;
  background: var(--surface-root);
  color: var(--text-primary);
  overflow-x: hidden;
  min-height: 100vh;
}

/* ════════════ Navbar ════════════ */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 16px 24px;
}

.nav-inner {
  max-width: 1280px;
  margin: 0 auto;
  border-radius: var(--radius-full);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 40px;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  text-decoration: none;
}

.nav-brand__text {
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 17px;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.nav-links { display: flex; gap: 32px; }

.nav-links a {
  font-size: 0.86rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: color 0.2s;
  text-decoration: none;
}

.nav-links a:hover { color: var(--brand-primary); }

.nav-right { display: flex; align-items: center; gap: 8px; }

.nav-btn-ghost {
  padding: 8px 18px;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.84rem;
  font-weight: 600;
  font-family: 'Manrope', system-ui, sans-serif;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn-ghost:hover {
  background: var(--surface-muted);
  color: var(--text-primary);
}

.nav-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 20px;
  border-radius: var(--radius-full);
  background: var(--brand-primary);
  color: #fff;
  font-size: 0.84rem;
  font-weight: 700;
  font-family: 'Manrope', system-ui, sans-serif;
  cursor: pointer;
  transition: all var(--ease-out);
  box-shadow: 0 2px 8px rgba(29, 78, 216, 0.2);
}

.nav-btn-primary:hover {
  background: var(--brand-primary-dark);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(29, 78, 216, 0.3);
}

/* ════════════ Hero ════════════ */
.hero {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 140px 24px 60px;
  text-align: center;
}

.hero-content {
  max-width: 720px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border-radius: var(--radius-full);
  background: var(--surface-accent);
  color: var(--brand-primary);
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  margin-bottom: 32px;
}

.hero-title {
  font-size: clamp(44px, 7vw, 80px);
  font-weight: 800;
  line-height: 1.06;
  letter-spacing: -0.03em;
  color: var(--text-primary);
  margin-bottom: 22px;
}

.hero-desc {
  max-width: 540px;
  font-size: 1.05rem;
  line-height: 1.7;
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.hero-actions {
  display: flex;
  gap: 14px;
  align-items: center;
}

.hero-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 30px;
  border-radius: var(--radius-full);
  background: var(--brand-primary);
  color: #fff;
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  transition: all var(--ease-out);
  box-shadow: 0 4px 16px rgba(29, 78, 216, 0.25);
}

.hero-btn-primary:hover {
  background: var(--brand-primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(29, 78, 216, 0.35);
}

.hero-btn-outline {
  padding: 14px 30px;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--text-secondary);
  border: 1.5px solid var(--border-default);
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  transition: all var(--ease-out);
}

.hero-btn-outline:hover {
  border-color: var(--brand-primary);
  color: var(--brand-primary);
  background: var(--surface-accent);
}

/* Metrics */
.hero-metrics {
  display: flex;
  align-items: center;
  gap: 48px;
  margin-top: 72px;
}

.metric-item { text-align: center; }

.metric-value {
  display: block;
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 2.2rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1;
  margin-bottom: 4px;
}

.metric-value em {
  font-style: normal;
  font-size: 1rem;
  font-weight: 600;
  color: var(--brand-primary);
  margin-left: 2px;
}

.metric-label {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--text-muted);
  letter-spacing: 0.03em;
}

.metric-divider {
  width: 1px;
  height: 40px;
  background: var(--border-default);
}

/* ════════════ Shared Section Styles ════════════ */
.section { position: relative; z-index: 1; padding: 120px 0; }

.section-header {
  text-align: center;
  margin-bottom: 64px;
}

.section-tag {
  display: inline-block;
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--brand-primary);
  background: var(--surface-accent);
  padding: 4px 14px;
  border-radius: var(--radius-full);
  margin-bottom: 18px;
}

.section-title {
  font-size: clamp(28px, 4vw, 44px);
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  margin-bottom: 14px;
}

.section-title i {
  font-family: 'Source Serif 4', Georgia, serif;
  font-style: italic;
  font-weight: 400;
  color: var(--text-muted);
}

.section-desc {
  font-size: 0.95rem;
  color: var(--text-muted);
  max-width: 400px;
  margin: 0 auto;
}

.section-header { margin-bottom: 64px; }

/* ════════════ Features ════════════ */
.features { background: transparent; }

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.feature-card {
  padding: 36px 32px;
  border-radius: var(--radius-lg);
  background: var(--surface-white);
  border: 1px solid var(--border-default);
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  cursor: default;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-accent);
}

.feature-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--surface-accent);
  color: var(--brand-primary);
  margin-bottom: 20px;
  transition: all 0.3s;
}

.feature-card:hover .feature-icon-wrap {
  background: var(--brand-primary);
  color: #fff;
}

.feature-card h3 {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.feature-card p {
  font-size: 0.88rem;
  color: var(--text-muted);
  line-height: 1.6;
  margin: 0;
}

/* ════════════ Workflow ════════════ */
.workflow { background: var(--surface-subtle); }

.steps-list {
  display: flex;
  flex-direction: column;
}

.step-row {
  display: flex;
  align-items: stretch;
}

.step-num {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: var(--brand-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 18px;
  font-weight: 800;
  margin-right: 24px;
  box-shadow: 0 4px 12px rgba(29, 78, 216, 0.2);
}

.step-line {
  flex-shrink: 0;
  width: 2px;
  border-radius: 1px;
  background: linear-gradient(to bottom, var(--brand-primary), var(--brand-accent-light));
  opacity: 0.15;
  margin: 4px 24px 4px 0;
}

.step-card {
  flex: 1;
  padding: 28px 32px;
  margin-bottom: 20px;
  background: var(--surface-white);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

.step-card:last-child { margin-bottom: 0; }

.step-card h3 {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.step-card p {
  font-size: 0.88rem;
  color: var(--text-muted);
  line-height: 1.6;
  margin: 0;
}

/* ════════════ Cases ════════════ */
.cases-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.case-card {
  text-align: center;
  padding: 40px 24px;
  border-radius: var(--radius-lg);
  background: var(--surface-white);
  border: 1px solid var(--border-default);
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  cursor: default;
}

.case-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--border-accent);
}

.case-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: var(--surface-accent);
  color: var(--brand-primary);
  margin: 0 auto 16px;
  transition: all 0.3s;
}

.case-card:hover .case-icon-wrap {
  background: var(--brand-primary);
  color: #fff;
}

.case-card h3 {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.case-card p {
  font-size: 0.82rem;
  color: var(--text-muted);
  line-height: 1.6;
  margin: 0;
}

/* ════════════ CTA ════════════ */
.cta { padding: 100px 0; }

.cta-card {
  padding: 72px 56px;
  text-align: center;
  position: relative;
  overflow: hidden;
  max-width: 900px;
  margin: 0 auto;
}

.cta-star {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: var(--surface-accent);
  color: var(--brand-primary);
  margin: 0 auto 24px;
}

.cta-card h2 {
  font-size: clamp(24px, 3.5vw, 40px);
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.cta-card p {
  font-size: 1rem;
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.cta-buttons {
  display: flex;
  justify-content: center;
  gap: 14px;
}

/* ════════════ Footer ════════════ */
.footer {
  position: relative;
  z-index: 1;
  padding: 80px 0 32px;
  border-top: 1px solid var(--border-default);
  background: var(--surface-white);
}

.footer-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 48px;
  margin-bottom: 40px;
}

.footer-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 16px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.footer-brand p {
  font-size: 0.86rem;
  color: var(--text-muted);
  line-height: 1.7;
  margin: 0;
}

.footer-col h4 {
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 18px;
}

.footer-col a {
  display: block;
  font-size: 0.86rem;
  color: var(--text-secondary);
  padding: 4px 0;
  cursor: pointer;
  transition: color 0.2s;
}

.footer-col a:hover { color: var(--brand-primary); }

.footer-bottom {
  padding-top: 24px;
  border-top: 1px solid var(--border-subtle);
  text-align: center;
}

.footer-bottom span {
  font-size: 0.78rem;
  color: var(--text-muted);
}

/* ──── Utility ──── */
.text-brand {
  font-family: 'Manrope', system-ui, sans-serif;
  font-weight: 700;
  color: var(--brand-primary);
}

/* ════════════ Responsive ════════════ */
@media (width <= 1024px) {
  .features-grid { grid-template-columns: repeat(2, 1fr); }
  .cases-grid { grid-template-columns: repeat(2, 1fr); }
  .footer-grid { grid-template-columns: 1fr 1fr; }
}

@media (width <= 768px) {
  .nav-links { display: none; }
  .hero { padding: 120px 20px 50px; }
  .hero-title { font-size: 36px; }
  .hero-metrics { gap: 28px; }
  .metric-value { font-size: 1.6rem; }
  .features-grid { grid-template-columns: 1fr; }
  .cases-grid { grid-template-columns: 1fr 1fr; }
  .cta-card { padding: 48px 24px; }
  .cta-buttons { flex-direction: column; align-items: center; }
  .footer-grid { grid-template-columns: 1fr; gap: 32px; }
  .hero-actions { flex-direction: column; }
}

@media (width <= 480px) {
  .cases-grid { grid-template-columns: 1fr; }
  .hero-title { font-size: 28px; }
}
</style>
