<template>
  <v-row justify="center">
    <v-dialog
      v-model="options.show"
      transition="dialog-bottom-transition"
      max-width="700"
    >
      <v-card>
        <v-card-title class="headline">
          新建任务
        </v-card-title>

        <v-divider/>
        <v-tabs
          dark
          v-model="tab"
        >
          <v-tabs-slider color="yellow"></v-tabs-slider>

          <v-tab
            key="uris"
          >
            任务链接
          </v-tab>
          <v-tab
            key="options"
          >
            配置选项
          </v-tab>
        </v-tabs>

        <v-tabs-items v-model="tab">
          <v-tab-item
            key="uris"
          >
            <v-card flat>
              <combobox 
                ref="combobox"
                :options="comboboxOptions"
              ></combobox>
            </v-card>
          </v-tab-item>
          <v-tab-item
            key="options"
          >
            <v-card flat>
              <p>123</p>
            </v-card>
          </v-tab-item>
        </v-tabs-items>
      
        <v-divider/>
        <div class="dialog-bottom">
          <v-switch
            v-model="preload"
            label="预加载"
            disabled
            inset
          ></v-switch>
          <v-spacer></v-spacer>

          <v-btn
            color="green darken-1"
            text
            @click="options.show = false"
          >
            取消
          </v-btn>

          <v-btn
            color="green darken-1"
            @click="submitTasks()"
            width="100"
          >
            开始
          </v-btn>
        </div>
      </v-card>
    </v-dialog>
  </v-row>
</template>



<script>
import { mapGetters, mapActions, mapState } from 'vuex'
import Combobox from './DialogLayout/Combobox'

export default {
  name: 'AddNewDialog',
  props: [
    'options',
  ],
  computed: {

  },
  methods: {
    ...mapActions('task', [
      'postNewTasks',
    ]),
    async submitTasks(){
      // this.$nextTick();
      // 提交任务
      let items = this.$refs['combobox'].items;
      let data = await this.postNewTasks(items);
      // this.postTasks(items).finally(() => {
      //   console.log(arguments)
      // })
      // 关闭对话框
      this.options.show = false
      // 清空组合框
      this.$refs['combobox'].model = [];
    },
  },
  data(){
    return {
      comboboxOptions: {
        label: 'URIs',
      },
      uriText: '',
      tab: null,
      items: [{
          name: '任务链接'
        },{
          name: '配置选项'
        }
      ],
      preload: false,

    }
  },
  components: {
    Combobox,
  }
}
</script>


<style lang="stylus" scoped>

.v-card
  border-radius: 0

.v-divider
  margin-left: 1rem

.v-tabs
  padding-left: 1rem

.v-tabs-items
  padding-left: 1rem
  padding-right: 1rem

.dialog-bottom
  display: flex
  padding: 0.5rem

.v-input--switch
  margin-top: 0
  margin-left: 1rem

</style>
