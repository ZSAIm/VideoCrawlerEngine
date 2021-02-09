<template>
  <div class="settings-container">
    <v-col class="settings-view">
      <v-row class="settings-tree">
        <Tree
          :items="bindConf"
          :active="activeItemId"
        />
      </v-row>

      <v-row id="settings-content"
        :style="{height: mainApp.height + 'px'}"
      >
        <Configure/>
      </v-row>
    </v-col>
  </div>
</template>

<script>
import { mapActions, mapGetters, mapState } from 'vuex'
import Tree from './layout/Tree'
import Configure from './layout/Configure'

export default {
  name: 'Settings',
  computed: {
    ...mapState('settings', [
      'inViewItems',
      'activeItemId',
      'bindConf'
    ]),
    ...mapGetters('settings', [
      'diffConf'
    ]),
    ...mapState('app', [
      'mainApp'
    ])
  },
  methods: {
    ...mapActions('settings', [
      'setActiveConfItem',
      'calMainInView'
    ]),
   
  },
  components: {
    Tree,
    Configure,
  },
  mounted(){
    let dom = document.getElementById('settings-content')
    dom && dom.addEventListener('scroll', this.calMainInView);
  },
  destroyed(){
    let dom = document.getElementById('settings-content')
    dom && dom.removeEventListener('scroll', this.calMainInView);
  }
}
</script>

<style lang="stylus" scoped>

.settings-view
.settings-tree
#settings-content
  margin: 0
  padding: 0


.settings-view
  display: flex
  flex-direction: row


.settings-tree
  max-width: 10rem

#settings-content
  flex: 1
  // height: 100%
  overflow-y: auto


.settings-container
  width: 100%

</style>