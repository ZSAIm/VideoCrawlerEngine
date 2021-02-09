<template>
  <div>
    <v-app-bar
      dense
      dark
    >
      <v-app-bar-nav-icon></v-app-bar-nav-icon>
      <SettingsControl></SettingsControl>
      <v-spacer></v-spacer>

      <v-btn icon>
        <v-icon>mdi-magnify</v-icon>
      </v-btn>
    </v-app-bar>
  </div>
</template>




<script>
import SettingsControl from '@/components/nav/SettingsControl/SettingsControl'

export default {
  name: 'SettingsNav',
  components: {
    SettingsControl
  }
}
</script>


<style>

</style>