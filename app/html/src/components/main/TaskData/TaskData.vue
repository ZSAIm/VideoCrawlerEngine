<template>
  <node-data
    :options="taskDataOptions"
  >
  </node-data>
</template>



<script>
import { mapState } from 'vuex'
import NodeData from './layout/NodeData'


export default {
  name: 'TaskData',
  props: [
  ],
  data(){
    return {
      
    }
  },
  computed: {
    ...mapState('app', [
      'mainApp',
    ]),
    taskDataOptions(){
      return {
        height: this.mainApp.height,
      }
    }
  },
  components: {
    NodeData,
  }
}
</script>


<style lang='stylus' scoped>


</style>