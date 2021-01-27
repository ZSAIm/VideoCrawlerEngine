<template>
  <div>
    <v-app-bar
      dense
      dark
    >
      <v-app-bar-nav-icon></v-app-bar-nav-icon>

      <!-- <v-toolbar-title>VCE</v-toolbar-title> -->
      <task-control></task-control>
      <v-spacer></v-spacer>

      <v-btn icon>
        <v-icon>mdi-magnify</v-icon>
      </v-btn>

      <!-- <v-menu
        left
        bottom
      >
        <template v-slot:activator="{ on, attrs }">
          <v-btn
            icon
            v-bind="attrs"
            v-on="on"
          >
            <v-icon>mdi-dots-vertical</v-icon>
          </v-btn>
        </template>

        <v-list>
          <v-list-item
            v-for="n in 5"
            :key="n"
            @click="() => {}"
          >
            <v-list-item-title>Option {{ n }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu> -->
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