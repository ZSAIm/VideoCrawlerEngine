<template>
  <!-- <v-col class="information-view"> -->
    <!-- <v-row class="information-tree">
      <Tree
      />
    </v-row> -->

    <!-- <v-row id="information-content"> -->
    <div class="information-container">
      <v-row no-gutters
        v-for="(item, index) in items"
        :key="item.name"
      >
        <v-card
          :color="item.color"
          class="app-info"
        >
          <v-row>
            <v-col>

              <v-card-title class="headline">
                {{ capitalize(item.name) }}
              </v-card-title>

              <v-card-subtitle>
                {{ item.gateway }}
              </v-card-subtitle>
              
            </v-col>
            <v-card-actions>
              <v-btn
                outlined
                rounded
                text
                disabled
              >
                Reload
              </v-btn>
            </v-card-actions>
          </v-row>
          <v-col
              :style="{width: mainApp.width}"
          >
            <WorkerInfo
              :options="item"
            />
          </v-col>
        </v-card>

        

      </v-row>
    </div>
</template>

<script>
import { mapActions, mapGetters, mapState } from 'vuex'
import AppInfo from './layout/AppInfo'
import WorkerInfo from './layout/WorkerInfo'
import { capitalize } from '@/helper/utils'

export default {
  name: 'Information',
  components: {
    AppInfo,
    WorkerInfo,
  },
  computed: {
    ...mapState('app', [
      'mainApp'
    ]),
    ...mapState('information', [
      'appStates',
    ]),
    items(){
      return this.appStates.map(v => {
        
        return {
          name: v.name,
          color: v.code == 0 ? "#385F73" : 'red darken-3',
          msg: v.msg,
          items: v.data,
          gateway: v.gateway
        }
      })
    }
  },
  methods: {
    ...mapActions('information', [
      'getAppState'
    ]),
    capitalize,
  },
  mounted(){
  }
}
</script>


<style lang='stylus' scoped>

.information-view
.information-tree
#information-content
  margin: 0
  padding: 0


.information-view
  display: flex
  flex-direction: row


.information-tree
  max-width: 10rem

#information-content
  flex: 1
  height: 100%
  overflow-y: auto


.app-info
  width: 100%
  margin: 0rem 1rem 1rem 1rem


.information-container
  overflow-y: auto
  padding-top: 1rem
  height: 100%
  // width: 100%


.v-card__actions
  margin-right: 1rem;

.v-card
  background-color: #222 !important

  .v-card__title.headline
    font-weight: 800
</style>