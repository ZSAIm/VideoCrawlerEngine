<template>
  <div class="control-box">
    <v-toolbar dense>
      <AddNewDialog
        :options="dialogOptions"
      ></AddNewDialog>

      <TaskTool
        :dialogOptions="dialogOptions"
      ></TaskTool>

    </v-toolbar>
  </div>
</template>


<script>
import { mapGetters, mapActions } from 'vuex'
import TaskTool from './layout/TaskTool'
import AddNewDialog from '@/components/popout/dialog/AddNew/AddNew'

export default {
  name: 'TaskControl',
  data() {
    return {
      dialogOptions: {
        show: false
      },
    }
  },
  
  methods:{
  },
  components: {
    AddNewDialog,
    TaskTool,
  }
}
</script>


<style lang='stylus' scoped>

.control-box
  display: flex
  flex-direction: row
  

</style>