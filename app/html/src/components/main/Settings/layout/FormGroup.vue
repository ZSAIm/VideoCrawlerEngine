

<script>
import Radio from './Radio'
import Selects from './Selects'
import Switches from './Switch'
import Combobox from './Combobox'
import Slider from './Slider'
import Checkbox from './Checkbox'
import Textareas from './Textareas'
import TextField from './TextField'

import { mapGetters, mapActions, mapState } from 'vuex'
import { capitalize } from '@/helper/utils'
import SettingTypes from '@/helper/settingTypes'

export default {
  name: 'FormGroup',
  props: [
    'conf',
  ],
  data(){
    return {
      inViewComp: {},
    }
  },
  components: {
    Radio,
    Selects,
    Switches,
    Combobox,
    Slider,
    Checkbox,
    Textareas,
    TextField,
  },
  computed: {
    ...mapState('settings', [
      'bindConf'
    ]),
    ...mapGetters('settings', [
      'diffConf',
    ])
  },
  methods: {
    ...mapActions('settings', [
      'enterView',
      'leaveView',
      'calMainInView',
      'confRollback'
    ]),
    intersect(entries, observer, isIntersecting){
      for(let v of entries){
        let domId = v.target.id;
        if(isIntersecting){
          // 进入视野内的情况下，添加到待监听队列
          this.enterView(domId);
        }else{
          // 退出视野的不需要再监听视野状态
          this.leaveView(domId);
        }
      }
      // 初始化目录active项
      this.calMainInView();
    },
  },
  watch: {
    // 改参数必须要被监听，该Getter与配置状态条绑定，用于提示配置是否被修改
    diffConf: () => {},
  },

  render(h){
    return (
    <div class="settings-group">
      <v-col>
        {this.conf.groups.map(group => {
          let directives = [{
            name: 'intersect',
            value: this.intersect,
          }];
          return (
          <div class="group-box"
            id={([this.conf.name, group.name]).join('|')}
            {...{directives}}
          >
            <div class="group-title">
              {capitalize(group.title)}
              <v-btn
                class="rollback-btn"
                text icon
                onClick={() => {this.confRollback(([this.conf.name, group.name]).join('|'))}}
              ><v-icon>mdi-refresh</v-icon></v-btn>
            </div>
            
            <div class="group-content">
            {group.items.map(item => {
              let elmAttr = {
                props: {
                  item: item,
                }
              };
              let confForm = h(
                SettingTypes[item.tag.toLowerCase()] || item.tag,
                elmAttr,
              )
              return (
                <v-list-item id={([this.conf.name, group.name, item.name]).join('|')}>
                  <v-row>
                    <div class="setting-item-box">
                      <div class={{"setting-item-status": true, "item-modified": item.modified }}></div>
                      <div class="setting-item-content">
                        <div class='setting-item-title'>{ item.title }</div>
                        <div class='setting-item-desc'>{ item.desc }</div>
                        {confForm}
                      </div>
                    </div>
                  </v-row>
                </v-list-item>
              )
            })}
            </div>
          </div>)
        })}
      </v-col>
    </div>)
  }
}
</script>


<style lang="stylus" scoped>

.group-title
  background-color: black
  line-height: 3rem
  padding-left: 1.5rem
  font-size: 25px
  font-weight: bold

.v-list-item
  padding-top: 0.8rem
  padding-left: 0.8rem

  &:hover
    background-color: #222

.row
  margin: 0

.setting-item-title
  font-weight: bold
  margin-bottom: 0.2rem
  font-size: 1rem;

.setting-item-desc
  font-size: 0.5rem;
  color: #bbb

.setting-item-content
  display: flex
  flex-direction: column
  width: 100%
  flex: 1

.setting-item-status
  width: 0.3rem
  margin-right: 0.8rem
  margin-bottom: 0.8rem


.item-modified
  background-color: #0a5286 !important


.setting-item-box
  display: flex
  width: 100%


.group-title
  .rollback-btn
    opacity: 0
    color: #aaa
  &:hover
    .rollback-btn
      opacity: 1


</style>