<template>
  <div class="mb-3">
    <!-- View Mode -->
    <div v-if="!isEditing" class="p-3 bg-gray-50 rounded-xl border border-gray-100 group relative hover:border-purple-200 transition-colors cursor-pointer" @click="startEdit">
      <div class="text-[10px] text-gray-400 font-bold uppercase mb-1 flex items-center justify-between">
        <span class="flex items-center">
          <span v-if="required" class="text-red-500 mr-1">*</span>
          {{ label }}
          <!-- AI Confidence Level Badge -->
          <span v-if="confidence && !isEdited" class="ml-2 px-1.5 py-[1px] rounded font-bold text-[8px]" :class="confidence >= 90 ? 'bg-green-100 text-green-600' : 'bg-amber-100 text-amber-600'">
            AI置信度: {{ confidence }}%
          </span>
          <!-- Edited Badge -->
          <span v-if="isEdited" class="ml-2 px-1.5 py-[1px] rounded font-bold text-[8px] bg-blue-100 text-blue-600">
            ✏️ 人工修正
          </span>
        </span>
        <!-- Edit Icon -->
        <svg class="w-3.5 h-3.5 text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>
      </div>
      <div class="text-sm font-bold truncate" :class="[highlight ? 'text-orange-600' : 'text-gray-800', !currentValue || currentValue === '-' ? 'text-gray-300 italic font-medium' : '']">
        {{ currentValue || '-' }}
      </div>

      <!-- Risk warning (if any) -->
      <div v-if="warningText" class="absolute -right-1 -top-2 bg-red-100 text-red-600 border border-red-200 shadow-sm text-[9px] px-1.5 py-0.5 rounded-md font-bold z-10 animate-bounce">
        {{ warningText }}
      </div>
    </div>

    <!-- Edit Mode -->
    <div v-else class="p-2.5 bg-white rounded-xl border-2 border-purple-500 shadow-sm shadow-purple-100 animate-[fade-in_0.15s_ease-out]">
      <div class="text-[10px] text-purple-600 font-bold uppercase mb-1 flex items-center">
        编辑: {{ label }}
      </div>
      <div class="flex items-center gap-1.5">
        <input
          ref="inputRef"
          v-model="editValue"
          @keyup.enter="saveEdit"
          @keyup.esc="cancelEdit"
          type="text"
          class="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1.5 text-sm font-bold text-gray-800 focus:outline-none focus:border-purple-300 focus:ring-1 focus:ring-purple-300 transition-all"
        />
        <button @click="saveEdit" class="p-1.5 bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors flex-shrink-0" title="保存 (Enter)">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"></path></svg>
        </button>
        <button @click="cancelEdit" class="p-1.5 bg-red-50 text-red-600 rounded-md hover:bg-red-100 transition-colors flex-shrink-0" title="取消 (Esc)">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';

const props = defineProps({
  label: String,
  modelValue: String,
  required: Boolean,
  highlight: Boolean,
  warningText: String,
  confidence: Number,
  editedParams: Object,
  fieldKey: String
});

const emit = defineEmits(['update:modelValue', 'mark-edited']);

const isEditing = ref(false);
const isEdited = ref(false);
const editValue = ref('');
const inputRef = ref(null);

// Get visual value (edited takes precedence)
const currentValue = ref(props.modelValue);

watch(() => props.modelValue, (newVal) => {
  if (!isEdited.value) {
    currentValue.value = newVal;
  }
});

const startEdit = () => {
  editValue.value = currentValue.value === '-' ? '' : currentValue.value;
  isEditing.value = true;
  nextTick(() => {
    if (inputRef.value) inputRef.value.focus();
  });
};

const cancelEdit = () => {
  isEditing.value = false;
};

const saveEdit = () => {
  const finalVal = editValue.value.trim() || '-';
  if (finalVal !== props.modelValue) {
    isEdited.value = true;
    emit('mark-edited', { key: props.fieldKey, value: finalVal });
  } else {
    isEdited.value = false;
  }
  currentValue.value = finalVal;
  emit('update:modelValue', finalVal);
  isEditing.value = false;
};
</script>

<style scoped>
@keyframes fade-in {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
