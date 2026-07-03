<script setup lang="ts">
defineProps<{
  eyebrow: string
  title: string
  description: string
}>()
</script>

<template>
  <header class="page-hero">
    <div class="page-hero__copy">
      <p class="page-hero__eyebrow">{{ eyebrow }}</p>
      <h1 class="page-hero__title">{{ title }}</h1>
      <p class="page-hero__desc">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="page-hero__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.page-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
  padding: 24px 28px;
  background: linear-gradient(135deg, #f8faff, #f5f9fe);
  border: 1px solid var(--border-accent);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.page-hero__eyebrow {
  margin: 0 0 4px;
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--brand-primary);
}

.page-hero__title {
  margin: 0;
  font-family: 'Manrope', system-ui, sans-serif;
  font-size: 1.3rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.page-hero__desc {
  margin: 6px 0 0;
  font-size: 0.88rem;
  color: var(--text-secondary);
  line-height: 1.6;
  max-width: 42rem;
}

.page-hero__actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

@media (max-width: 768px) {
  .page-hero {
    flex-direction: column;
    padding: 18px 20px;
  }

  .page-hero__actions { width: 100%; }
}
</style>
