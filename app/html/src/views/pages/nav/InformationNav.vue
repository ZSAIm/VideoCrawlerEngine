<template>
  <div>
    <v-app-bar
      dense
      dark
    >
      <v-app-bar-nav-icon></v-app-bar-nav-icon>
      <InformationControl></InformationControl>
      <v-spacer></v-spacer>

      <v-btn icon>
        <v-icon>mdi-magnify</v-icon>
      </v-btn>
    </v-app-bar>
  </div>
</template>




<script>
import InformationControl from '@/components/nav/InformationControl/InformationControl'

export default {
  name: 'InformationNav',
  components: {
    InformationControl
  }
}
</script>


<style>

</style>