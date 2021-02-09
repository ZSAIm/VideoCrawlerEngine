import * as types from '../mutation-types';
import axios from '@/plugins/axios'
import Vue from 'vue'

const state = {
    taskRawItems: [],
    fetchTimer: null,
    activeTask: {
        key: '',
        node: '',
    },
    selectedTasks: {},

};

const getters = {
    taskRawItems: state => state.taskRawItems,
    activeTaskRawItem(state) {
        let key = state.activeTask.key;
        for (let v of state.taskRawItems) {
            if (v.sign == key) {
                return v;
            }
        }
        return null;
    },
    activeTaskKey: state => state.activeTask.key,
    activeTaskNode: state => state.activeTask.node,
    activeTask(state, getters) {
        return {
            ...state.activeTask,
            rawItem: getters.activeTaskRawItem
        }
    },
    selectedTasks: state => state.selectedTasks,
    isAllSelect(state) {
        return Object.keys(state.selectedTasks).length == state.taskRawItems.length;
    },
    isEmptySelect(state) {
        return Object.keys(state.selectedTasks).length == 0;
    },
};

const mutations = {
    [types.UPDATE_TASK_ITEM_DATA](state, data) {
        state.taskRawItems = data;
    },
    [types.SET_ACTIVE_TASK_KEY](state, taskKey = '') {
        state.activeTask.key = taskKey;
    },
    [types.SELECT_FLOW_NODE](state, node_a5g = '') {
        state.activeTask.node = node_a5g;
    },
    [types.SELECT_TASK](state, key) {
        Vue.set(state.selectedTasks, key, {});
    },
    [types.UNSELECT_TASK](state, key) {
        Vue.delete(state.selectedTasks, key);
    },
    [types.CLEAR_TASK_SELECT](state) {
        state.selectedTasks = {};
    },
    [types.SELECT_ALL_TASK](state) {
        state.selectedTasks = {};
        for (let v of state.taskRawItems) {
            Vue.set(state.selectedTasks, v.sign, {});
        }
    },
    [types.SET_TASK_FETCH_TIMER](state, timer) {
        state.fetchTimer = timer;
    },
    [types.CLEAR_TASK_FETCH_TIMER](state) {
        clearTimeout(state.fetchTimer)
        state.fetchTimer = null;
    }
};


const actions = {
    async getTaskList({ commit, state }) {
        let { data } = await axios.get('/api/task/list', {
            params: {
                // 获取active的任务的详情
                active: state.activeTask.key
            }
        });
        if (data.code != 0) return;
        commit(types.UPDATE_TASK_ITEM_DATA, data.data);
    },
    async postNewTasks({ commit }, items, options = {}) {
        let postData = {
            urls: items.map(v => v.text),
            options: options
        };
        let { data } = await axios.post('/api/task/new', postData)
        if (data.code != 0) return;
        return data;
    },
    async postStopTasks({ commit }, items) {
        let postData = {
            keys: items.map(v => v.key),
        };
        let { data } = await axios.post('/api/task/stop', postData)
        if (data.code != 0) return;
        return data
    },
    selectNodeItem({ commit, state }, node_a5g) {
        // 选择要显示详细信息的任务节点
        commit(types.SELECT_FLOW_NODE, node_a5g)
    },
    startFetchTaskListTimer({ commit, state }) {
        // 开始任务进度获取时钟
        let timerWorker = (() => {
            actions.getTaskList({ commit, state }).finally(() => {
                if (state.fetchTimer == null) {
                    // 定时器被中途暂停
                    return
                }
                clearTimeout(state.fetchTimer);
                commit(
                    types.SET_TASK_FETCH_TIMER,
                    setTimeout(timerWorker, 1000)
                )
            });
        });
        if (state.fetchTimer != null) return;
        commit(
            types.SET_TASK_FETCH_TIMER,
            setTimeout(timerWorker, 1)
        )
    },
    stopFetchTaskListTimer({ commit, state }) {
        commit(types.CLEAR_TASK_FETCH_TIMER)
    },
    setActiveTaskKey({ commit }, taskKey) {
        // 设置激活任务KEY
        commit(types.SET_ACTIVE_TASK_KEY, taskKey);
    },
    async toggleSelectTask({ commit, state }, key) {
        // 切换任务选择
        let isSelected = state.selectedTasks[key] != undefined;
        if (isSelected) {
            commit(types.UNSELECT_TASK, key);
        } else {
            commit(types.SELECT_TASK, key);
        }
        return !isSelected;
    },
    async clearTaskSelect({ commit }) {
        // 清空任务选择
        commit(types.CLEAR_TASK_SELECT);
    },
    async selectAllTask({ commit }) {
        commit(types.SELECT_ALL_TASK)
    },

};

export default {
    state,
    getters,
    mutations,
    actions
}