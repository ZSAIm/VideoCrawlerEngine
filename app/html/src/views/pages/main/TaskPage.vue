<template>
  <v-row class="task-view-main">
    <transition name="left-in">
      <v-col
        v-if="activeTaskNode == ''"
        id="task-view-left"
      >
        <TaskView
        ></TaskView>
      </v-col>
    </transition>

    <transition name="right-in">
      <v-col
        v-if="activeTaskKey != ''"
        id="task-view-right"
      >
        <TaskDetail
        ></TaskDetail>
      </v-col>
    </transition>

    <transition name="right-in">
      <v-col
        v-if="activeTaskNode != ''"
        id="task-view-right-expand"
      >
        <TaskData
        ></TaskData>
      </v-col>
    </transition>
    
  </v-row>
</template>


<script>
import { mapGetters, mapState, mapActions } from 'vuex'
import TaskView from '@/components/main/TaskView/TaskView'
import TaskDetail from '@/components/main/TaskDetail/TaskDetail'
import TaskData from '@/components/main/TaskData/TaskData'


export default {
  name: 'TaskPage',
  props: [
  ],
  data() {
    return {

    }
  },
  computed: {
    ...mapGetters('task', [
      'activeTaskNode',
      'activeTaskKey',
    ]),

  },
  methods: {
    ...mapActions('task', [
      'startFetchTaskListTimer',
      'stopFetchTaskListTimer'
    ])
  },
  components: {
    TaskView,
    TaskDetail,
    TaskData,
  },
  mounted() {
    
    // 开启下载任务获取
    this.startFetchTaskListTimer();

    // 加载测试数据
    // this.$store.dispatch('task/test')
  },
  destroyed(){
    this.stopFetchTaskListTimer()
  }
}
</script>


<style lang="stylus" scoped>


.right-in-enter-active
.left-in-enter-active
  transition: all .5s ease


.right-in-leave-to
.left-in-enter
  transform: translateX(-50px)
  opacity: 0


.left-in-leave-to
.right-in-enter
  transform: translateX(50px)
  opacity: 0


.v-col
.v-row
.task-view-main
#task-view-left
#task-view-right
#task-view-right-expand
  padding: 0 !important
  margin: 0 !important


</style>