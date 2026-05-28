<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import {
  ArrowRight,
  Search,
  Bot,
  FileText,
  Users,
  ShieldCheck,
  FileSearch,
  Zap,
  GraduationCap,
  Landmark,
  Factory,
} from "lucide-vue-next";
import LoginModal from "@/components/LoginModal.vue";

const router = useRouter();
const authStore = useAuthStore();
const showLoginModal = ref(false);

function navigateToApp() {
  if (authStore.isAuthenticated) {
    router.push(authStore.homePath);
  } else {
    showLoginModal.value = true;
  }
}

// ── Hero video fade logic ──
const heroVideoRef = ref<HTMLVideoElement | null>(null);
const heroOpacity = ref(0);
let heroRaf = 0;
let heroTarget = 1;

function animateHeroOpacity() {
  const video = heroVideoRef.value;
  if (!video) return;
  const current = heroOpacity.value;
  const step = 0.08;
  if (Math.abs(current - heroTarget) < step) {
    heroOpacity.value = heroTarget;
  } else {
    heroOpacity.value = current + (heroTarget > current ? step : -step);
    heroRaf = requestAnimationFrame(animateHeroOpacity);
  }
}

function fadeHeroTo(target: number) {
  heroTarget = target;
  cancelAnimationFrame(heroRaf);
  heroRaf = requestAnimationFrame(animateHeroOpacity);
}

function onHeroCanPlay() {
  const video = heroVideoRef.value;
  if (!video) return;
  video.play();
  fadeHeroTo(1);
}

function onHeroEnded() {
  const video = heroVideoRef.value;
  if (!video) return;
  video.currentTime = 0;
  video.play();
}

// ── Nav smooth scroll ──
function scrollToSection(id: string) {
  const el = document.getElementById(id);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

onBeforeUnmount(() => {
  cancelAnimationFrame(heroRaf);
});

// ── Scroll reveal ──
onMounted(() => {
  const reveals = document.querySelectorAll(".scroll-reveal");
  const obs = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );
  reveals.forEach((el) => obs.observe(el));
});

// ── Features ──
const features = [
  {
    icon: FileText,
    title: "文档知识管理",
    desc: "上传多种格式文档，自动切片、向量化、索引入库，支持断点续传与秒传。",
  },
  {
    icon: Search,
    title: "知识库问答",
    desc: "群组内提问，混合检索驱动 LLM 生成可溯源回答，无法回答时主动拒答。",
  },
  {
    icon: Bot,
    title: "AI 智能助手",
    desc: "多轮对话 Agent，支持 SSE 流式输出、工具编排与短期记忆管理。",
  },
  {
    icon: Users,
    title: "团队协作",
    desc: "创建知识库群组，邀请成员，审批申请，群组间数据完全隔离。",
  },
  {
    icon: FileSearch,
    title: "答案溯源",
    desc: "每条回答附带引用片段与相关度评分，让 AI 回答有据可查。",
  },
  {
    icon: ShieldCheck,
    title: "安全保障",
    desc: "JWT 双令牌认证，BCrypt 加密，三级权限体系，全链路数据保护。",
  },
];

// ── Steps ──
const steps = [
  {
    num: "01",
    title: "创建群组，组建团队",
    desc: "一键创建知识库群组，生成邀请码，团队成员即可加入协作。",
  },
  {
    num: "02",
    title: "上传文档，自动入库",
    desc: "拖拽上传文档，系统自动解析、切片、向量化并建立全文索引。",
  },
  {
    num: "03",
    title: "提问检索，获取答案",
    desc: "群组内自然语言提问，混合检索 + RRF 融合，LLM 生成可溯源回答。",
  },
  {
    num: "04",
    title: "AI 助手，持续对话",
    desc: "Agent 自主编排工具调用，流式输出，三级记忆管理长对话。",
  },
];

// ── Cases ──
const cases = [
  { icon: Zap, title: "电力", desc: "巡检手册、安全规程、故障排除问答" },
  { icon: Landmark, title: "金融", desc: "合规检索、风控政策、产品知识库" },
  { icon: GraduationCap, title: "教育", desc: "课程知识库、学员自助答疑、教学辅助" },
  { icon: Factory, title: "制造", desc: "技术文档、设备 SOP、供应商资料管理" },
];
</script>

<template>
  <div class="landing">
    <LoginModal v-model:visible="showLoginModal" />

    <!-- ════════════ Fixed video background ════════════ -->
    <video
      ref="heroVideoRef"
      class="landing-video"
      muted
      autoplay
      loop
      playsinline
      preload="auto"
      :style="{ opacity: heroOpacity }"
      @canplay="onHeroCanPlay"
      @ended="onHeroEnded"
    >
      <source src="/videos/ocean.mp4" type="video/mp4" />
    </video>
    <div class="landing-video-overlay" />

    <!-- ════════════ Navbar ════════════ -->
    <header class="navbar">
      <div class="nav-pill liquid-glass">
        <div class="nav-left">
          <div class="nav-brand">
            <a @click.prevent="scrollToTop()" title="回到顶部">
              <svg width="24" height="24" viewBox="0 0 32 32" fill="none">
                <defs>
                  <linearGradient id="ko" x1="0" y1="0" x2="32" y2="32">
                    <stop offset="0" stop-color="#0A2F5C" />
                    <stop offset=".5" stop-color="#1565C0" />
                    <stop offset="1" stop-color="#06B6D4" />
                  </linearGradient>
                  <radialGradient id="kc" cx="16" cy="15" r="4">
                    <stop offset="0" stop-color="#E0F2FE" />
                    <stop offset="1" stop-color="#38BDF8" />
                  </radialGradient>
                </defs>
                <circle
                  cx="16"
                  cy="16"
                  r="14.5"
                  fill="none"
                  stroke="url(#ko)"
                  stroke-width="1.2"
                />
                <g fill="#38BDF8">
                  <circle cx="16" cy="2.8" r="1.1" />
                  <circle cx="26.2" cy="7" r="1" />
                  <circle cx="29.2" cy="16" r="1.1" />
                  <circle cx="26.2" cy="25" r="1" />
                  <circle cx="16" cy="29.2" r="1.1" />
                  <circle cx="5.8" cy="25" r="1" />
                  <circle cx="2.8" cy="16" r="1.1" />
                  <circle cx="5.8" cy="7" r="1" />
                </g>
                <path
                  d="M7 18Q12 13 16 16T25 14"
                  fill="none"
                  stroke="#38BDF8"
                  stroke-width="1.1"
                  stroke-linecap="round"
                  opacity=".65"
                />
                <path
                  d="M5.5 21Q12 15 16 19T26.5 17"
                  fill="none"
                  stroke="#38BDF8"
                  stroke-width="1.1"
                  stroke-linecap="round"
                  opacity=".4"
                />
                <path
                  d="M8.5 15Q12 11.5 16 14T23.5 12.5"
                  fill="none"
                  stroke="#38BDF8"
                  stroke-width="1.1"
                  stroke-linecap="round"
                  opacity=".85"
                />
                <circle cx="16" cy="15" r="3.5" fill="url(#kc)" />
                <circle cx="16" cy="15" r="1.8" fill="#FFFFFF" opacity=".9" />
              </svg>
            </a>
            <a class="logo" @click.prevent="scrollToTop()" title="回到顶部">
              知识海洋平台
            </a>
          </div>
          <nav class="nav-links">
            <a @click.prevent="scrollToSection('features')">核心功能</a>
            <a @click.prevent="scrollToSection('workflow')">工作流程</a>
            <a @click.prevent="scrollToSection('cases')">应用场景</a>
          </nav>
        </div>
        <div class="nav-right">
          <button class="nav-link-btn" @click="navigateToApp()">登录</button>
          <button class="nav-cta-btn liquid-glass" @click="navigateToApp()">
            进入平台
          </button>
        </div>
      </div>
    </header>

    <!-- ════════════ Hero ════════════ -->
    <section class="hero">
      <div class="hero-content">
        <div class="hero-badge liquid-glass">
          <span class="badge-dot" />
          RAG + Agent · 企业级智能知识平台
        </div>
        <h1 class="hero-title">
          让每一次提问<br />
          <em class="hero-em">都有据可查</em>
        </h1>
        <p class="hero-desc">
          基于检索增强生成与 AI Agent 技术，将企业私有知识库与大语言模型深度融合，
          实现精准溯源、自主编排的可信智能知识服务。
        </p>
        <!-- Email input -->
        <div class="hero-input-wrap liquid-glass">
          <input
            type="text"
            readonly
            class="hero-input"
            placeholder="知识海洋 · 企业级 RAG 知识平台"
          />
          <button class="hero-submit-btn" @click="navigateToApp()">
            <ArrowRight :size="20" />
          </button>
        </div>
        <!-- CTA buttons -->
        <div class="hero-actions">
          <button class="hero-btn primary-btn" @click="navigateToApp()">开始使用</button>
          <button class="hero-btn outline-btn liquid-glass" @click="navigateToApp()">
            进入工作台
          </button>
        </div>
      </div>

      <!-- Metrics -->
      <div class="hero-footer">
        <div class="hero-metrics">
          <div class="metric">
            <span class="metric-value">98<span class="metric-unit">%</span></span>
            <span class="metric-label">检索准确率</span>
          </div>
          <div class="metric-divider" />
          <div class="metric">
            <span class="metric-value">&lt;200<span class="metric-unit">ms</span></span>
            <span class="metric-label">平均响应</span>
          </div>
          <div class="metric-divider" />
          <div class="metric">
            <span class="metric-value">20<span class="metric-unit">+</span></span>
            <span class="metric-label">文件格式支持</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ════════════ Features ════════════ -->
    <section id="features" class="features">
      <div class="section-container">
        <div class="section-header scroll-reveal">
          <span class="section-tag">Core Features</span>
          <h2 class="section-title">
            覆盖知识管理<span
              class="font-serif italic"
              style="color: rgba(255, 255, 255, 0.4)"
              >全链路</span
            >
          </h2>
          <p class="section-desc">从文档入库到 AI 对话，一站式构建企业智能知识服务体系</p>
        </div>

        <div class="features-grid">
          <div
            v-for="(feat, i) in features"
            :key="i"
            class="feature-card liquid-glass scroll-reveal"
            :style="{ transitionDelay: `${i * 0.08}s` }"
          >
            <div class="feature-icon">
              <component :is="feat.icon" :size="22" />
            </div>
            <h3>{{ feat.title }}</h3>
            <p>{{ feat.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ════════════ Workflow ════════════ -->
    <section id="workflow" class="workflow">
      <div class="section-container-narrow">
        <div class="section-header scroll-reveal">
          <span class="section-tag">Workflow</span>
          <h2 class="section-title">
            四步开启智能<span
              class="font-serif italic"
              style="color: rgba(255, 255, 255, 0.4)"
              >知识服务</span
            >
          </h2>
          <p class="section-desc">从零到一，快速构建企业级 RAG 应用</p>
        </div>

        <div class="steps-list scroll-reveal">
          <div v-for="(step, i) in steps" :key="i" class="step-row">
            <div class="step-num">{{ step.num }}</div>
            <div v-if="i < steps.length" class="step-divider-v" />
            <div
              class="step-card liquid-glass"
              style="margin-bottom: 0"
              :class="{ 'step-card-last': i === steps.length - 1 }"
            >
              <h3>{{ step.title }}</h3>
              <p>{{ step.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ════════════ Cases ════════════ -->
    <section id="cases" class="cases">
      <div class="section-container">
        <div class="section-header scroll-reveal">
          <span class="section-tag">Use Cases</span>
          <h2 class="section-title">
            赋能<span class="font-serif italic" style="color: rgba(255, 255, 255, 0.4)"
              >各行各业</span
            >
          </h2>
          <p class="section-desc">灵活适配不同业务场景，释放企业知识资产价值</p>
        </div>

        <div class="cases-grid scroll-reveal">
          <div v-for="(cs, i) in cases" :key="i" class="case-card liquid-glass">
            <div class="case-icon">
              <component :is="cs.icon" :size="24" />
            </div>
            <h3>{{ cs.title }}</h3>
            <p>{{ cs.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ════════════ CTA ════════════ -->
    <section class="cta">
      <div class="section-container-wide">
        <div class="cta-card liquid-glass scroll-reveal">
          <h2>准备好构建您的<br />智能知识平台了吗？</h2>
          <p>立即体验企业级 RAG + Agent 解决方案，让每一次提问都有据可查。</p>
          <div class="cta-buttons">
            <button class="cta-btn-primary" @click="navigateToApp()">免费试用</button>
            <button class="cta-btn-outline liquid-glass" @click="navigateToApp()">
              查看演示
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- ════════════ Footer ════════════ -->
    <footer class="footer">
      <div class="section-container">
        <div class="footer-grid">
          <!-- Brand -->
          <div class="footer-brand">
            <div class="footer-logo-row">
              <svg width="24" height="24" viewBox="0 0 32 32" fill="none">
                <circle
                  cx="16"
                  cy="16"
                  r="14.5"
                  fill="none"
                  stroke="url(#kof)"
                  stroke-width="1.2"
                />
                <defs>
                  <linearGradient id="kof" x1="0" y1="0" x2="32" y2="32">
                    <stop offset="0" stop-color="#0A2F5C" />
                    <stop offset=".5" stop-color="#1565C0" />
                    <stop offset="1" stop-color="#06B6D4" />
                  </linearGradient>
                </defs>
                <g fill="#38BDF8">
                  <circle cx="16" cy="2.8" r="1.1" />
                  <circle cx="26.2" cy="7" r="1" />
                  <circle cx="29.2" cy="16" r="1.1" />
                  <circle cx="26.2" cy="25" r="1" />
                  <circle cx="16" cy="29.2" r="1.1" />
                  <circle cx="5.8" cy="25" r="1" />
                  <circle cx="2.8" cy="16" r="1.1" />
                  <circle cx="5.8" cy="7" r="1" />
                </g>
                <path
                  d="M7 18Q12 13 16 16T25 14"
                  fill="none"
                  stroke="#38BDF8"
                  stroke-width="1.1"
                  stroke-linecap="round"
                  opacity=".65"
                />
                <circle cx="16" cy="15" r="2" fill="#38BDF8" opacity=".5" />
                <circle cx="16" cy="15" r="1.2" fill="#E0F2FE" opacity=".8" />
              </svg>
              KnowOcean
            </div>
            <p>企业级智能知识管理平台<br />融合 RAG 与 AI Agent 技术</p>
          </div>
          <!-- Links -->
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
        <!-- 最底部网站授权信息 -->
        <div class="footer-bottom">
          <div class="footer-row">
            <a
              class="footer-link"
              title="master"
              target="_blank"
              href="#"
              rel="noreferrer"
            >
              <span>
                <svg
                  viewBox="64 64 896 896"
                  focusable="false"
                  data-icon="user"
                  width="1em"
                  height="1em"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path
                    d="M858.5 763.6a374 374 0 00-80.6-119.5 375.63 375.63 0 00-119.5-80.6c-.4-.2-.8-.3-1.2-.5C719.5 518 760 444.7 760 362c0-137-111-248-248-248S264 225 264 362c0 82.7 40.5 156 102.8 201.1-.4.2-.8.3-1.2.5-44.8 18.9-85 46-119.5 80.6a375.63 375.63 0 00-80.6 119.5A371.7 371.7 0 00136 901.8a8 8 0 008 8.2h60c4.4 0 7.9-3.5 8-7.8 2-77.2 33-149.5 87.8-204.3 56.7-56.7 132-87.9 212.2-87.9s155.5 31.2 212.2 87.9C779 752.7 810 825 812 902.2c.1 4.4 3.6 7.8 8 7.8h60a8 8 0 008-8.2c-1-47.8-10.9-94.3-29.5-138.2zM512 534c-45.9 0-89.1-17.9-121.6-50.4S340 407.9 340 362c0-45.9 17.9-89.1 50.4-121.6S466.1 190 512 190s89.1 17.9 121.6 50.4S684 316.1 684 362c0 45.9-17.9 89.1-50.4 121.6S557.9 534 512 534z"
                  ></path></svg
              ></span>
              站长：程序员阿哲</a
            >
          </div>
          <div class="footer-row">
            <span class="footer-copyright">
              <svg
                viewBox="64 64 896 896"
                focusable="false"
                data-icon="copyright"
                width="1em"
                height="1em"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372zm5.6-532.7c53 0 89 33.8 93 83.4.3 4.2 3.8 7.4 8 7.4h56.7c2.6 0 4.7-2.1 4.7-4.7 0-86.7-68.4-147.4-162.7-147.4C407.4 290 344 364.2 344 486.8v52.3C344 660.8 407.4 734 517.3 734c94 0 162.7-58.8 162.7-141.4 0-2.6-2.1-4.7-4.7-4.7h-56.8c-4.2 0-7.6 3.2-8 7.3-4.2 46.1-40.1 77.8-93 77.8-65.3 0-102.1-47.9-102.1-133.6v-52.6c.1-87 37-135.5 102.2-135.5z"
                ></path>
              </svg>
            </span>
            2026 知识海洋平台. All rights reserved.
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.logo {
  cursor: pointer;
}
/* ═══════════════════════════════════════
   Landing — full-page fixed video layout
   ═══════════════════════════════════════ */
.landing {
  position: relative;
  background: #000;
  color: #fff;
  overflow-x: hidden;
}

/* ── Fixed video background ── */
.landing-video {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  width: 100vw;
  height: 100vh;
  object-fit: cover;
  object-position: bottom;
}

.landing-video-overlay {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: radial-gradient(
    70% 60% at 50% 35%,
    rgba(255, 255, 255, 0.08) 0%,
    transparent 50%,
    rgba(0, 0, 0, 0.15) 100%
  );
}

/* ── Navbar ── */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  pointer-events: none;
  padding: 20px 24px;
}

.nav-pill {
  pointer-events: auto;
  border-radius: 9999px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1280px;
  margin: 0 auto;
  padding: 14px 28px;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 36px;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #fff;
  font-family: "Poppins", "Noto Sans SC", sans-serif;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.01em;
  white-space: nowrap;
}

.nav-links {
  display: flex;
  gap: 32px;
}

.nav-links a {
  color: rgba(255, 255, 255, 0.7);
  font-size: 13.5px;
  font-weight: 500;
  transition: color 0.2s;
  text-decoration: none;
  cursor: pointer;
}

.nav-links a:hover {
  color: #fff;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-link-btn {
  color: rgba(255, 255, 255, 0.8);
  background: transparent;
  border: none;
  border-radius: 9999px;
  padding: 8px 18px;
  font-size: 13.5px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}

.nav-link-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.05);
}

.nav-cta-btn {
  color: #fff;
  border: none;
  border-radius: 9999px;
  padding: 8px 20px;
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s;
  font-family: inherit;
}

.nav-cta-btn:hover {
  background: rgba(255, 255, 255, 0.06);
}

/* ── Hero ── */
.hero {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 120px 24px 40px;
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  max-width: 720px;
  transform: translateY(-5%);
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.7);
  border-radius: 9999px;
  padding: 6px 18px;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 32px;
  animation: fade-in-up 0.6s both;
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #38bdf8;
  animation: pulse-ring 2.5s ease-in-out infinite;
}

.hero-title {
  color: #fff;
  font-family: "Poppins", "Noto Sans SC", sans-serif;
  font-size: clamp(48px, 7vw, 88px);
  font-weight: 800;
  line-height: 1.08;
  letter-spacing: -0.03em;
  margin-bottom: 24px;
  animation: fade-in-up 0.6s 0.1s both;
}

.hero-em {
  font-family: "Instrument Serif", "Noto Serif SC", Georgia, serif;
  font-style: italic;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.55);
}

.hero-desc {
  color: rgba(255, 255, 255, 0.55);
  max-width: 520px;
  margin-bottom: 20px;
  font-size: 16px;
  line-height: 1.7;
  animation: fade-in-up 0.6s 0.15s both;
}

.hero-input-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  /* max-width: 480px; */
  max-width: 630px;
  height: 65px;
  padding: 4px 5px 4px 24px;
  border-radius: 9999px;
  margin-bottom: 16px;
  animation: fade-in-up 0.6s 0.2s both;
}

.hero-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #fff;
  font-size: 15px;
  font-family: inherit;
  cursor: pointer;
}

.hero-input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.hero-submit-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: #fff;
  color: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.25s;
}

.hero-submit-btn:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: scale(1.05);
}

.hero-actions {
  display: flex;
  gap: 14px;
  animation: fade-in-up 0.6s 0.3s both;
}

.hero-btn {
  border-radius: 9999px;
  padding: 14px 36px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  letter-spacing: 0.01em;
  transition: all 0.25s;
  font-family: inherit;
}

.primary-btn {
  background: #fff;
  color: #000;
}

.primary-btn:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
}

.outline-btn {
  color: #fff;
}

.outline-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  transform: translateY(-1px);
}

/* ── Hero footer / metrics ── */
.hero-footer {
  position: relative;
  z-index: 10;
  margin-top: auto;
  padding-bottom: 20px;
}

.hero-metrics {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 40px;
  animation: fade-in-up 0.6s 0.4s both;
}

.metric {
  text-align: center;
}

.metric-value {
  display: block;
  color: #fff;
  font-family: "Poppins", sans-serif;
  font-size: 28px;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 4px;
}

.metric-unit {
  color: rgba(255, 255, 255, 0.4);
  font-size: 16px;
}

.metric-label {
  color: rgba(255, 255, 255, 0.3);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.03em;
}

.metric-divider {
  width: 1px;
  height: 32px;
  background: rgba(255, 255, 255, 0.1);
}

/* ── Shared section styles ── */
.section-container {
  max-width: 1280px;
  margin-left: auto;
  margin-right: auto;
  padding-left: 24px;
  padding-right: 24px;
}

.section-container-narrow {
  max-width: 880px;
  margin-left: auto;
  margin-right: auto;
  padding-left: 24px;
  padding-right: 24px;
}

.section-container-wide {
  max-width: 1280px;
  margin-left: auto;
  margin-right: auto;
  padding-left: 24px;
  padding-right: 24px;
}

.section-header {
  text-align: center;
  margin-bottom: 72px;
}

.section-tag {
  display: inline-block;
  color: rgba(96, 165, 250, 0.9);
  background: rgba(59, 130, 246, 0.1);
  border-radius: 9999px;
  padding: 4px 14px;
  font-family: "Poppins", sans-serif;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  margin-bottom: 18px;
}

.section-title {
  color: #fff;
  font-family: "Poppins", "Noto Sans SC", sans-serif;
  font-size: clamp(28px, 4vw, 48px);
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: 14px;
}

.section-desc {
  color: rgba(255, 255, 255, 0.4);
  font-size: 15px;
  max-width: 440px;
  margin: 0 auto;
}

.font-serif {
  font-family: "Instrument Serif", "Noto Serif SC", Georgia, serif;
}

.italic {
  font-style: italic;
}

/* ── Features ── */
.features {
  position: relative;
  z-index: 1;
  scroll-margin-top: 100px;
  padding: 120px 0;
  background: linear-gradient(rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0.3));
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.feature-card {
  cursor: pointer;
  border-radius: 24px;
  padding: 48px 40px;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.feature-card:hover {
  background: rgba(255, 255, 255, 0.04);
  transform: translateY(-4px);
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.15);
}

.feature-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: rgba(59, 130, 246, 0.1);
  color: #60a5fa;
  margin-bottom: 22px;
  transition: all 0.3s;
}

.feature-card:hover .feature-icon {
  color: #93c5fd;
  background: rgba(59, 130, 246, 0.2);
}

.feature-card h3 {
  color: #fff;
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 8px;
}

.feature-card p {
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  line-height: 1.65;
  margin: 0;
}

/* ── Workflow ── */
.workflow {
  position: relative;
  z-index: 1;
  scroll-margin-top: 100px;
  padding: 120px 0;
  background: rgba(0, 0, 0, 0.3);
}

.steps-list {
  display: flex;
  flex-direction: column;
}

.step-row {
  display: flex;
  align-items: stretch;
  gap: 0;
}

.step-num {
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: rgba(59, 130, 246, 0.1);
  color: #60a5fa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: "Poppins", sans-serif;
  font-size: 20px;
  font-weight: 800;
  margin-right: 20px;
}

.step-divider-v {
  flex-shrink: 0;
  width: 2px;
  border-radius: 1px;
  background: linear-gradient(#60a5fa, #06b6d4);
  opacity: 0.25;
  margin: 4px 20px 4px 0;
  align-self: stretch;
}

.step-card {
  flex: 1;
  border-radius: 20px;
  padding: 32px 40px 48px;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  margin-bottom: 24px;
}

.step-card-last {
  margin-bottom: 0;
}

.step-card h3 {
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 6px;
}

.step-card p {
  color: rgba(255, 255, 255, 0.45);
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
}

/* ── Cases ── */
.cases {
  position: relative;
  z-index: 1;
  scroll-margin-top: 100px;
  padding: 120px 0;
  background: rgba(0, 0, 0, 0.3);
}

.cases-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.case-card {
  text-align: center;
  cursor: pointer;
  border-radius: 24px;
  padding: 48px 32px;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.case-card:hover {
  background: rgba(255, 255, 255, 0.04);
  transform: translateY(-4px);
}

.case-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: rgba(59, 130, 246, 0.1);
  color: #60a5fa;
  margin: 0 auto 16px;
  transition: all 0.3s;
}

.case-card:hover .case-icon {
  color: #93c5fd;
  background: rgba(59, 130, 246, 0.2);
}

.case-card h3 {
  color: #fff;
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 6px;
}

.case-card p {
  color: rgba(255, 255, 255, 0.35);
  font-size: 13px;
  line-height: 1.6;
  margin: 0;
}

/* ── CTA ── */
.cta {
  position: relative;
  z-index: 1;
  padding: 100px 0;
  background: rgba(0, 0, 0, 0.3);
}

.cta-card {
  text-align: center;
  border-radius: 40px;
  padding: 100px 56px;
  position: relative;
  overflow: hidden;
  max-width: 1280px;
  width: calc(100% - 48px);
  height: 410px;
  margin-left: auto;
  margin-right: auto;
}

.cta-card h2 {
  position: relative;
  z-index: 1;
  color: #fff;
  font-family: "Instrument Serif", "Noto Serif SC", Georgia, serif;
  font-size: clamp(28px, 4vw, 48px);
  font-weight: 400;
  letter-spacing: -0.02em;
  margin-bottom: 18px;
}

.cta-card p {
  position: relative;
  z-index: 1;
  color: rgba(255, 255, 255, 0.5);
  font-size: 15px;
  margin-bottom: 40px;
}

.cta-buttons {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: center;
  gap: 14px;
}

.cta-btn-primary {
  background: #fff;
  color: #000;
  border: none;
  border-radius: 9999px;
  padding: 14px 36px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.25s;
}

.cta-btn-primary:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.cta-btn-outline {
  color: #fff;
  border: none;
  border-radius: 9999px;
  padding: 14px 36px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.25s;
}

.cta-btn-outline:hover {
  background: rgba(255, 255, 255, 0.05);
  transform: translateY(-2px);
}

/* ── Footer ── */
.footer {
  position: relative;
  z-index: 1;
  background: rgba(0, 0, 0, 0.4);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding: 80px 0 13px;
}

.footer-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 48px;
  margin-bottom: 48px;
}

.footer-logo-row {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #fff;
  font-family: "Poppins", "Noto Sans SC", sans-serif;
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 12px;
}

.footer-brand p {
  color: rgba(255, 255, 255, 0.35);
  margin: 0;
  font-size: 13.5px;
  line-height: 1.7;
}

.footer-col h4 {
  color: rgba(255, 255, 255, 0.3);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-family: "Poppins", sans-serif;
  font-size: 11px;
  font-weight: 700;
  margin-bottom: 18px;
}

.footer-col a {
  display: block;
  color: rgba(255, 255, 255, 0.5);
  padding: 4px 0;
  font-size: 13.5px;
  text-decoration: none;
  transition: color 0.2s;
  cursor: pointer;
}

.footer-col a:hover {
  color: #fff;
}

.footer-bottom {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  color: rgba(255, 255, 255, 0.5);
  text-align: center;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  margin-top: 48px;
  padding-top: 24px;
}

.footer-bottom > div {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.footer-webmaster {
  margin: 0 0 10px;
}

.footer-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  text-decoration: none;
  transition: color 0.25s;
  cursor: pointer;
}

.footer-link:hover {
  color: #60a5fa;
}

.footer-copyright {
  color: rgba(255, 255, 255, 0.4);
  margin: 0;
  font-size: 12px;
}

/* ── Animations ── */
@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse-ring {
  0% {
    box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.4);
  }

  70% {
    box-shadow: 0 0 0 10px rgba(56, 189, 248, 0);
  }

  100% {
    box-shadow: 0 0 0 0 rgba(56, 189, 248, 0);
  }
}

/* ── Responsive ── */
@media (width <=1024px) {
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .cases-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .footer-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (width <=768px) {
  .nav-links {
    display: none;
  }

  .nav-pill {
    padding: 12px 16px;
  }

  .nav-brand {
    font-size: 15px;
  }

  .hero {
    padding: 140px 20px 40px;
  }

  .hero-title {
    font-size: 40px;
  }

  .hero-input-wrap {
    max-width: 100%;
  }

  .hero-actions {
    flex-direction: column;
    align-items: center;
  }

  .hero-metrics {
    gap: 24px;
  }

  .metric-value {
    font-size: 24px;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .cases-grid {
    grid-template-columns: 1fr 1fr;
  }

  .cta-card {
    border-radius: 28px;
    padding: 56px 24px;
  }

  .cta-buttons {
    flex-direction: column;
    align-items: center;
  }

  .footer-grid {
    grid-template-columns: 1fr;
    gap: 32px;
  }
}

@media (width <=480px) {
  .cases-grid {
    grid-template-columns: 1fr;
  }

  .hero-title {
    font-size: 32px;
  }
}
</style>
