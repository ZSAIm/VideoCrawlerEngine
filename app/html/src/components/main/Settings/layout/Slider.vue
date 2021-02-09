<template>
  <v-slider
    v-model="item.value"
    :label="item.name"
    :min="item.validation.min"
    :max="item.validation.max"
    thumb-label
    ticks
  ></v-slider>
</template>


<script>
export default {
  name: "Slider",
  props: [
    'item'
  ]
}
</script>


<style lang="stylus" scoped>

</style>