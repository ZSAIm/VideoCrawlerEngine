<template>
  <div class="tool-box">
    <!-- <v-toolbar dense>
      <add-new-dialog
        :options="dialogOptions"
      ></add-new-dialog> -->

      <v-btn 
        text
        @click="dialogOptions.show = true"
      >
        <v-icon>mdi-plus</v-icon>
        新建
      </v-btn>

      <div class="tool-control">
        <v-btn 
          text
          :disabled="continuesButton.disabled"
        >
          <v-icon>mdi-play</v-icon>
        </v-btn>
        <v-btn 
          text 
          :disabled="pauseButton.disabled"
          @click="stopSelectedTask()"
        >
          <v-icon>mdi-pause</v-icon>
        </v-btn>
      </div>
    <!-- </v-toolbar> -->
  </div>
</template>


<script>
import { mapGetters, mapState, mapActions } from 'vuex'

export default {
  name: 'ControlTool',
  props: [
    'dialogOptions'
  ],
  data() {
    return {
      continuesBtn: {
        disabled: true,
      },
      pauseBtn: {
        disabled: true
      },

    }
  },
  computed: {
    ...mapGetters('task', [
      'selectedTasks',

    ]),
    continuesButton(){
      return {
        disabled: Object.keys(this.selectedTasks).length == 0
      }
    },
    pauseButton(){
      return {
        disabled: Object.keys(this.selectedTasks).length == 0
      }
    }
  },
  methods: {
    ...mapActions('task', [
      'postStopTasks',

    ]),
    async stopSelectedTask(){
      let items = Object.keys(this.selectedTasks).map(v => ({
        key: v,
      }));
      let resp = await this.postStopTasks(items)
      console.log(resp)
    },
  },
}
</script>


<style lang='stylus' scoped>
.tool-box
  display: flex
  flex-direction: row
  height: 100%
  margin-left: 0.5rem

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