<template>
  <div 
    :id="'worker-info-container-' + options.name"
    class="worker-info-chart"
    :updateChart="!updateChartComputed"
  >
  </div>
</template>



<script>
import { mapState, mapActions } from 'vuex'
import * as echarts from 'echarts'
import { capitalize } from '@/helper/utils'

export default {
  name: 'WorkerInfo',
  props: [
    'options',
  ],
  data(){
    return {
      $echarts: null,
      historyJSON: '{}',
      xAxisData: [],
    }
  },
  computed: {
    ...mapState('app', [
      'mainApp'
    ]),
    updateChartComputed(){
      let rawJSON = this.options.items ? JSON.stringify(this.options.items) : '{}';
      if(this.$echarts && rawJSON != this.historyJSON){
        this.historyJSON = rawJSON;
        this.$echarts.setOption(this.chartsOption);
      }
    },
    seriesData(){
      let seriesData = [];
      let xAxisData = [];
      let emphasisStyle = {
        itemStyle: {
          shadowBlur: 1,
          shadowColor: 'rgba(0,0,0,0.3)'
        }
      };
      let workers = this.options.items.worker;
      if(this.options.items){
          // 生成X轴数据
          xAxisData = workers.map(v => {
            return v.name
          });
          // 线程上限数据
          let totalVData = [];
          seriesData = workers.map((v, index) => {
            let vData = [];
            vData[index] = v.count;
            totalVData.push(v.maxConcurrent);
            return {
                name: capitalize(v.name),
                type: 'bar',
                smooth: true,
                stack: '1',
                emphasis: emphasisStyle,
                data: vData,
                barGap: '-100%',
                zlevel: 1
            }
          })
          // 线程上限条
          seriesData.push({
              name: 'Max',
              type: 'bar',
              darkMode: true,
              smooth: true,
              stack: '0',
              emphasis: emphasisStyle,
              data: totalVData,
              label: {
                normal: {
                    show: true,
                    position: 'top',
                    textStyle: { color: '#fff' },
                    formatter: function(v) {
                        return v.value
                    },
                }
              },
              itemStyle: {
                color: '#bbbbbb55',
              },
              zlevel: 0,
              barGap: '-100%',
          })

      }
      this.xAxisData = xAxisData;

      return seriesData;
    },
    chartsOption(){ 
      return {
          tooltip: {},
          xAxis: {
            data: this.xAxisData,
            axisLabel: {
              interval: 0,
              rotate: 35,
              color: '#fff'
            },
            name: '',
            axisLine: {
              onZero: true,
              lineStyle: {
                color: '#fff'
              }
            },
            splitLine: {show: false},
            splitArea: {show: false}
          },
          yAxis: {
            axisLabel: {
              interval: 0,
              color: '#fff'
            },
            name: '线程数',
            axisLine: {
              onZero: true,
              lineStyle: {
                color: '#fff'
              }
            },
            splitLine: {show: false},
            splitArea: {show: false},
            minInterval: 1
          },
          series: this.seriesData
      };

    }
  },
  watch: {
    mainApp(){
      this.$echarts && this.$echarts.resize();
    },
  },
  mounted(){
    let dom = document.getElementById('worker-info-container-' + this.options.name);
    let charts = echarts.init(dom);
    this.$echarts = charts;
    charts.clear();
    charts.setOption(this.chartsOption);
  }


}
</script>

<style lang='stylus' scoped>

.worker-info-chart
  width: 100%
  height: 300px

</style>