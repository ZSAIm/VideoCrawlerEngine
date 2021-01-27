<template>
  <v-tabs 
      vertical 
      dark
    >
      <div class="tab-top">
        <v-tab
          :replace="true"
          to="/"
        >
          <v-icon 
            left 
          >
            mdi-file-tree
          </v-icon>
        </v-tab>
        <v-tab
          :replace="true"
          to="/settings"
        >
          <v-icon 
            left 
          >
            mdi-settings
          </v-icon>
        </v-tab>
      </div>

      <v-spacer></v-spacer>
      
      <div class="tab-bottom">
        <v-progress-circular
          :value="29"
          :size="22"
          color="deep-orange lighten-2"
        ></v-progress-circular>
      </div>
    </v-tabs>
</template>


<script>
export default {
  name: 'MainTab',
  data () {
    return {
    }
  },

}
</script>


<style lang='stylus' scoped>

.v-tabs
  height: 100%
  width: 3.5rem
  .tab-top
    .v-tab
      min-width: 0
      padding: 0

      .v-icon
        margin: 0
          

</style>