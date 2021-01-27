<template>
  <div id="app">
    <v-app>
      <nav-bar/>
      <div class="main-content">
        <sider-bar/>
        <div class="content-right">
          <app-main/>
          <status-bar/>
        </div>
      </div>
    </v-app>
  </div>
</template>

<script>
import NavBar from '@/views/layout/NavBar' 
import SiderBar from '@/views/layout/SiderBar' 
import AppMain from '@/views/layout/AppMain'
import StatusBar from '@/views/layout/StatusBar'


export default {
  name: 'App',
  components: {
    SiderBar,
    NavBar,
    AppMain,
    StatusBar,
  }
}
</script> 


<style lang="stylus">

@import 'css/materialdesignicons.css';
@import 'css/google-material-icons.css';
@import 'css/main.css';
  
html
  overflow-y: hidden

.main-content
  display: flex

  .content-right
    flex: 1
    display: flex
    flex-direction: column
    flex: 1

  border-radius: 0

</style>
