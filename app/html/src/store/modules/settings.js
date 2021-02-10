import * as types from '../mutation-types';
import axios from '@/plugins/axios'
import Vue from 'vue'
import { deepCopyJsonObject } from '@/helper/utils'

const state = {
    copyConf: [],
    bindConf: [],
    inViewItems: [],
    activeItemId: null,
};

const getters = {
    diffConf(state) {
        // 返回被修改的表单
        let diffItems = [];
        for (let i0 in state.bindConf) {
            let newConf = state.bindConf[i0];
            let originConf = state.copyConf[i0];
            for (let i1 in originConf.groups) {
                let newGroup = newConf.groups[i1];
                let originGroup = originConf.groups[i1];
                for (let i2 in originGroup.items) {
                    let newItem = newGroup.items[i2];
                    let originItem = originGroup.items[i2];
                    // 方便对象数组比较
                    if (JSON.stringify(newItem.value) != JSON.stringify(originItem.value)) {
                        diffItems.push({
                            link: [newConf.name, newGroup.name, newItem.name],
                            newVal: newItem.value,
                            oldVal: originItem.value,
                        });
                        // 更新配置选项修改状态
                        Vue.set(newItem, 'modified', true);
                    } else {
                        Vue.set(newItem, 'modified', false);
                    }
                }

            }
        }
        return diffItems
    }

};

const mutations = {
    [types.FETCH_CONFIGURE](state, rawConf) {
        state.copyConf = rawConf;
        state.bindConf = deepCopyJsonObject(rawConf);
    },
    [types.CONF_ITEM_ENTER_VIEW](state, { itemId, dom }) {
        state.inViewItems[itemId] = dom
    },
    [types.CONF_ITEM_LEAVE_VIEW](state, itemId) {
        if (state.inViewItems[itemId]) {
            delete state.inViewItems[itemId]
        }
    },
    [types.SET_ACTIVE_CONF_ITEM](state, itemId) {
        state.activeItemId = itemId;
    },
    [types.CONF_ROLLBACK](state, groupId) {
        let [app, group] = groupId.split('|');
        for (let i0 in state.bindConf) {
            let v0 = state.bindConf[i0];
            if (v0.name == app) {
                for (let i1 in v0.groups) {
                    let v1 = v0.groups[i1];
                    if (v1.name == group) {
                        v1.items = deepCopyJsonObject(state.copyConf[i0].groups[i1].items);

                        return
                    }
                }
            }
        }
    },
    [types.CLEAR_CONF_DATA](state) {
        state.bindConf = [];
        state.copyConf = [];
    }
};

const actions = {
    async getConf({ commit, state }) {
        let { data } = await axios.get('/api/conf/query');
        if (data.code != 0) return;
        commit(types.FETCH_CONFIGURE, data.data);
        return data;
    },
    async postConfModifies({ commit, state, getters }) {
        let diff = getters.diffConf
        if (diff.length == 0) {
            return
        }
        let postData = {
            items: diff,
        }
        let { data } = await axios.post('/api/conf/modify', postData);
        if (data.code != 0) return;
        return data;
    },
    async enterView({ commit }, itemId) {
        let dom = document.getElementById(itemId);
        commit(types.CONF_ITEM_ENTER_VIEW, { itemId, dom })
    },
    async leaveView({ commit }, itemId) {
        commit(types.CONF_ITEM_LEAVE_VIEW, itemId)
    },
    async setActiveConfItem({ commit, state }, itemId) {
        commit(types.SET_ACTIVE_CONF_ITEM, itemId);
        // 自动折叠展开组
        let [app, group] = itemId.split('|');
        for (let v of state.bindConf) {
            if (v.name == app) {
                Vue.set(v, 'opened', true)
            } else {
                Vue.set(v, 'opened', false)
            }
        }
    },
    async calMainInView({ commit, state }) {
        let min = null;
        let curActiveDom = state.inViewItems[state.activeItemId]
            // 允许当前激活项在缓冲区内不被切换
        if (curActiveDom != undefined) {
            // 激活状态切换缓冲区间，模糊界限
            let rect = curActiveDom.getBoundingClientRect();
            if (rect.y <= 130 && rect.bottom >= 100) {
                actions.setActiveConfItem({ commit, state }, state.activeItemId);
                return
            }
        }

        // 匹配最合适的作为激活块
        for (let k in state.inViewItems) {
            let dom = state.inViewItems[k];

            let rect = dom.getBoundingClientRect();
            if (rect.y >= 80 && rect.y <= 150) {
                actions.setActiveConfItem({ commit, state }, k)
                return
            }
            if (min == null || rect.y < min.y) {
                min = { id: k, y: rect.y }
            }
        }

        if (min != null) {
            actions.setActiveConfItem({ commit, state }, min.id);
        }
    },
    async confRollback({ commit }, groupId) {
        commit(types.CONF_ROLLBACK, groupId)
    },
    async scrollToConfItem({ commit, state }, itemId) {
        if (typeof itemId == 'number') {
            // 如果数字为索引，那么属于父组
            let firstGroup = state.bindConf[itemId].groups[0];
            if (firstGroup != undefined) {
                itemId = [state.bindConf[itemId].name, firstGroup.name].join('|')
            }
        }
        let dom = document.getElementById(itemId);
        dom && dom.scrollIntoView({
            behavior: "smooth",
        });
    },
    async clearConfData({ commit }) {
        // 清空配置信息，避免切换页加载大量的表单出现卡顿
        commit(types.CLEAR_CONF_DATA)
    }
};



export default {
    state,
    getters,
    mutations,
    actions
}