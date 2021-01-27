<template>
  <div class="tool-box">
    <v-toolbar dense>
      <add-new-dialog
        :options="dialogOptions"
      ></add-new-dialog>

      <control-tool
        :dialogOptions="dialogOptions"
      ></control-tool>

    </v-toolbar>
  </div>
</template>


<script>
import { mapGetters, mapActions } from 'vuex'
import ControlTool from './layout/ControlTool'
import AddNewDialog from './layout/AddNewDialog'

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
    ControlTool,
  }
}
</script>


<style lang='stylus' scoped>

.tool-box
  display: flex
  flex-direction: row
  .v-btn
    height: 100%
    border-radius: 0
    
    .v-icon
      margin-right: 0.3rem
  .tool-control
    height: 100%

    .v-btn
      min-width: 2rem
      padding: 0
.v-dialog
  border-radius: 0

</style>