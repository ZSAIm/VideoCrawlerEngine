<template>
  <main id="main-container"
    :style="{width: mainApp.width + 'px',height: mainApp.height + 'px' }"
  >
    <RespAlert
      :option="alertOptions"
    ></RespAlert>
    <v-container
      fluid
    >
      <router-view 
        name="main"
      />
    </v-container>
  </main>
</template>


<script>
import { mapActions, mapState } from 'vuex'
import RespAlert from '@/components/popout/message/RespAlert/RespAlert'


export default {
  name: 'AppMain',
  data(){
    return {
    }
  },
  computed: {
    ...mapState('app', [
      'alertOptions',
      'mainApp'
    ]),
  },
  methods: {
    ...mapActions('app', [
      'initAppModule',
      'destroyAppModule'
    ])
  },
  mounted() {
    this.initAppModule()
  },
  destroyed(){
    this.destroyAppModule()
  },
  components: {
    RespAlert
  }
}
</script>



<style lang='stylus' scoped>

#main-container
  flex: 1

  .container
    height: 100%
    padding: 0px
    
    
</style>