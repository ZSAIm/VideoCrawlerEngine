<template>
  <div class="task-data-panel" :style="{'height': mainApp.height + 'px'}">
    <v-tabs
      v-model="taskDataTab"
    >
      <v-tab
        key="NodeData"
      >Data</v-tab>
      <v-tab
        key="NodeLog"
      >Log</v-tab>
    </v-tabs>


    <v-tabs-items v-model="taskDataTab">
      <v-tab-item
        key="NodeData"
      >
        <NodeData
          :options="taskDataOptions"
        >
        </NodeData>
        <!-- <v-card flat>
          <v-card-text v-text="text"></v-card-text>
        </v-card> -->
      </v-tab-item>


      <v-tab-item
        key="NodeLog"
      >
        <NodeLog
          :options="taskDataOptions"
        >
        </NodeLog>
      </v-tab-item>

    </v-tabs-items>

  </div>
</template>



<script>
import { mapState } from 'vuex'
import NodeData from './layout/NodeData'
import NodeLog from './layout/NodeLog'


export default {
  name: 'TaskData',
  props: [
  ],
  data(){
    return {
      taskDataTab: null,
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
    NodeLog,
  }
}
</script>


<style lang='stylus' scoped>

.task-data-panel
  display: flex
  flex-direction: column

  .v-tabs
    flex: 0

  .v-tabs-items
    flex: 1
    overflow-y: auto

</style>