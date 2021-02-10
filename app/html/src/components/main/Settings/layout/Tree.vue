<template>
  <!-- <div class="settings-left"> -->
    <v-card
      class="mx-auto"
      width="300"
    >
      <v-list dense outlined>
        <v-list-item-group
          @change="scrollToConfItem"
          :value="activeItem"
          active-class="tree-item-active"
        >
        <v-list-group
          v-for="item in items"
          :key="item.name"
          :group="item.name"
          append-icon=""
          :value="item.opened"
        >
          <template v-slot:activator>
            <v-list-item-title>{{ capitalize(item.title) }}</v-list-item-title>
          </template>

          <v-list-item
            v-for="group in item.groups"
            :key="[item.name, group.name].join('|')"
            :value="[item.name, group.name].join('|')"
            sub-group
          >
            <v-list-item-content
              class="tree-group-item"
            >
                <v-list-item-title>{{ capitalize(group.title) }}</v-list-item-title>
            </v-list-item-content>

          </v-list-item>

        </v-list-group>
        </v-list-item-group>
      </v-list>
    </v-card>


  
</template>

<script>
import { mapGetters, mapActions, mapState } from 'vuex'
import { capitalize } from '@/helper/utils'

export default {
  name: 'Tree',
  props: [
    'items',
    'active'
  ],
  data(){
    return {
    }
  },
  computed: {
    activeItem(){
      return this.active
    },
  },
  methods: {
    ...mapActions('settings', [
      'scrollToConfItem',
    ]),
    capitalize,

  },
}
</script>

<style lang="stylus" scoped>


.v-card
  background-color: #111 !important

.v-treeview
  width: 100%

  >>> .v-treeview-node__level
    width: 1rem
  
  >>> .v-treeview-node__label
    font-weight: normal

  >>> .v-treeview-node--active
    .v-treeview-node__label
      font-weight: bold

.tree-group-item
  padding-left: 1rem !important


.tree-item-active
  .v-list-item__title
    font-weight: bold !important
    color: white !important


.v-list-group
  >>> .v-list-item
    min-height: 20px
    
    .v-list-item__title
      color: #ccc
      font-weight: normal
    
    .tree-group-item
      padding: 0


</style>