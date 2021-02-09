import * as types from '../mutation-types';
import axios from '@/plugins/axios'
import Vue from 'vue'
import { deepCopyJsonObject } from '@/helper/utils'

const state = {
    appStates: [],
    fetchTimer: null
};

const getters = {


};

const mutations = {
    [types.GET_APP_STATE](state, data) {
        state.appStates = data;
    },

    [types.SET_INFO_FETCH_TIMER](state, timer) {
        state.fetchTimer = timer;
    },
    [types.CLEAR_TASK_FETCH_TIMER](state) {
        clearTimeout(state.fetchTimer)
        state.fetchTimer = null;
    }
};

const actions = {
    async getAppState({ commit }) {
        let { data } = await axios.get('/api/system/state');
        if (data.code != 0) return;
        commit(types.GET_APP_STATE, data.data);
        return data;
    },
    startFetchAppInfoTimer({ commit, state }) {
        let timerWorker = (() => {
            actions.getAppState({ commit, state }).finally(() => {
                if (state.fetchTimer == null) {
                    // 定时器被中途暂停
                    return
                }
                clearTimeout(state.fetchTimer);
                commit(
                    types.SET_INFO_FETCH_TIMER,
                    setTimeout(timerWorker, 1500)
                )
            });
        });
        if (state.fetchTimer != null) return;
        commit(
            types.SET_INFO_FETCH_TIMER,
            setTimeout(timerWorker, 1)
        )
    },
    stopFetchAppInfoTimer({ commit, state }) {
        commit(types.CLEAR_TASK_FETCH_TIMER)
    },
};



export default {
    state,
    getters,
    mutations,
    actions
}