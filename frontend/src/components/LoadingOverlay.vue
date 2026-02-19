<template>
  <Teleport to="body">
    <transition name="fade">
      <div
        v-if="open"
        class="loading-overlay"
        role="status"
        aria-live="polite"
        aria-busy="true"
      >
        <div class="loading-card">
          <div class="ring" aria-hidden="true"></div>

          <div class="loading-text">
            <div class="title">{{ title }}</div>
            <div v-if="message" class="msg">{{ message }}</div>
          </div>

          <div class="dots" aria-hidden="true">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: 'Loading' },
  message: { type: String, default: '' },
})
</script>

<style scoped>
/* overlay */
.loading-overlay{
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: grid;
  place-items: center;
  background: rgba(10, 12, 18, .55);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 24px;
}

/* card */
.loading-card{
  width: min(420px, 92vw);
  display: grid;
  grid-template-columns: 56px 1fr auto;
  gap: 14px;
  align-items: center;
  padding: 18px 18px;
  border-radius: 18px;
  background: rgba(255,255,255,.10);
  border: 1px solid rgba(255,255,255,.14);
  box-shadow: 0 20px 70px rgba(0,0,0,.35);
}

/* spinner ring */
.ring{
  width: 44px;
  height: 44px;
  border-radius: 999px;
  border: 3px solid rgba(255,255,255,.18);
  border-top-color: rgba(255,255,255,.92);
  animation: spin 1s linear infinite;
}

/* text */
.loading-text .title{
  font-weight: 700;
  letter-spacing: .2px;
  color: rgba(255,255,255,.95);
  font-size: 14px;
}
.loading-text .msg{
  margin-top: 2px;
  color: rgba(255,255,255,.75);
  font-size: 13px;
  line-height: 1.25;
}

/* dots */
.dots{
  display: inline-flex;
  gap: 6px;
  padding-left: 6px;
}
.dots span{
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: rgba(255,255,255,.72);
  animation: bounce 1.0s ease-in-out infinite;
}
.dots span:nth-child(2){ animation-delay: .12s; }
.dots span:nth-child(3){ animation-delay: .24s; }

/* transitions */
.fade-enter-active, .fade-leave-active{ transition: opacity .18s ease; }
.fade-enter-from, .fade-leave-to{ opacity: 0; }

@keyframes spin{ to { transform: rotate(360deg); } }
@keyframes bounce{
  0%, 100% { transform: translateY(0); opacity: .55; }
  50% { transform: translateY(-5px); opacity: 1; }
}
</style>
