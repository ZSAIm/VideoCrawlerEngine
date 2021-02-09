<template>
  <div class="combobox-item">
    <!-- 列表类型文本框 -->
    <v-combobox
      v-model="item.value"
      :label="item.name"
      :items="item.extra.items"
      multiple
      chips
    >
      <template v-slot:selection="{ attrs, item, parent, selected }">
        <v-chip
          v-bind="attrs"
          :input-value="selected"
          label
          small
        >
          <span class="pr-2">
            {{ item }}
          </span>
          <v-icon
            small
            @click="parent.selectItem(item)"
          >
            close
          </v-icon>
        </v-chip>
      </template>
    </v-combobox>
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


.combobox-item
  width: 100%


</style>