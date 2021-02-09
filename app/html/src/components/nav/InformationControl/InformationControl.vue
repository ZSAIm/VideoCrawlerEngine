<template>
  <div class="control-box">
    <v-toolbar dense>
      <SettingsTool
        :dialogOptions="dialogOptions"
      ></SettingsTool>

    </v-toolbar>
  </div>
</template>


<script>
import { mapGetters, mapActions } from 'vuex'
// import SettingsTool from './layout/SettingsTool'

export default {
  name: 'InformationControl',
  data() {
    return {
    }
  },
  
  methods:{
  },
  components: {
    // SettingsTool,
  }
}
</script>


<style lang='stylus' scoped>

.control-box
  display: flex
  flex-direction: row
  >>> .v-toolbar__content
    padding: 0



</style>