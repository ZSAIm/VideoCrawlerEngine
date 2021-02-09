<template>
  <Settings/>
</template>


<script>
import { mapState, mapActions } from 'vuex'
import Settings from '@/components/main/Settings/Settings'

export default {
  name: 'SettingsPage',
  computed: {
    ...mapState('app', [
      'mainApp'
    ]),
  },
  methods: {
    ...mapActions('settings', [
      'getConf',
      'clearConfData'
    ])
  },
  components: {
    Settings,
  },
  mounted(){
    // 避免路由切换不流畅，延时获取配置信息
    setTimeout(() => {
      this.getConf()
    }, 200)
  },
  destroyed(){
    this.clearConfData();
  }
}
</script>

<style lang='stylus' scoped>


</style>