<template>
  <!-- <v-card
    class="mx-auto"
  > -->
    <!-- <v-list id="info-list">
      <v-list-item
        v-for="item in items"
        :key="item.name"
      > -->
        <!-- <v-row> -->
          <!-- <v-col cols="12"> -->
            <v-card
              color="#385F73"
              dark
            >
              <v-card-title class="headline">
                Unlimited music now
              </v-card-title>

              <v-card-subtitle>Listen to your favorite artists and albums whenever and wherever, online and offline.</v-card-subtitle>

              <v-card-actions>
                <v-btn text>
                  Listen Now
                </v-btn>
              </v-card-actions>
            </v-card>
          <!-- </v-col> -->
        <!-- </v-row> -->
      <!-- </v-list-item>
    </v-list> -->
  <!-- </v-card> -->
</template>


<script>
import { mapState, mapGetters, mapActions } from 'vuex'


export default {
  name: 'Info',
  props: [
    'items'
  ],
  data(){
    return {
    }
  },
  computed: {
  },
  methods: {

  },
  components: {
  },

}
</script>

<style lang="stylus" scoped>

.v-card
  width: 100%
  background-color: #111

.v-list
  background-color: #111 !important


</style>