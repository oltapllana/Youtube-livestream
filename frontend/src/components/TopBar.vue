<template>
  <header class="topbar">
    <div class="topbar-left">
      <img
        src="../assets/up.svg"
        alt="UniPRStream Logo"
        class="logo-image"
        style="height:40px;background-color:white;border-radius:100%"
      />
      <span class="logo-brand">UniPR<span class="logo-accent">Stream</span></span>
    </div>
    <div class="topbar-center">
      <span class="now-label">{{ clockLabel }}</span>
    </div>
    <div class="topbar-right">
      <button class="btn-icon" @click="$emit('openPrefs')" title="Preferences">
        <svg viewBox="0 0 24 24">
          <path d="M3 17v2h6v-2H3zM3 5v2h10V5H3zm10 16v-2h8v-2h-8v-2h-2v6h2zM7 9v2H3v2h4v2h2V9H7zm14 4v-2H11v2h10zm-6-4h2V7h4V5h-4V3h-2v6z" />
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup>
defineProps({
  clockLabel: { type: String, default: '—' },
})

defineEmits(['openPrefs'])
</script>

<style scoped>
.logo-image {
  height: 42px;
  width: auto;
  object-fit: contain;
}
.logo-brand {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: #f1f1f1;
}
.logo-accent {
  color: #3ea6ff;
}
</style>