<template>
  <v-card
    tile
  >
    <v-list dense>
        <v-virtual-scroll
          :bench="1"
          :items="items"
          :height="mainApp.height - 16 + 'px'"
          item-height="81"
          multiple
        >
          <template v-slot:default="{ item }">
              <div 
                class="list-item"
                v-ripple="{ class: item.selected ? `pink--text` : `white--text` }"
              >
                <v-list-item
                  :id="'task-' + item.sign"
                  :key="'task-' + item.sign"
                  @dblclick="toggleSelectItem(item.sign, 2)"
                  @click="toggleSelectItem(item.sign, 1)"
                  :class="{ 'selected-item': item.selected }"
                >
                    <v-avatar
                      color="info"
                      size="32"
                    >
                      <span class="white--text">
                        {{ item.avatar }}

                      </span>
                    </v-avatar>
                    <v-list-item-content>
                      <div class="list-item-title">
                        <v-btn
                          x-small
                          color="secondary"
                          dark
                        >
                          {{ item.doneState }}
                        </v-btn>
                        <v-list-item-title 
                          v-text="item.title"
                          class="font-weight-blod"
                        ></v-list-item-title>
                        
                      </div>
                      <div class="item-subtitle">
                        <v-list-item-subtitle v-text="item.url"></v-list-item-subtitle>
                        <v-spacer/>
                        <v-list-item-subtitle
                          class="item-speed" 
                          v-text="item.speed">
                        </v-list-item-subtitle>
                      </div>
                      <div class="list-item-progress">
                        <v-progress-linear
                          v-for="(progress, index) in item.progresses"
                          :key="item.sign + '-' + index"
                          :indeterminate="progress.indeterminate"
                          :stream="progress.stream"
                          :style="{ flex: progress.ratio }" 
                          :value="progress.percent"
                          :color="progress.color"
                          buffer-value="100"
                          height="5"
                        >
                        </v-progress-linear>
                      </div>
                    </v-list-item-content>
                    <v-btn
                      depressed
                      icon
                      @click.stop="setActiveTaskKey(item.sign)"
                    >
                      <v-icon>
                       mdi-chevron-right  
                      </v-icon>
                    </v-btn>
                </v-list-item>
                <v-divider/>
              </div>
            
          </template>
        </v-virtual-scroll>
    </v-list>
  </v-card>
</template>


<script>
import { mapGetters, mapState, mapActions } from 'vuex'
import { getStatusColor } from '@/helper/task'

export default {
  name: 'List',
  props: [
    'options'
  ],
  data(){
    return {
    }
  },
  computed: {
    ...mapState('app', [
      'mainApp',
    ]),
    ...mapGetters('task', [
      'taskRawItems',
      'selectedTasks',
    ]),
    items () {
      return this.updateTaskListView(this.taskRawItems);
    },
  },
  methods: {
    ...mapActions('task', [
      'updateTaskItemData',
      'startFetchTaskListTimer',
      'setActiveTaskKey',
      'toggleSelectTask',
      'clearTaskSelect',
    ]),
    async toggleSelectItem(key, clickMode){
      // clickMode =1 单击； 2 双击
      // 这里结合使用原生更新样式，
      // 减少数据绑定的延迟造成的样式渲染延迟。
      let selLength = Object.keys(this.selectedTasks).length;
      if(clickMode == 1 && selLength == 0){
        // 空选择的情况下，需要双击激活选择
        return
      }else if(clickMode == 2 && selLength != 0) {
        // 非空选择的情况下，屏蔽双击
        return
      }
      let dom = document.getElementById('task-' + key);
      if(await this.toggleSelectTask(key)){
        dom.classList.add('selected-item')
      }else{
        dom.classList.remove('selected-item')
      }
    },
    updateTaskListView(taskRawItems){
      return taskRawItems.map(v => {
        let roots = v.allRoots;
        let rootIds = v.runningRoots.length == 0 ? Object.keys(roots) : v.runningRoots;
        let progresses = rootIds.map(rid => {
            return {
              indeterminate: roots[rid].percent == null,
              ratio: 1,
              percent: roots[rid].percent,
              color: getStatusColor(roots[rid].status),
            }
        });
        let doneCount = 0;
        Object.keys(roots).map(rid => {
            if (roots[rid].status == 'done'){
              doneCount ++;
            }
        })
        // 避免出现进度条空缺的问题
        if (progresses.length == 0) {
            progresses = [{
                indeterminate: false,
                ratio: 1,
                percent: 0,
                color: 'grey darken-2'
            }]
        }
        return {
            sign: v.sign,
            title: v.title,
            url: v.url,
            avatar: v.name.slice(0, 5),
            progresses: progresses,
            percent: v.percent,
            status: v.status,
            doneState: doneCount + '/' + Object.keys(roots).length,
            selected: this.selectedTasks[v.sign] != undefined
        }
      });
    },

  },
    mounted() {
      
      // 开启下载任务获取
      this.startFetchTaskListTimer();

      // 加载测试数据
      // this.$store.dispatch('task/test')
    }

}
</script>


<style lang="stylus" scoped>


.v-list-item
  cursor: pointer
  padding-top: 0.5rem
  padding-bottom: 0.5rem
  background-color: #181a1b
  transition: background-color 0.5s

  .v-list-item__title
    font-weight: 600
    transition: color 1s

  &:hover:before
  &:focus:before
    opacity: 0;

  &.selected-item
    background-color: #311d25 !important
    transition: background-color 1s

    .v-list-item__title
      color: rgb(235, 51, 114) !important
      transition: color 0.5s


.v-avatar
  margin-right: 1rem


.v-list-item__content
  margin-right: 1rem


.list-item-title
  display: flex

  .v-list-item__title
    padding-left: 0.3rem
    font-size: 0.95rem
    margin-top: auto
    margin-bottom: auto

  .v-btn
    float: left

.item-subtitle
  display: flex
  .item-speed
    flex: none


.list-item-progress
  margin-top: 0.2rem
  display: flex

  .v-progress-linear
    flex: 1

.item-progress-circular-percent
  color: white
  font-size: 0.1rem

</style>
