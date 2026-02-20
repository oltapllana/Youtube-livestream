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
          <span>Opening Time <small class="field-hint">(when the schedule starts)</small></span>
          <input type="time" v-model="prefs.openTime" />
        </label>
        <label>
          <span>Closing Time <small class="field-hint">(when the schedule ends)</small></span>
          <input type="time" v-model="prefs.closeTime" />
        </label>
        <label>
          <span>Min Duration <small class="field-hint">(minimum length of each slot, % of shortest video)</small></span>
          <select v-model.number="prefs.minDurationPct">
            <option :value="70">70%</option>
            <option :value="80">80%</option>
            <option :value="90">90%</option>
            <option :value="100">100%</option>
          </select>
        </label>
        <label>
          <span>Channels Count <small class="field-hint">(how many channels to include)</small></span>
          <select v-model.number="prefs.channelsCount">
            <option :value="10">10</option>
            <option :value="20">20</option>
          </select>
        </label>
        <label>
          <span>Switch Penalty <small class="field-hint">(cost of switching channels, % of avg score)</small></span>
          <select v-model.number="prefs.switchPenaltyPct">
            <option :value="3">3%</option>
            <option :value="5">5%</option>
            <option :value="7">7%</option>
            <option :value="10">10%</option>
          </select>
        </label>
        <label>
          <span>Bonus <small class="field-hint">(reward for preferred content, % of avg score)</small></span>
          <select v-model.number="prefs.bonusPct">
            <option :value="3">3%</option>
            <option :value="5">5%</option>
            <option :value="7">7%</option>
            <option :value="10">10%</option>
          </select>
        </label>
        <label>
          <span>Termination Penalty <small class="field-hint">(penalty when a program is cut short)</small></span>
          <input
            type="number"
            v-model.number="prefs.terminationPenalty"
            min="0"
            max="100"
          />
        </label>
        <label>
          <span>Max Consecutive Genre <small class="field-hint">(max same-genre programs in a row)</small></span>
          <input
            type="number"
            v-model.number="prefs.maxConsecutiveGenre"
            min="1"
            max="10"
          />
        </label>

        <!-- Category selector with toggle switches -->
        <div class="category-section">
          <h4>Channel Categories <small class="field-hint">(filter streams by topic)</small></h4>
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
          <div class="channels-header">
            <h4>Selected Channels ({{ selectedChannelsCount }})</h4>
            <label class="select-all-control">
              <span>Select all</span>
              <input
                type="checkbox"
                class="channel-checkbox"
                :checked="allChannelsSelected"
                @change="toggleSelectAllChannels"
              />
              <span class="checkmark" :class="{ partial: someChannelsSelected && !allChannelsSelected }"></span>
            </label>
          </div>
          <div class="channels-list">
            <div v-for="c in channels" :key="c.channel_id" class="channel-item">
              <div class="channel-left" @click="toggleSingleChannel(c.channel_id)">
                <input
                  type="checkbox"
                  class="channel-checkbox"
                  :checked="isChannelSelected(c.channel_id)"
                />
                <span class="checkmark"></span>
              </div>
             
              <span class="channel-name">{{ c.title }}</span>
              <span class="channel-category" :class="`category-${c.category}`">{{ displayCategory(c.category) }}</span>
            </div>
          </div>
        </div>
        <div v-else class="no-channels-hint">
          <p>Select categories above to view channels</p>
        </div>

        <div class="filters-actions">
          <button class="btn btn-secondary" @click="onSave">Save</button>
          <button class="btn btn-primary" @click="onSaveAndGenerate">
            Save &amp; Generate
          </button>
        </div>
        <p class="filters-status" :style="{ color: statusColor }">{{ statusMsg }}</p>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from "vue";
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

const currentChannelIds = computed(() => channels.value.map((c) => c.channel_id));

const allChannelsSelected = computed(() => {
  if (!channels.value.length) return false;
  const selected = new Set(props.prefs.selectedChannelIds || []);
  return currentChannelIds.value.every((id) => selected.has(id));
});

const someChannelsSelected = computed(() => {
  if (!channels.value.length) return false;
  const selected = new Set(props.prefs.selectedChannelIds || []);
  return currentChannelIds.value.some((id) => selected.has(id));
});

const selectedChannelsCount = computed(() => {
  if (!channels.value.length) return 0;
  const selected = new Set(props.prefs.selectedChannelIds || []);
  return currentChannelIds.value.filter((id) => selected.has(id)).length;
});

function normalizeCategories(categories = []) {
  if (!Array.isArray(categories)) return [];
  return [...new Set(categories.map((c) => String(c).toLowerCase()))];
}

function syncSelectedChannels(addedCategories = []) {
  const validIds = new Set(currentChannelIds.value);
  const selectedSet = new Set(
    (props.prefs.selectedChannelIds || []).filter((id) => validIds.has(id))
  );

  if (addedCategories.length) {
    const addedSet = new Set(addedCategories.map((c) => String(c).toLowerCase()));
    channels.value.forEach((channel) => {
      if (addedSet.has(channel.category)) {
        selectedSet.add(channel.channel_id);
      }
    });
  }

  props.prefs.selectedChannelIds = [...selectedSet];
}

function toggleSelectAllChannels() {
  if (!channels.value.length) return;

  const currentSet = new Set(props.prefs.selectedChannelIds || []);
  if (allChannelsSelected.value) {
    currentChannelIds.value.forEach((id) => currentSet.delete(id));
  } else {
    currentChannelIds.value.forEach((id) => currentSet.add(id));
  }
  props.prefs.selectedChannelIds = [...currentSet];
}

function isChannelSelected(channelId) {
  return (props.prefs.selectedChannelIds || []).includes(channelId);
}

function toggleSingleChannel(channelId) {
  const selectedSet = new Set(props.prefs.selectedChannelIds || []);
  if (selectedSet.has(channelId)) {
    selectedSet.delete(channelId);
  } else {
    selectedSet.add(channelId);
  }
  props.prefs.selectedChannelIds = [...selectedSet];
}

function channelInitials(title = "") {
  const words = String(title).trim().split(/\s+/).filter(Boolean);
  if (!words.length) return "CH";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

function displayCategory(category = "") {
  const text = String(category).toLowerCase();
  if (!text) return "Unknown";
  return text.charAt(0).toUpperCase() + text.slice(1);
}

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
  if (props.open) {
    loadStreams().then(() => syncSelectedChannels());
  }
});

watch(
  () => props.open,
  async (isOpen) => {
    if (!isOpen) return;
    await loadStreams();
    syncSelectedChannels();
  }
);

watch(
  () => normalizeCategories(props.prefs.categoryFilter),
  async (newCategories, oldCategories = []) => {
    if (props.open) {
      await loadStreams();
      const oldSet = new Set(oldCategories);
      const addedCategories = newCategories.filter((cat) => !oldSet.has(cat));
      syncSelectedChannels(addedCategories);
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

function onSaveAndGenerate() {
  const selectedCategories = normalizeCategories(props.prefs.categoryFilter);
  if (selectedCategories.length === 0) {
    statusMsg.value = "Please select at least one category before generating a schedule.";
    statusColor.value = "#f44336";
    setTimeout(() => {
      statusMsg.value = "";
    }, 3000);
    return;
  }

  emit("saveAndGenerate");
}
</script>
