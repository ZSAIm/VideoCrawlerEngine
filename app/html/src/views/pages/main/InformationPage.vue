<template>
  <Information/>
</template>


<script>
import { mapState, mapActions } from 'vuex'
import Information from '@/components/main/Information/Information'

export default {
  name: 'InformationPage',
  computed: {
    ...mapState('app', [
      'mainApp'
    ]),
  },
  methods: {
    ...mapActions('information', [
      'startFetchAppInfoTimer',
      'stopFetchAppInfoTimer'
    ])
  },
  components: {
    Information,
  },
  mounted(){
    this.startFetchAppInfoTimer()
  },
  destroyed(){
    this.stopFetchAppInfoTimer()
  }
}
</script>

<style lang='stylus' scoped>


</style>