<template>
  <v-card>
    <main-tab>
    </main-tab>
  </v-card>
</template>

<script>
import MainTab from '@/components/sider/MainTab/MainTab'


export default {
  name: 'SiderBar',
  components: {
    MainTab,
  }
}
</script>


<style lang="stylus" scoped>


.v-card
    border-radius: 0px

</style>