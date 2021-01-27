// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from '@/plugins/router'
import vuetify from '@/plugins/vuetify'
import axios from '@/plugins/axios'
import store from '@/plugins/store'
import jsonViewer from '@/plugins/jsonViewer'

Vue.config.productionTip = false;

/* eslint-disable no-new */
new Vue({
    el: '#app',
    router,
    store,
    vuetify,
    components: { App },
    template: '<App/>'
})