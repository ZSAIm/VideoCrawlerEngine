import * as types from '../mutation-types';



const state = {
    mainApp: {
        height: 0,
    },
};

const getters = {


};

const mutations = {

};

const actions = {
    initAppModule({ commit }) {
        window.addEventListener('resize', windowResizeHandler);
        windowResizeHandler();
    },
    destroyAppModule({ commit }) {
        window.removeEventListener('resize', windowResizeHandler);
    }
};


function windowResizeHandler() {
    let mainDom = document.getElementById('main-container');
    let statusDom = document.getElementById('status-bar');
    if (mainDom && statusDom) {
        state.mainApp.height = (
            innerHeight -
            statusDom.offsetHeight -
            mainDom.offsetTop
        )
    }
}



export default {
    state,
    getters,
    mutations,
    actions
}