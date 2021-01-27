<template>
  <main id="main-container">
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
import { mapActions } from 'vuex'


export default {
  name: 'AppMain',
  data(){
    return {
      mainSize: {
        height: 0,
      }
    }
  },
  computed: {
    // mainContainerDom(){
    //   return document.getElementById('main-container')
    // },
    // statusBarDom(){
    //   return document.getElementById('status-bar')
    // },
  },
  methods: {
    ...mapActions('app', [
      'initAppModule',
      'destroyAppModule'
    ])
    // windowResize(){
    //   this.mainSize.height = (
    //       innerHeight - 
    //       this.statusBarDom.offsetHeight - 
    //       this.mainContainerDom.offsetTop
    //   );
    // }
  },
  mounted() {
    this.initAppModule()
  },
  destroyed(){
    this.destroyAppModule()
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