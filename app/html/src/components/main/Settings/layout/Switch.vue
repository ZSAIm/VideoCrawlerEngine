<template>
  <div class="switch-item">
    <v-switch
      :label="item.name"
      v-model="item.value"
      :disabled="item.disabled"
    >
    </v-switch>
  </div>
</template>


<script>
export default {
  name: "Switches",
  props: [
    'item'
  ],
}
</script>


<style lang="stylus" scoped>

.v-input
  margin: 0
.switch-item
  width: 100%


.switch-title
  font-weight: bold
  margin-bottom: 0.2rem
  font-size: 1rem;

.switch-desc
  font-size: 0.5rem;
  color: #bbb


</style>