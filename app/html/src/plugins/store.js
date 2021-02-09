import Vuex from 'vuex';
import Vue from 'vue';

import { actions, getters, modules } from '@/store/'
Vue.use(Vuex);
const store = new Vuex.Store({
    actions,
    getters,
    modules: {
        ...modules,
    }
})

export default store