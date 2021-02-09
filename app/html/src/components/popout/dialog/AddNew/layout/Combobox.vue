<template>
<div>
  <!-- <v-btn     
    @click="onClickH()"
  ></v-btn> -->
  <v-combobox
    v-model="model"
    :label="options.label"
    multiple
    clearable
    chips
  >
    <template v-slot:selection="{ attrs, index, item, parent, selected }">
        <v-chip
          v-bind="attrs"
          :input-value="selected"
          label
        >
          <!-- <v-chip
            small
            color="red"
          >
            {{ index }}
          </v-chip> -->
          <v-avatar
            class="accent white--text"
            left
            v-text="index"
          ></v-avatar>


          <span>
            {{ items[index].text }}
          </span>
          <v-spacer></v-spacer>
          <v-icon
            small
            @click="parent.selectItem(item)"
          >
            mdi-close-circle
          </v-icon>
        </v-chip>
      </template>
  </v-combobox>
</div>
</template>


<script>
export default {
  name: 'Combobox',
  props: [
    'options'
  ],
  data () {
    return {
      model: [],
      trimItem: true,
      items: [],
    }
  },
  methods: {
    onClickH(){
      console.log(this.model)
      console.log(this.items)
    },
    getPreview(){
      // 预览

    }
  },
  watch: {
    model (val, prev) {
      if (val.length === prev.length) return
      // 取数组的差值
      this.trimItem && (val = val.map(v => v.trim()));
      let valSet = new Set(val);
      // 清除首位空格后，避免重复传值
      if (val.length != valSet.size){
        val = Array.from(valSet.values())
        this.model = val
        return
      }
      let prevSet = new Set(prev);
      let [more, lessSet] = valSet.size > prevSet.size ? [val, prevSet] : [prev, valSet];
      let diffs = more.filter(x => !lessSet.has(x))
      // 处理item对象
      if(val.length > prev.length){
        // 新增元素
        for(let v of diffs){
          this.items.push({
            text: v,
            model: 'B'
          })
        }
      }else{
        // 删除元素
        this.items = this.items.filter(v => diffs.indexOf(v.text) == -1);
      }
    },
  },
  mounted() {
    // 监听组合框input的onpatse事件
    let input = this.$el.getElementsByClassName('v-select__selections')[0].getElementsByTagName('input')[0];
    input.addEventListener('paste', evt => {
      // 截获粘贴内容，避免input text去掉了换行符。以实现多行的输入
      let textLines = evt.clipboardData.getData('text').split('\n');
      // 过滤空行
      this.trimItem && (textLines = textLines.map(x => x.trim()));
      console.log(this.trimItem, textLines)
      textLines = textLines.filter(x => x !== '');
      // 单行的不进行处理
      if(textLines.length <= 1) return;

      // 数据唯一性，不允许数据重复。
      let newItems = textLines.filter(x => this.model.indexOf(x) == -1);
      // 仅在有新数据才更新，避免model更新空数据发生异常
      if(newItems) this.model = this.model.concat(newItems);
      // 数据不需要填入框
      evt.preventDefault();
    })
  },

}
</script>


<style lang="stylus" scoped>

.v-select--chips
  >>> .v-select__selections
    display: block
    max-height: 15rem
    overflow-y: auto

    .v-chip
      display: block
      border-radius: 0 !important
      .v-chip__content
        display: flex

  >>> .v-select__slot
    > div.v-input__append-inner:last-of-type
      display: none
    .v-chip__content span
      text-overflow: ellipsis;
      max-width: 95%;
      white-space: nowrap;
      overflow: hidden;

</style>