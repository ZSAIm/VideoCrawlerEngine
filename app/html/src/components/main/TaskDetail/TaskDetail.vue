<template>
  <div>
    <v-toolbar floating>
      <v-btn 
        icon
        @click="activeTaskNode == '' ? setActiveTaskKey('') : selectNodeItem('')"
      >
        <v-icon>mdi-chevron-left</v-icon>
      </v-btn>

      <v-select
        :value="rootSelect.selected"
        :items="rootSelect.items"
        label="Root"
        dense
      ></v-select>
    </v-toolbar>
    <flow-chart
      :options="taskFlowOptions"
      :rootSelect="rootSelect"
    ></flow-chart>
    <node-table
      id="task-table-container"
      :options="taskTableOptions"
      :rootSelect="rootSelect"
    ></node-table>
  </div>

</template>


<script>
import { mapActions, mapState, mapGetters } from 'vuex'
import FlowChart from './layout/FlowChart'
import NodeTable from './layout/NodeTable'

export default {
  name: 'TaskDetail',
  props: [
  ],
  data(){
    return {
      rootSelect: {
        selected: null,
        items: [],
      },
    }
  },
  computed: {
    ...mapGetters('task', [
      'activeTaskRawItem',
      'activeTaskNode',
    ]),
    ...mapState('app', [
      'mainApp',
    ]),
    taskTableOptions(){
      return {
        height: this.mainApp.height / 2,
      }
    },
    taskFlowOptions(){
      return {
        height: this.mainApp.height / 2,
      }
    },
  },
  methods:{
    ...mapActions('task', [
      'selectNodeItem',
      'setActiveTaskKey'
    ]),
  },
  watch: {
    activeTaskRawItem(val, prev){
      if(!val) return [];
      this.rootSelect.items = Object.keys(val.allRoots);
      if(this.rootSelect.selected == null){
        this.rootSelect.selected = this.rootSelect.items[0]
      }
    },

  },
  components: {
    FlowChart,
    NodeTable
  },

}
</script>



<style lang='stylus' scoped>


.v-toolbar
  position: fixed
  z-index: 99999
  border-radius: 0 !important
  background-color: #2727272b !important
  transition: background-color 3s;


  >>> .v-text-field__details
  >>> .v-messages
    min-height: 0px !important


.v-toolbar:hover
  background-color: #272727 !important
  transition: background-color .8s;
  
  


</style>