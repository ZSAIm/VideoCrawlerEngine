<template>
  <v-alert
    :value="option.show"
    text
    prominent
    type="error"
    icon="mdi-cloud-alert"
  >
    {{ option.msg }}
  </v-alert>
</template>

<script>
export default {
  name: 'ResponseMsg',
  props: [
    'option'
  ]
}
</script>


<style lang="stylus" scoped>


.v-alert
  position: fixed
  z-index: 999999
  right: 0

</style>