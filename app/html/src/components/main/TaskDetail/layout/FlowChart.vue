<template>
  
  <div id="task-flow-container" 
    :updateChart="!updateChartComputed"
    :style="{ height: options.height + 'px' }"
  >
    <!-- 
      virtualValue属性的传递没有实际用处，
      主要是利用computed的计算特性来更新节点图。
     -->
    
  </div>
</template>


<script>
import * as echarts from 'echarts';
import { mapGetters, mapActions } from 'vuex';

export default {
  name: 'FlowChart',
  props: [
    'options',
    'rootSelect',
  ],
  data() {
    return {
      $echarts: null,
      historyFlowJSON: '',
    }
  },
  computed: {
    ...mapGetters('task',[
      'activeTaskRawItem',
    ]),
    chartNode(){
      if(!this.activeTaskRawItem) return {};
      return this.genTaskFlowNodeData(this.activeTaskRawItem);
    },
    linksData(){
      let selected = this.rootSelect.selected || 0;
      if(!this.chartNode[selected]) return [];
      return this.chartNode[selected].links;
    },
    nodesData(){
      let selected = this.rootSelect.selected || 0;
      if(!this.chartNode[selected]) return [];  
      return this.chartNode[selected].data;
    },
    chartsOption(){
      return {
          title: {
              text: '节点图'
          },
          tooltip: {},
          animationDurationUpdate: 1000,
          animationEasingUpdate: 'quinticInOut',
          series: [
            {
              type: 'graph',
              layout: 'none',
              symbolSize: 50,
              roam: true,
              label: {
                show: true
              },
              edgeSymbol: ['circle', 'arrow'],
              edgeSymbolSize: [0, 8],
              edgeLabel: {
                fontSize: 20
              },
              data: this.nodesData,
              links: this.linksData,
              lineStyle: {
                opacity: 0.9,
                width: 2,
                curveness: 0
              }
            }
          ]
      };
    },
    updateChartComputed(){
      // 节点图计算属性
      let rawFlowJSON = this.activeTaskRawItem ? JSON.stringify(this.activeTaskRawItem.rawFlows) : '[]';
      this.$echarts && rawFlowJSON != this.historyFlowJSON 
      if(this.$echarts && rawFlowJSON != this.historyFlowJSON){
        this.historyFlowJSON = rawFlowJSON;
        this.$echarts.setOption(this.chartsOption);
      }
    },
  },
  watch: {
    activeTaskRawItem(){
      // 切换任务的时候更新图
      this.$echarts.resize()
    },
    options: {
      immediate: true,
      handler(val){
        this.updateChartForce();
      }
    },
    ['options.height'](){
      this.updateChartForce();
    }
  },
  methods: {
    updateChartForce(){
      this.$nextTick(() => {
        // 等待高度样式渲染结束在进行渲染节点图
        this.$echarts.setOption(this.chartsOption)
        this.$echarts.resize()
      })
    },
    genParallelLink(linksData, nodesData, o, source){
      // 生成并行层连接关系
      // 在并行层中，每一分支的返回都作为下一“节点”的源节点
      let nextSources = [];
      // 并行层中考虑X轴最大的一分支的X作为下一“节点”的起始位置
      let x = source.x;
      let y = source.y;
      let mX = x;
      for(let v of o){
        let src = source.val;
        if(Array.isArray(v)){
          let tmpSource = {
            val: src, 
            x: x, 
            y: y,
            mX: x,
            mY: y
          }
          nextSources.push(...this.genSerialLink(linksData, nodesData, v, tmpSource))
          // 并行层中的子层（串行层）的子层（并行层）等在Y轴的最大位置决定着该层下一分支的Y轴位置
          y = tmpSource.mY;
          // 并行层中需要记录其子层（串行层）中最大的X轴位置，这是父层（串行层）的下一节点的X轴位置。
          mX = Math.max(mX, tmpSource.mX)
        }else{
          // // 缩减节点名称
          // let [a, b, ...c3g] = v.split('-')
          // v = c3g.join('-')

          linksData.push({source: src, target: v})
          nextSources.push(v)

          // 并行层中节点位置和名称
          nodesData.push({
            name: v,
            x: x,
            y: y,
          })
        }
        // 并行层中的每一分支都增长了Y轴方向的位置
        y++;
      }
      // 最后y轴减去1是因为在遍历的最后的一次y++是多余的
      o != [] && y--;
      // 记录当前层及其子层在X轴最大位置和Y轴最大位置。
      source.mX = mX;
      source.mY = y;
      return nextSources;
    },
    genSerialLink(linksData, nodesData, o, source){
      // 生成串行层连接关系
      // 在串行层中，只需要去最后一“节点”作为下一节点的源节点
      let nextSources = null;
      let x = source.x;
      let y = source.y;
      // 串行层中考虑Y轴最大的一流作为下一节点的
      let mY = source.y;
      for(let v of o){
        // 串行层中，节点的起始由上一个节点确定，如果是第一个节点就从起始确定。
        let src = nextSources || source.val;

        if(Array.isArray(v)){
          let tmpSource = {
            val: src, 
            x: x, 
            y: y,
            mX: x,
            mY: y
          };
          // 串行层中在子层（并行层）的下一个“节点”的源节点应为子层（并行层）的最后一个节点集合（列表）。
          nextSources = this.genParallelLink(linksData, nodesData, v, tmpSource)
          // 在串行层中的子层（并行层）的子层（串行层）等在X轴最大的位置决定着下一“节点”的X轴位置
          x = tmpSource.mX;
          // 串行层中需要记录其子层（并行层）中最大的Y轴位置，这是其父层（并行层）的下一个节点Y的位置
          mY = Math.max(tmpSource.mY, mY);
        }else{
          // // 缩减节点名称
          // let [a, b, ...c3g] = v.split('-')
          // v = c3g.join('-')

          // 如果src是一个数组，那么说明了上一“节点”是并行层的结果
          if(Array.isArray(src)){
            for(let i of src){
              linksData.push({source: i, target: v})
            }
          }else{
            linksData.push({source: src, target: v})
          }
          // 串行层中的单个节点，其返回就是单个节点
          // 为了保证返回类型统一，这里统一返回一个数组，即使只有一个元素
          nextSources = [v]
          
          // 串行层中节点位置和名称
          nodesData.push({
            name: v,
            x: x,
            y: y,
          })
        }
        // 串行层中的每一节点都增长了X轴方向的位置
        x+=2;
      }
      // 最后x轴减去1是因为在遍历的最后的一次x++是多余的
      o != [] && (x-=2);
      // 记录当前层及其子层在X轴最大位置和Y轴最大位置。
      source.mY = mY;
      source.mX = x;
      return nextSources;
    },
    genTaskFlowNodeData(rawItem){
      let rawFlows = rawItem.rawFlows;
      let rootNodesData = {};
      for(let index in rawFlows){
        // 初始化根节点数据
        let data = [{
          name: index,
          x: -2,
          y: 0
        }];
        let links = [];
        rootNodesData[index] = {
          data: data,
          links: links,
        }
        let source = {
          val: index,
          x: 0,
          y: parseInt(index),
        }

        this.genParallelLink(links, data, rawFlows[index], source)
      }
      return rootNodesData
    },
    
  },
  mounted(){
    let dom = document.getElementById('task-flow-container');
    let charts = echarts.init(dom);
    this.$echarts = charts;
    window.testUpdate = () => {
      this.$echarts.setOption(this.chartsOption);
      this.$echarts.resize()
    };
  },
}
</script>


<style lang='stylus' scoped>


#task-flow-container
  >>> div:first-child
  >>> div:first-child canvas
    height: 100% !important
    width: 100% !important

</style>