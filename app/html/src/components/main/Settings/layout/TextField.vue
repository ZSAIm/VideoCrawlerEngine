<template>
  <div class="text-field-item">
    <!-- 数值类型文本框 -->
    <v-text-field
      v-if="!Array.isArray(item.value) && item.validation.type == 'number'"
      :label="item.name"
      v-model.number="item.value"
      outlined
      clearable
      :disabled="item.disabled"
      dense
    >
    </v-text-field>

    <!-- 文本类型文本框 -->
    <v-text-field
      v-else
      :label="item.name"
      v-model="item.value"
      outlined
      clearable
      :disabled="item.disabled"
      dense
    >
    </v-text-field>

  </div>
</template>


<script>
export default {
  name: "TextField",
  props: [
    'item'
  ],

}
</script>


<style lang="stylus" scoped>

.v-input
  margin: 0 !important
  margin-top: 0.6rem !important

  >>> .v-input__slot
    background-color: #333 !important
    border-radius: 0 !important
  
.v-input--is-disabled 
  >>> .v-input__slot
    background-color: #111 !important


.text-field-item
  width: 100%


</style>