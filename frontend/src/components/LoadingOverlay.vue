<template>
  <div class="loading-overlay">
    <div class="spinner"></div>
    <p>{{ message }}</p>
  </div>
</template>

<script setup>
defineProps({
  message: { type: String, default: 'Loading…' },
})
</script>
