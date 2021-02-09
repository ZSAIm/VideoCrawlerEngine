<template>
  <div class="checkbox-item">
    <!-- <div class='checkbox-title'>{{ item.title }}</div> -->
    <v-checkbox
      :label="item.name"
      v-model="item.value"
    >

    </v-checkbox>
  </div>
</template>


<script>
export default {
  name: "Checkbox",
  props: [
    'item'
  ]
}
</script>


<style lang="stylus" scoped>

.v-input
  margin: 0
.checkbox-item
  width: 100%

.checkbox-title
  font-weight: bold
  margin-bottom: 0.2rem
  font-size: 1rem;

.checkbox-desc
  font-size: 0.5rem;
  color: #bbb

</style>