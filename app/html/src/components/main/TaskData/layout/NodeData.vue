<template>
    <v-data-table
    :headers="headers"
    :items="dataItems"
    item-key="field"
    class="elevation-1"
    disable-pagination
    :hide-default-footer="true"
    fixed-header
  >
    <!-- :height="options.height" -->

    <template v-slot:item.value="{ item }">
      <div
        v-if="typeof item.value === 'object' && item.value != null"
      >
        <json-viewer
          :value="cacheField[item.field][1].value"
          :expand-depth=3
          copyable
          theme="json-viewer-theme"
        ></json-viewer>
      </div>
      <div v-else>
        {{ item.value }}
      </div>
    </template>
  </v-data-table>
</template>


<script>
import { mapGetters, mapState, mapActions } from 'vuex'


export default {
  name: 'NodeData',
  props: [
    'options',
  ],
  data(){
    return {
      cacheField:{},
      headers: [{
        text: 'Field',
        value: 'field'
      },{
        text: 'Value',
        value: 'value',
      },]
    }
  },
  watch: {
    activeTaskNode(){
      // 清空缓存
      this.cacheField = {};
    }
  },
  computed: {
    ...mapGetters('task', [
      'activeTaskRawItem',
      'activeTaskNode',
    ]),
    dataItems(){
      if(!this.activeTaskRawItem || this.activeTaskNode == '') return []
      let node = this.activeTaskRawItem.allNodes[this.activeTaskNode];
      let nodeData = node.data;
      let field_value = []
      for(let k in nodeData){
        let value = nodeData[k];

        // 同一JSON结果避免重新渲染，缓存Object对象
        let valueJson = JSON.stringify(value);
        let dataItem = null;
        let [cacheJson, cacheValue] = this.cacheField[k] || [];
        if(valueJson == cacheJson){
          dataItem = cacheValue;
        }else{
          dataItem = {
            field: k,
            value: value
          }
          // 缓存JSON对象
          this.cacheField[k] = [valueJson, dataItem]
        }
        field_value.push(dataItem)
      }
      return field_value
    }

  },
}

</script>

<style lang='stylus' scoped>

.v-data-table
  >>> .v-data-table__wrapper
    > table> tbody> tr:hover
      background-color: #0000 !important

.v-data-table
  border-radius: 0

  >>> .v-row-group__header
    background-color: #313131
    padding: 0.2rem

  >>> .json-viewer-theme 
    background: #0000
    white-space: nowrap
    color: #525252
    font-size: 14px
    font-family: Consolas, Menlo, Courier, monospace

    .jv-ellipsis 
      color: #999;
      background-color: #eee
      display: inline-block
      line-height: 0.9
      font-size: 0.9em
      padding: 0px 4px 2px 4px
      border-radius: 3px
      vertical-align: 2px
      cursor: pointer
      user-select: none
    
    .jv-button
      color: #49b3ff 
    .jv-key
      color: #fff 
    .jv-item
      &.jv-array
        color: #fff
      &.jv-boolean
        color: #fc1e70
      &.jv-function
        color: #067bca
      &.jv-number
        color: #fc1e70
      &.jv-number-float
        color: #fc1e70
      &.jv-number-integer
        color: #fc1e70
      &.jv-object
        color: #fff
      &.jv-undefined
        color: #e08331
      &.jv-string
        color: #42b983
        word-break: break-word
        white-space: normal
    .jv-node:after
      color: #fff

    .jv-code 
      .jv-toggle
        &:before
          padding: 0px 2px
          border-radius: 2px
        
        &:hover 
          &:before 
            background: #eee


</style>