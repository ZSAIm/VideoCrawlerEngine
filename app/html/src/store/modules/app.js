import * as types from '../mutation-types';
import Vue from 'vue'


const state = {
    mainApp: {
        height: 0,
        width: 0
    },
    alertOptions: {
        show: false,
        msg: '',
        color: 'red',
        timeout: null,
    }
};

const getters = {


};

const mutations = {
    [types.MAIN_APP_RESIZE](state, height) {
        state.mainApp.height = height;
    },
    [types.SET_ALERT_OPTION](state, option) {
        state.alertOptions = option;
        if (option.timeout) {
            setTimeout(() => {
                Vue.set(state.alertOptions, 'show', false)
            }, option.timeout)
        }
    },
    // [types.UNSHOW_RESPONSE_MESSAGE](state) {
    //     Vue.set(state.alertOptions, 'show', false)
    // }
};

const actions = {
    initAppModule({ commit }) {
        window.addEventListener('resize', windowResizeHandler);
        windowResizeHandler();
    },
    destroyAppModule({ commit }) {
        window.removeEventListener('resize', windowResizeHandler);
    },
    setAlertOption({ commit }, option) {
        commit(types.SET_ALERT_OPTION, option);

    },
};


function windowResizeHandler() {
    let mainDom = document.getElementById('main-container');
    let statusDom = document.getElementById('statusbar-container');
    let siderDom = document.getElementById('siderbar-container')
    if (mainDom && statusDom && siderDom) {
        state.mainApp = {
            height: (
                innerHeight -
                statusDom.offsetHeight -
                mainDom.offsetTop
            ),
            width: innerWidth - siderDom.offsetWidth
        }

    }
}



export default {
    state,
    getters,
    mutations,
    actions
}