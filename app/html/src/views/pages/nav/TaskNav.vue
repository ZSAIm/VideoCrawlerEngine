<template>
  <div>
    <v-app-bar
      dense
      dark
    >
      <v-app-bar-nav-icon></v-app-bar-nav-icon>
      <TaskControl></TaskControl>
      <v-spacer></v-spacer>

      <v-btn icon>
        <v-icon>mdi-magnify</v-icon>
      </v-btn>
    </v-app-bar>
  </div>
</template>




<script>
import TaskControl from '@/components/nav/TaskControl/TaskControl'

export default {
  name: 'TaskNav',
  components: {
    TaskControl
  }
}
</script>


<style>

</style>>