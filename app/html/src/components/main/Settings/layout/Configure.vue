<template>
  <v-card
    class="mx-auto"
  >
    <v-list id="setting-conf-list">
        <div
          v-for="(conf, i) in bindConf"
          :key="i"
        >
          <FormGroup
            :conf="conf"
          ></FormGroup>
        </div>
    </v-list>
  </v-card>
</template>


<script>
import { mapState, mapGetters, mapActions } from 'vuex'
import FormGroup from './FormGroup'


export default {
  name: 'Configure',
  props: [
    'items'
  ],
  data(){
    return {
    }
  },
  computed: {
    ...mapState('settings', [
      'bindConf',
    ])
  },
  methods: {

  },
  components: {
    FormGroup,
  },

}
</script>

<style lang="stylus" scoped>

.v-card
  width: 100%
  background-color: #111

.v-list
  background-color: #111 !important

#viewRefDiv
  position: fixed
  z-index: 0

</style>