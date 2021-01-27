<template>
  <v-data-table
    :headers="headers"
    :items="taskNodeItems"
    item-key="a5g"
    class="elevation-1"
    disable-pagination
    :hide-default-footer="true"
    group-by="ab"
    sort-by="index"
    loading="true"
    fixed-header
    :height="options.height"
  >
    <template  v-slot:group.header="{ toggle, group, items, headers, isOpen }">
      <td :colspan="headers.length" class="data-group-header" @click="toggle">
        <div class="group-header">
          <strong class="group-header-title">{{ updateGroupItem(group, items) }}</strong>
          <v-progress-linear
            :value="groupItems[group].percent"
            :color="groupItems[group].color"
            height="15"
          >
            <strong>{{ groupItems[group].percent.toFixed(2) }}%</strong>
          </v-progress-linear>
          <v-btn 
            small 
            icon 
            class="group-collapse-toggle"
          >
            <v-icon>
            {{ isOpen ? 'mdi-chevron-down' : 'mdi-chevron-up' }} 
            </v-icon>
          </v-btn>
        </div>
        
      </td>
    </template>
    <template v-slot:item.percent="{ item }">
      <v-progress-linear
        :value="item.percent == null ? 0 : item.percent"
        :indeterminate="item.percent == null ? true : false"
        :color="item.color"
        height="15"
      >
        <strong>{{ item.percent == null ? '' : item.percent.toFixed(2) + '%' }}</strong>
      </v-progress-linear>
    </template>

    <template v-slot:item.control="{ item }">
      <v-btn 
        small 
        icon
        disabled
      >
        <v-icon>
          mdi-play
        </v-icon>
      </v-btn>
      <v-btn 
        small 
        icon 
        disabled
      >
        <v-icon>
          mdi-pause
        </v-icon>
      </v-btn>
      <v-btn 
        small 
        icon 
        @click="selectNodeItem(item.a5g)"
      >
        <v-icon>
          mdi-information-outline 
        </v-icon>
      </v-btn>
      
    </template>
  </v-data-table>

</template>


<script>
import { mapActions, mapGetters, mapState } from 'vuex'
import { getStatusColor, getItemsTotalStatus } from '@/helper/task'

export default {
  name: 'NodeTable',
  props: [
    'options',
    'rootSelect'
  ],
  data(){
    return {
      groupItems:{},
      headers: [{
        text: '#',
        value: 'index',
        align: 'end',
      },{
        text: 'Ab',
        value: 'ab'
      },{
        text: 'A5g',
        value: 'a5g',
      },{
        text: 'Name',
        value: 'name'
      },{
        text: 'Percent',
        value: 'percent'
      },{
        text: 'Speed',
        value: 'speed'
      },{
        text: 'TimeLeft',
        value: 'timeleft'
      },{
        text: 'Control',
        value: 'control',
        align: 'end',
        sortable: false,
      }],
    }
  },
  computed: {
    ...mapGetters('task',[
      'activeTaskRawItem',
    ]),
    taskNodeItems(){
      if(!this.activeTaskRawItem) return [];
      let allNodes = this.activeTaskRawItem.allNodes;
      this.groupItems = {};
      return Object.values(allNodes).map((v, index) => {
        let [a, b, ..._] = v.a5g.split('-');
        let ab = [a,b].join('-')
        return {
          index: index,
          ab: ab,
          a5g: v.a5g,
          name: v.name,
          percent: v.percent,
          speed: v.speed,
          timeleft: v.timeleft == null ? '∞' : v.timeleft.toFixed(2) + 's',
          weight: v.weight,
          color: getStatusColor(v.status),
          status: v.status,
        }
      })
    }
  },
  methods: {
    ...mapActions('task', [
      'selectNodeItem',
    ]),
    updateGroupItem(groupName, items){
      // 将插槽数据绑定到data以复用
      let status = getItemsTotalStatus(items);
      this.groupItems[groupName] = {
        name: groupName,
        percent: this.getBranchPercent(items),
        color: getStatusColor(status),
      }
      return groupName
    },
    getBranchPercent(items){
      let totalWeight = 0;
      let totalPercent = 0;
      for(let v of items){
        totalWeight += v.weight;
      }
      for(let v of items){
        if(v.percent == null){
          totalPercent = 0
          break
        } 
        totalPercent += v.percent * v.weight / totalWeight
      }
      return totalPercent;
    },
  },
}
</script>


<style lang='stylus' scoped>


.v-data-table
  >>> .v-data-table__wrapper
    > table> tbody> tr:hover
      background-color: #2c2c2c !important


.v-data-table
  >>> .v-data-table__wrapper
    overflow-y: overlay
    &:hover
      &::-webkit-scrollbar-track
        background-color: #2525258c

      &::-webkit-scrollbar-thumb
        background-color: #4242428c

  >>> .v-row-group__header
    background-color: #313131
    padding: 0.2rem

  >>> .data-group-header
    border-radius: 0
    cursor: pointer
    height: auto
    padding: 0

  >>> .group-collapse-toggle
    float: right
    flex: 1

.group-header
  display: flex

  .group-header-title
  .v-progress-linear
    margin-top: auto
    margin-bottom: auto
    margin-left: 0.6rem
    margin-right: 0.6rem

  .group-header-title 
    flex: none
    

  .v-btn
    flex: none


</style>