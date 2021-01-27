import axios from 'axios';
import Vue from 'vue';

// axios.defaults.baseURL = 'http://localhost:2332/';
// axios.defaults.timeout = 1000;
Vue.prototype.$axios = axios;

export default axios;