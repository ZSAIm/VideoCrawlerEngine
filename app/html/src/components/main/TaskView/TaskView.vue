<template>
  <task-list></task-list>
</template>


<script>
import TaskList from './layout/TaskList'

export default {
  name: 'TaskView',
  props: [
  ],
  data(){
    return {
    }
  },
  components: {
    TaskList,
  }

}
</script>


<style lang="stylus" scoped>


.v-avatar
  margin-right: 1rem


.v-list
  .v-divider
    margin-top: 0.4rem
    margin-bottom: 0.4rem

.v-list-item__content
  margin-right: 1rem


.list-item-title
  display: flex

  .v-list-item__title
    padding-left: 0.3rem
    font-size: 0.95rem
    margin-top: auto
    margin-bottom: auto

  .v-btn
    float: left

.item-subtitle
  display: flex
  .item-speed
    flex: none


.list-item-progress
  margin-top: 0.2rem
  display: flex

  .v-progress-linear
    flex: 1

.item-progress-circular-percent
  color: white
  font-size: 0.1rem

</style>
