<template>
  <div>
    <div
      class="filters-overlay"
      :class="{ open }"
      @click="$emit('update:open', false)"
    ></div>
    <aside class="filters-panel" :class="{ open }">
      <div class="filters-header">
        <h2>Preferences</h2>
        <button class="btn-icon btn-close" @click="$emit('update:open', false)">
          &times;
        </button>
      </div>

      <div class="filters-body">
        <label>
          <span>Opening Time</span>
          <input type="time" v-model="prefs.openTime" />
        </label>
        <label>
          <span>Closing Time</span>
          <input type="time" v-model="prefs.closeTime" />
        </label>
        <label>
          <span>Min Duration (% of shortest)</span>
          <select v-model.number="prefs.minDurationPct">
            <option :value="70">70%</option>
            <option :value="80">80%</option>
            <option :value="90">90%</option>
            <option :value="100">100%</option>
          </select>
        </label>
        <label>
          <span>Channels Count</span>
          <select v-model.number="prefs.channelsCount">
            <option :value="10">10</option>
            <option :value="20">20</option>
          </select>
        </label>
        <label>
          <span>Switch Penalty (% of avg score)</span>
          <select v-model.number="prefs.switchPenaltyPct">
            <option :value="3">3%</option>
            <option :value="5">5%</option>
            <option :value="7">7%</option>
            <option :value="10">10%</option>
          </select>
        </label>
        <label>
          <span>Bonus (% of avg score)</span>
          <select v-model.number="prefs.bonusPct">
            <option :value="3">3%</option>
            <option :value="5">5%</option>
            <option :value="7">7%</option>
            <option :value="10">10%</option>
          </select>
        </label>
        <label>
          <span>Termination Penalty</span>
          <input
            type="number"
            v-model.number="prefs.terminationPenalty"
            min="0"
            max="100"
          />
        </label>
        <label>
          <span>Max Consecutive Genre</span>
          <input
            type="number"
            v-model.number="prefs.maxConsecutiveGenre"
            min="1"
            max="10"
          />
        </label>

        <!-- Category selector with toggle switches -->
        <div class="category-section">
          <h4>Channel Categories</h4>
          <div class="category-toggles">
            <label class="toggle-label">
              <input
                type="checkbox"
                v-model="prefs.categoryFilter"
                value="science"
                class="toggle-input"
              />
              <span class="toggle-switch"></span>
              <span class="toggle-text">Science</span>
            </label>
            <label class="toggle-label">
              <input
                type="checkbox"
                v-model="prefs.categoryFilter"
                value="technology"
                class="toggle-input"
              />
              <span class="toggle-switch"></span>
              <span class="toggle-text">Technology</span>
            </label>
            <label class="toggle-label">
              <input
                type="checkbox"
                v-model="prefs.categoryFilter"
                value="climate"
                class="toggle-input"
              />
              <span class="toggle-switch"></span>
              <span class="toggle-text">Climate</span>
            </label>
          </div>
        </div>

        <!-- Channels list for selected categories -->
        <div v-if="channels.length" class="channels-section">
          <h4>Selected Channels</h4>
          <div class="channels-list">
            <label v-for="c in channels" :key="c.channel_id" class="channel-item">
              <input
                type="checkbox"
                :value="c.channel_id"
                v-model="prefs.selectedChannelIds"
                class="channel-checkbox"
              />
              <span class="checkmark"></span>
              <span class="channel-name">{{ c.title }}</span>
            </label>
          </div>
        </div>
        <div v-else class="no-channels-hint">
          <p>Select categories above to view channels</p>
        </div>

        <div class="filters-actions">
          <button class="btn btn-secondary" @click="onSave">Save</button>
          <button class="btn btn-primary" @click="$emit('saveAndGenerate')">
            Save &amp; Generate
          </button>
        </div>
        <p class="filters-status" :style="{ color: statusColor }">{{ statusMsg }}</p>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import { fetchStreams } from "../api.js";
import { withLoader } from "../loading.js";

const props = defineProps({
  open: { type: Boolean, default: false },
  prefs: { type: Object, required: true },
});

const emit = defineEmits(["update:open", "save", "saveAndGenerate"]);

const statusMsg = ref("");
const statusColor = ref("#aaa");

const channels = ref([]);

async function loadStreams() {
  // opsionale: mos e ngarko nëse paneli është i mbyllun
  if (!props.open) return;

  const selCats = [...(props.prefs.categoryFilter || [])];

  return withLoader(
    { title: "Loading channels", message: "Fetching streams…" },
    async () => {
      try {
        const data = await fetchStreams(false);
        if (selCats.length === 0) {
          channels.value = [];
        } else {
          channels.value = selCats.flatMap((cat) =>
            (data[cat] || []).map((s) => ({ ...s, category: cat }))
          );
        }
      } catch (e) {
        channels.value = [];
      }
    }
  );
}

onMounted(() => {
  if (props.open) loadStreams();
});

watch(
  () => [props.open, props.prefs.categoryFilter],
  async () => {
    if (props.open) {
      await loadStreams();
      // Filter selectedChannelIds to only include channels from currently selected categories
      const validIds = new Set(channels.value.map((c) => c.channel_id));
      props.prefs.selectedChannelIds = props.prefs.selectedChannelIds.filter((id) =>
        validIds.has(id)
      );
    }
  },
  { deep: true }
);

async function onSave() {
  try {
    emit("save");
    statusMsg.value = "Preferences saved!";
    statusColor.value = "#4caf50";
  } catch {
    statusMsg.value = "Failed to save";
    statusColor.value = "#f44336";
  }
  setTimeout(() => {
    statusMsg.value = "";
  }, 3000);
}
</script>
