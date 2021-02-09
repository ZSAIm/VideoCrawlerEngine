<template>
  <div class="tool-box">
    <v-btn 
      text
      color="green"
      @click="submitDiff()"
      :disabled="diffConfList.length == 0"
    >
      <v-icon>mdi-playlist-check</v-icon>
      提交
    </v-btn>
    <v-card>
      <v-btn icon
        @click="prevDiff()"
      >
        <v-icon>mdi-chevron-left </v-icon>
      </v-btn>
      <v-card-title>{{ modifiedIndex + '/' + diffConfList.length}}</v-card-title>
      <v-btn icon
        @click="nextDiff()"
      >
        <v-icon>mdi-chevron-right </v-icon>
      </v-btn>
    </v-card>    
  </div>
</template>


<script>
import { mapGetters, mapState, mapActions } from 'vuex'


export default {
  name: 'TaskTool',
  props: [
    'dialogOptions'
  ],
  data() {
    return {
      modifiedIndex: 0,
    }
  },
  computed: {
    ...mapGetters('settings', [
      'diffConf'
    ]),
    diffConfList(){
      // 更新清零
      this.modifiedIndex = 0;
      return this.diffConf
    },
  },
  methods: {
    ...mapActions('settings', [
      'scrollToConfItem',
      'postConfModifies',
      'getConf',
      'calMainInView',
    ]),
    ...mapActions('app', [
      'setAlertOption'
    ]),
    async submitDiff(){
      // 提交修改的配置
      // TODO: 修改详情，确定框
      let {code, data, msg} = await this.postConfModifies();
      await this.getConf()
      await this.calMainInView()
      // this.setAlertOption({
      //   show: true,
      //   msg,
      //   // timeout:3000
      // })
    },
    nextDiff(){
      if(this.diffConfList.length == 0){
        this.modifiedIndex = 0
      }else{
        if(this.modifiedIndex +1 <= this.diffConfList.length){
          this.modifiedIndex ++;
        }else{
          this.modifiedIndex = 1;
        }
      }
      // 滚动到下一个差异处
      let diffItem = this.diffConfList[this.modifiedIndex - 1]
      diffItem != undefined && this.scrollToConfItem(diffItem.link.join('|'))
    },
    prevDiff(){
      if(this.modifiedIndex - 1 > 0){
        this.modifiedIndex--
      }else{
        this.modifiedIndex = this.diffConfList.length
      }
      // 滚动到上一个差异处
      let diffItem = this.diffConfList[this.modifiedIndex - 1]
      diffItem != undefined && this.scrollToConfItem(diffItem.link.join('|'))
      
    }
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
    height: 100% !important
    border-radius: 0
    
    .v-icon
      margin-right: 0.3rem
  .tool-control
    height: 100%

    .v-btn
      min-width: 2rem
      padding: 0


.v-card
  display: flex
  flex-direction: row
  .v-card__title
    font-size: 12px
    padding: 0
    margin-left: 0.5rem
    margin-right: 0.5rem

</style>